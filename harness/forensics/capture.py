"""Record everything that happens in one session of the replica, as a list of raw events.

The raw stream is the most complete record possible (level L2). The other levels are
projections of it (levels.py), so every level describes the same session.

Recording is done from outside the orchestrator:
  - RecordingProvider wraps the model: the exact input of every call, and its output
  - RecordingBank wraps the mock core API: every call, the customer it ran for, and the
    channel that triggered it (a model's tool call or the app's native confirmation)
  - RecordingHelpCenter wraps retrieval: the passages served for each customer message
  - RecordingOrchestrator records customer messages, tool calls and results, the
    orchestrator's own events as they happen, and each reply before and after rendering

Times come from a simulated clock, so the records are identical on every run.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from orchestrator import TOOLS, HelpCenter, MockBank, Orchestrator

HARNESS = Path(__file__).resolve().parent.parent


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256(text: str | bytes) -> str:
    return hashlib.sha256(text.encode("utf-8") if isinstance(text, str) else text).hexdigest()


class Clock:
    """Simulated clock: one second per recorded event, plus explicit pauses between turns."""

    def __init__(self, start: str):
        self.now = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))

    def tick(self) -> str:
        self.now += dt.timedelta(seconds=1)
        return self.now.isoformat().replace("+00:00", "Z")

    def advance(self, seconds: int) -> None:
        self.now += dt.timedelta(seconds=seconds)


class Recorder:
    def __init__(self, session_id: str, clock: Clock):
        self.session_id = session_id
        self.clock = clock
        self.events: list[dict] = []
        self.call_to_request: dict[str, str] = {}

    def add(self, type_: str, **fields: Any) -> dict:
        event = {"type": type_, "ts": self.clock.tick(), "session_id": self.session_id, **copy.deepcopy(fields)}
        self.events.append(event)
        return event


class RecordingProvider:
    """Wraps a provider. Records the model's exact input (system prompt, messages, tools) and its output."""

    def __init__(self, inner, recorder: Recorder):
        self.inner = inner
        self.rec = recorder
        self.name = inner.name
        self.model = inner.model
        self.served_models = getattr(inner, "served_models", set())
        self._n = 0

    def complete(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        self._n += 1
        request_id = f"{self.rec.session_id}-req-{self._n}"
        self.rec.add(
            "model_request",
            request_id=request_id,
            model_requested=self.inner.model,
            settings={"temperature": 0, "reasoning_effort": getattr(self.inner, "reasoning_effort", None)},
            system_prompt_sha256=sha256(system),
            tools_sha256=sha256(canonical(tools)),
            context=messages,
            context_sha256=sha256(canonical({"system": system, "messages": messages, "tools": tools})),
        )
        out = self.inner.complete(system, messages, tools)
        calls = [{"id": c["id"], "name": c["name"], "args": c["args"]} for c in out["tool_calls"]]
        for c in calls:
            self.rec.call_to_request[c["id"]] = request_id
        self.rec.add("model_response", request_id=request_id, served_models=sorted(self.served_models),
                     text=out["text"], tool_calls=calls)
        return out


class RecordingBank(MockBank):
    """Mock core API that records every call, the customer it ran for, and what triggered it."""

    def __init__(self, recorder: Recorder, extra_transactions: dict[str, list[dict]] | None = None):
        super().__init__(extra_transactions=extra_transactions)
        self.rec = recorder
        self.channel = lambda: "unknown"  # set by the orchestrator

    def get_recent_transactions(self, customer_id: str) -> list[dict]:
        txs = super().get_recent_transactions(customer_id)
        self.rec.add("core_api_call", api="get_recent_transactions", customer_id=customer_id, channel=self.channel(),
                     result={"n": len(txs), "ids": [t["id"] for t in txs]})
        return txs

    def freeze_card(self, customer_id: str, last4: str, caller_customer_id: str, check_ownership: bool) -> dict:
        res = super().freeze_card(customer_id, last4, caller_customer_id, check_ownership)
        self.rec.add("core_api_call", api="freeze_card", customer_id=customer_id, card_last4=last4,
                     channel=self.channel(), result=res)
        return res

    def open_support_ticket(self, customer_id: str, summary: str) -> dict:
        res = super().open_support_ticket(customer_id, summary)
        self.rec.add("core_api_call", api="open_support_ticket", customer_id=customer_id, channel=self.channel(), result=res)
        return res


class RecordingHelpCenter(HelpCenter):
    """Help center whose retrieval records the passages served. The orchestrator calls
    retrieve() once per customer message, before it adds the message to the conversation,
    so this is also where the customer's message is recorded, in its true place in time."""

    def __init__(self, recorder: Recorder, extra_articles: dict[str, str] | None = None):
        super().__init__(extra_articles=extra_articles)
        self.rec = recorder
        self.before_retrieve = lambda query: None

    def retrieve(self, query: str, k: int = 2) -> list[tuple[str, str]]:
        self.before_retrieve(query)
        passages = super().retrieve(query, k)
        self.rec.add("retrieval", query=query, passages=[{"article_id": n, "sha256": sha256(b), "text": b} for n, b in passages])
        return passages


class _RecordingList(list):
    """The orchestrator's event list: every event is recorded the moment it is appended."""

    def __init__(self, recorder: Recorder):
        super().__init__()
        self.rec = recorder

    def append(self, item: dict) -> None:  # type: ignore[override]
        super().append(item)
        self.rec.add("orchestrator_event", event=item)


class RecordingOrchestrator(Orchestrator):
    def __init__(self, provider, customer_id: str, controls, bank: RecordingBank, help_center: RecordingHelpCenter,
                 recorder: Recorder):
        self.rec = recorder
        super().__init__(RecordingProvider(provider, recorder), customer_id, controls, bank, help_center)
        self.transcript.events = _RecordingList(recorder)
        self._channel = "none"
        bank.channel = lambda: self._channel
        help_center.before_retrieve = lambda query: self.rec.add("customer_message", text=query)
        code = (HARNESS / "orchestrator.py").read_bytes()
        recorder.add(
            "session_start",
            customer_id=customer_id,
            model_requested=provider.model,
            controls=self.controls.describe(),
            system_prompt_sha256=sha256(self.system_prompt),
            tools_sha256=sha256(canonical(TOOLS)),
            orchestrator_sha256=sha256(code),
        )

    def turn(self, user_text: str, native_confirmation: str | None = None) -> str:
        if self.controls.k02 and native_confirmation and native_confirmation == self.pending_freeze:
            self.rec.add("app_native_confirmation", card_last4=native_confirmation,
                         app_message=f"[La app confirmó el bloqueo de la tarjeta terminada en {native_confirmation}.]")
            self._channel = "app_native_confirmation"
        try:
            reply = super().turn(user_text, native_confirmation)
        finally:
            self._channel = "none"
        self.rec.add("reply", raw=self.transcript.raw_replies[-1], rendered=reply, k05=self.controls.k05)
        return reply

    def _execute(self, call: dict) -> dict:
        self.rec.add("tool_call", call_id=call["id"], request_id=self.rec.call_to_request.get(call["id"]),
                     name=call["name"], args=call["args"])
        previous, self._channel = self._channel, "tool_call"
        try:
            result = super()._execute(call)
        finally:
            self._channel = previous
        self.rec.add("tool_result", call_id=call["id"], name=call["name"], result=result)
        return result
