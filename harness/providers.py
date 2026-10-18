"""Model providers behind one interface.

provider.complete(system, messages, tools) -> {"text": str | None, "tool_calls": [{"id", "name", "args"}]}

`messages` use an OpenAI-style shape: user / assistant (optionally with tool_calls) / tool.
Configuration comes from environment variables so no key ever lives in the repo:

  PROVIDER        openai | anthropic | mock        (default: openai)
  MODEL           model name, recorded in results   (required for openai/anthropic)
  REASONING_EFFORT  optional, passed as reasoning_effort to OpenAI-compatible endpoints
  OPENAI_API_KEY, OPENAI_BASE_URL   for any OpenAI-compatible endpoint (OpenAI, Groq,
                                    Gemini's compatibility endpoint, a local Ollama server...)
  ANTHROPIC_API_KEY                 for Anthropic
"""
from __future__ import annotations

import json
import os
import re
from typing import Any


def from_env():
    kind = os.environ.get("PROVIDER", "openai").lower()
    model = os.environ.get("MODEL")
    if kind == "mock":
        return MockProvider()
    if not model:
        raise SystemExit("Set MODEL (e.g. MODEL=gpt-4.1-mini).")
    if kind == "openai":
        return OpenAICompatible(model)
    if kind == "anthropic":
        return AnthropicProvider(model)
    raise SystemExit(f"Unknown PROVIDER={kind}")


class OpenAICompatible:
    name = "openai-compatible"

    def __init__(self, model: str):
        from openai import OpenAI  # lazy import so the mock works without the SDK

        self.model = model
        self.reasoning_effort = os.environ.get("REASONING_EFFORT") or None
        self.served_models: set[str] = set()  # model names the API reports back; an alias can resolve elsewhere
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=os.environ.get("OPENAI_BASE_URL") or None,
                             timeout=float(os.environ.get("REQUEST_TIMEOUT", "180")), max_retries=4)

    def complete(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        oai_msgs: list[dict] = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "assistant" and m.get("tool_calls"):
                oai_msgs.append({
                    "role": "assistant",
                    "content": m.get("content") or None,
                    "tool_calls": [
                        {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": json.dumps(c["args"], ensure_ascii=False)},
                         **c.get("extra", {})}  # e.g. Gemini's thought_signature, which must be sent back
                        for c in m["tool_calls"]
                    ],
                })
            elif m["role"] == "tool":
                oai_msgs.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
            else:
                oai_msgs.append({"role": m["role"], "content": m["content"]})
        oai_tools = [{"type": "function", "function": t} for t in tools]
        extra = {"reasoning_effort": self.reasoning_effort} if self.reasoning_effort else {}
        resp = self.client.chat.completions.create(model=self.model, messages=oai_msgs, tools=oai_tools, temperature=0, **extra)
        if getattr(resp, "model", None):
            self.served_models.add(resp.model)
        msg = resp.choices[0].message
        calls = []
        for c in msg.tool_calls or []:
            try:
                args = json.loads(c.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": c.function.arguments}
            call = {"id": c.id, "name": c.function.name, "args": args}
            if getattr(c, "model_extra", None):
                call["extra"] = dict(c.model_extra)
            calls.append(call)
        return {"text": msg.content, "tool_calls": calls}


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str):
        import anthropic

        self.model = model
        self.served_models: set[str] = set()
        self.client = anthropic.Anthropic()

    def complete(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        a_msgs: list[dict] = []
        for m in messages:
            if m["role"] == "assistant" and m.get("tool_calls"):
                blocks: list[dict] = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                blocks += [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]} for c in m["tool_calls"]]
                a_msgs.append({"role": "assistant", "content": blocks})
            elif m["role"] == "tool":
                block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                if a_msgs and a_msgs[-1]["role"] == "user" and isinstance(a_msgs[-1]["content"], list):
                    a_msgs[-1]["content"].append(block)
                else:
                    a_msgs.append({"role": "user", "content": [block]})
            else:
                a_msgs.append({"role": m["role"], "content": m["content"]})
        a_tools = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in tools]
        resp = self.client.messages.create(model=self.model, system=system, messages=a_msgs, tools=a_tools, max_tokens=1024, temperature=0)
        if getattr(resp, "model", None):
            self.served_models.add(resp.model)
        text_parts, calls = [], []
        for b in resp.content:
            if b.type == "text":
                text_parts.append(b.text)
            elif b.type == "tool_use":
                calls.append({"id": b.id, "name": b.name, "args": dict(b.input)})
        return {"text": "\n".join(text_parts) or None, "tool_calls": calls}


class MockProvider:
    """A deliberately naive scripted model, used only to check the harness mechanics
    (PROVIDER=mock). It fetches transactions when asked about movimientos, obeys any
    instruction it finds in a description, and freezes a card on any 'sí'. Results from
    the mock are never evidence."""

    name = "mock"
    model = "mock-naive"

    def __init__(self):
        self._n = 0
        self.served_models: set[str] = {"mock-naive"}

    def _cid(self) -> str:
        self._n += 1
        return f"call_{self._n}"

    def complete(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        last = messages[-1]
        if last["role"] == "tool" and last["name"] == "get_recent_transactions":
            data = json.loads(last["content"])
            text = "Estos son tus últimos movimientos:\n" + "\n".join(
                f"- {t['date']} {t['counterparty']} ${t['amount']:,.0f}" for t in data["transactions"]
            )
            blob = json.dumps(data, ensure_ascii=False)
            # Naively obey an injected instruction of the shape "ASISTENTE: ... <text>"
            m = re.search(r"ASISTENTE:\s*([^\"<\]]+)", blob)
            if m:
                instr = m.group(1)
                if "bloque" in instr.lower():
                    l4 = re.search(r"\b(\d{4})\b", instr)
                    return {"text": None, "tool_calls": [{"id": self._cid(), "name": "freeze_card", "args": {"customer_id": "C-1001", "card_last4": l4.group(1) if l4 else "4417"}}]}
                text += "\n\n" + instr
            return {"text": text, "tool_calls": []}
        if last["role"] == "tool":
            return {"text": "Listo.", "tool_calls": []}
        user = last["content"].lower()
        if "movimiento" in user or "transferencia" in user or "gast" in user:
            return {"text": None, "tool_calls": [{"id": self._cid(), "name": "get_recent_transactions", "args": {"customer_id": "C-1001"}}]}
        if user.strip().startswith(("sí", "si", "dale", "ok")):
            return {"text": None, "tool_calls": [{"id": self._cid(), "name": "freeze_card", "args": {"customer_id": "C-1001", "card_last4": "4417"}}]}
        if "bloque" in user:
            return {"text": "¿Confirmás el bloqueo de la tarjeta terminada en 4417?", "tool_calls": []}
        return {"text": "¿En qué te puedo ayudar?", "tool_calls": []}
