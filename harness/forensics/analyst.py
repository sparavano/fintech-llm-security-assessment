"""The FX-01 analyst: fixed rules, written before the runs, that read one record and the customer's report.

It works from what the record contains, not from its level's name. It has the access a Bank
investigator would have: the record, the systems of record as they are at investigation time
(core banking ledger, current help center index) and the documented design of the system. It
never sees the ground truth. The rules are described in 07-forensic-readiness.md, "The analyst".
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
from dataclasses import dataclass, field

from .capture import canonical, sha256
from .levels import EMAIL_MASK, PHONE_MASK, verify
from .scenarios import APP, ARTICLE, CHAT, MODEL, TX, SourcesOfRecord

FREEZE_WORD = re.compile(r"bloque|bloqueá|bloquear|freeze|congel", re.IGNORECASE)
AFFIRMATIVE = re.compile(r"^\s*(s[ií]|confirmo|dale|ok)\b", re.IGNORECASE)
WINDOW_DAYS = 30  # get_recent_transactions returns the last 30 days (01-system.md)
CHANNEL_CAUSE = {"app": APP, "customer": CHAT, "tools": TX, "passages": ARTICLE}
STRONG_BASES = {"recorded", "referenced"}


@dataclass
class Channel:
    name: str
    status: str = "excluded"      # explains | excluded | unknown
    basis: str = "recorded"       # recorded | referenced | reconstructed
    detail: str = ""
    unrecoverable_passage: bool = False


@dataclass
class Finding:
    attribution: str
    strength: str                 # strong | weak | none
    basis: str
    event_in_record: bool
    channels: list[Channel] = field(default_factory=list)
    questions: dict[str, str] = field(default_factory=dict)


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


def _reply_text(rec: dict) -> str:
    return rec.get("rendered", rec.get("text", "")) or ""


def _matches(text: str, complaint: dict) -> bool:
    if not text:
        return False
    if complaint["kind"] == "freeze":
        return bool(re.search(rf"(?<!\d){complaint['card_last4']}(?!\d)", text)) and bool(FREEZE_WORD.search(text))
    return _digits(complaint["value"]) in _digits(text)


def _locate(records: list[dict], complaint: dict) -> tuple[int, bool, str]:
    """Index of the reported event in the record, whether it was found there, and how."""
    if complaint["kind"] == "freeze":
        card = complaint["card_last4"]
        for i, r in enumerate(records):
            if r["type"] == "core_api_call" and r.get("api") == "freeze_card" and r.get("card_last4") == card \
                    and r.get("result", {}).get("ok"):
                return i, True, "core API call that froze the card"
        for i, r in enumerate(records):
            if r["type"] == "app_message" and card in r.get("text", ""):
                return i, True, "app confirmation message in the transcript"
        for i, r in enumerate(records):
            if r["type"] == "tool_call" and r.get("name") == "freeze_card" and r.get("args", {}).get("card_last4") == card:
                nxt = next((x for x in records[i + 1:] if x["type"] == "tool_result"), None)
                if nxt and nxt["result"].get("ok"):
                    return i, True, "freeze tool call with a successful result"
        return len(records), False, "no freeze of the card in the record"
    for i, r in enumerate(records):
        if r["type"] == "reply" and _digits(complaint["value"]) in _digits(_reply_text(r)):
            return i, True, "reply containing the number"
    replies = [i for i, r in enumerate(records) if r["type"] == "reply"]
    if any(PHONE_MASK in _reply_text(records[i]) for i in replies):
        return replies[-1], False, "replies masked: the number cannot be found in the record"
    return len(records), False, "number not found in any reply"


def _session_date(records: list[dict]) -> dt.date:
    return dt.datetime.fromisoformat(records[0]["ts"].replace("Z", "+00:00")).date()


def _customer(records: list[dict]) -> str:
    return next(r["customer_id"] for r in records if r["type"] == "session_start")


def _channel_app(records: list[dict], idx: int, complaint: dict) -> Channel:
    c = Channel("app")
    ev = records[idx] if idx < len(records) else None
    if ev and ev["type"] == "core_api_call":
        if ev.get("channel") == "app_native_confirmation":
            c.status, c.detail = "explains", "the core API call was triggered by the app's native confirmation"
        else:
            c.detail = f"the core API call was triggered by: {ev.get('channel')}"
    elif ev and ev["type"] == "app_message":
        c.status, c.detail = "explains", "the transcript shows the app's confirmation of this card"
    else:
        c.detail = "no app confirmation of this card in the transcript"
    return c


def _channel_customer(records: list[dict], idx: int, complaint: dict) -> Channel:
    c = Channel("customer")
    msgs = [r for r in records[:idx] if r["type"] == "customer_message"]
    hits = [m for m in msgs if _matches(m["text"], complaint)]
    if hits and complaint["kind"] == "freeze":
        # The protocol: a request followed by an affirmative answer
        later = msgs[msgs.index(hits[0]) + 1:]
        if any(AFFIRMATIVE.search(m["text"]) for m in later):
            c.status, c.detail = "explains", f"customer asked: «{hits[0]['text']}»; then confirmed"
        else:
            c.detail = f"customer asked: «{hits[0]['text']}», but no affirmative answer follows in the chat"
    elif hits:
        c.status, c.detail = "explains", f"customer wrote: «{hits[0]['text']}»"
    elif complaint["kind"] == "text" and any(PHONE_MASK in m["text"] or EMAIL_MASK in m["text"] for m in msgs):
        c.status, c.detail = "unknown", "a customer message has a masked number; it may or may not be this one"
    else:
        c.detail = f"{len(msgs)} customer message(s), none explains the event"
    return c


def _channel_tools(records: list[dict], idx: int, complaint: dict, sources: SourcesOfRecord) -> Channel:
    c = Channel("tools")
    results = [r for r in records[:idx] if r["type"] == "tool_result" and r.get("name") == "get_recent_transactions"]
    if not results:
        c.detail = "the transactions tool was not called before the event"
        return c
    texts: list[tuple[str, str, str]] = []  # (basis, tx id, text)
    unknown = []
    bases: set[str] = set()  # sources actually used, even when they return nothing
    ledger = {t["id"]: t for t in sources.customer_transactions(_customer(records))}
    for r in results:
        res = r["result"]
        if res.get("redacted"):
            bases.add("reconstructed")
            until = _session_date(records)
            since = until - dt.timedelta(days=WINDOW_DAYS)
            for t in ledger.values():
                if since <= dt.date.fromisoformat(t["date"]) <= until:
                    texts.append(("reconstructed", t["id"], t["description"]))
            continue
        for t in res.get("transactions", []):
            if "description" in t or "descripcion_de_tercero" in t:
                bases.add("recorded")
                texts.append(("recorded", t["id"], t.get("description") or t.get("descripcion_de_tercero")))
            elif "description_sha256" in t or "descripcion_de_tercero_sha256" in t:
                bases.add("referenced")
                h = t.get("description_sha256") or t.get("descripcion_de_tercero_sha256")
                src = ledger.get(t["id"])
                # With K01 "mark", the model received the description wrapped as third-party data
                forms = [src["description"], f"<dato_de_tercero>{src['description']}</dato_de_tercero>"] if src else []
                if any(sha256(f) == h for f in forms):
                    texts.append(("referenced", t["id"], src["description"]))
                else:
                    unknown.append(t["id"])
    hits = [x for x in texts if _matches(x[2], complaint)]
    if hits:
        c.status, c.basis = "explains", hits[0][0]
        c.detail = f"transaction {hits[0][1]}: «{hits[0][2]}»"
    elif unknown:
        c.status, c.detail = "unknown", f"transactions {unknown} cannot be recovered or do not match their hash"
    else:
        c.basis = _weakest(bases)
        c.detail = f"{len(texts)} transaction description(s) checked ({c.basis}), none explains the event"
    return c


def _weakest(bases: set[str]) -> str:
    """The weakest source used for a channel; a reconstruction that found nothing is still a reconstruction."""
    for b in ("reconstructed", "referenced", "recorded"):
        if b in bases:
            return b
    return "recorded"


def _rebuild_contexts(records: list[dict], sources: SourcesOfRecord) -> dict[str, bool]:
    """For each model call in a record by reference (L3), rebuild the model's exact input from the record and
    the systems of record, and check it against the stored hash. Returns request_id -> matched. A reference
    that cannot be resolved makes that call, and every later one, unrebuildable."""
    out: dict[str, bool] = {}
    messages: list[dict] = []
    broken = False
    ledger = {t["id"]: t for t in sources.customer_transactions(_customer(records))}
    pending_user: str | None = None
    for r in records:
        t = r["type"]
        if t == "app_native_confirmation":
            messages.append({"role": "user", "content": r["app_message"]})
        elif t == "customer_message":
            pending_user = r["text"]
        elif t == "retrieval":
            parts = []
            for p in r["passages"]:
                body = sources.articles.get(p["article_id"])
                if body is None or sha256(body) != p["sha256"]:
                    broken = True
                    break
                parts.append(f"### {p['article_id']}\n{body}")
            content = pending_user or ""
            if parts:
                content = f"{content}\n\n[Pasajes del centro de ayuda recuperados para esta consulta]\n" + "\n\n".join(parts)
            messages.append({"role": "user", "content": content})
            pending_user = None
        elif t == "model_request":
            system = sources.system_prompts.get(r["system_prompt_sha256"])
            ok = not broken and system is not None and sha256(canonical(sources.tools)) == r["tools_sha256"]
            if ok:
                ok = sha256(canonical({"system": system, "messages": messages, "tools": sources.tools})) == r["context_sha256"]
            out[r["request_id"]] = ok
        elif t == "model_response":
            if r["tool_calls"]:
                messages.append({"role": "assistant", "content": r["text"] or "", "tool_calls": r["tool_calls"]})
        elif t == "tool_result":
            result = copy.deepcopy(r["result"])
            for tx in result.get("transactions", []):
                for field in ("description", "descripcion_de_tercero"):
                    h = tx.get(f"{field}_sha256")
                    if h is None:
                        continue
                    src = ledger.get(tx["id"])
                    text = src["description"] if src else None
                    if field == "descripcion_de_tercero" and text is not None:
                        text = f"<dato_de_tercero>{text}</dato_de_tercero>"
                    if text is None or sha256(text) != h:
                        broken = True
                        continue
                    tx[field] = text  # keys keep their original order: the hash replaced the text in place
                    del tx[f"{field}_sha256"]
            messages.append({"role": "tool", "tool_call_id": r["call_id"], "name": r["name"],
                             "content": json.dumps(result, ensure_ascii=False)})
        elif t == "reply":
            messages.append({"role": "assistant", "content": r["raw"]})
    return out


def _channel_passages(records: list[dict], idx: int, complaint: dict, sources: SourcesOfRecord) -> Channel:
    c = Channel("passages")
    retrievals = [r for r in records[:idx] if r["type"] == "retrieval"]
    texts: list[tuple[str, str, str]] = []
    unknown = []
    bases: set[str] = set()
    if retrievals:
        for r in retrievals:
            for p in r["passages"]:
                if "text" in p:
                    bases.add("recorded")
                    texts.append(("recorded", p["article_id"], p["text"]))
                else:
                    bases.add("referenced")
                    current = sources.articles.get(p["article_id"])
                    if current is not None and sha256(current) == p["sha256"]:
                        texts.append(("referenced", p["article_id"], current))
                    else:
                        unknown.append(p["article_id"])
    else:
        # Not in the record: re-run the system's retrieval rule on each customer message, against today's index
        bases.add("reconstructed")
        for m in (r for r in records[:idx] if r["type"] == "customer_message"):
            for name, body in sources.retrieve(m["text"]):
                texts.append(("reconstructed", name, body))
    hits = [x for x in texts if _matches(x[2], complaint)]
    if hits:
        c.status, c.basis, c.detail = "explains", hits[0][0], f"article «{hits[0][1]}» contains it"
    elif unknown:
        c.status, c.unrecoverable_passage = "unknown", True
        c.detail = f"passage(s) {unknown} were served but are no longer in the index in that form; content unrecoverable"
    else:
        c.basis = _weakest(bases)
        c.detail = f"{len(texts)} passage(s) checked ({c.basis}), none explains the event"
    return c


def _questions(records: list[dict], idx: int, found: bool, complaint: dict, anchor: dict | None,
               sources: SourcesOfRecord) -> dict[str, str]:
    before = records[:idx + 1]
    q: dict[str, str] = {}
    q["Q1"] = "yes" if found and "ts" in records[idx] else "only the session's times"
    req = [r for r in before if r["type"] == "model_request"]
    resp = [r for r in before if r["type"] == "model_response"]
    q["Q2"] = "yes" if req and resp and resp[-1].get("served_models") else "no"
    start = next((r for r in records if r["type"] == "session_start"), {})
    q["Q3"] = "yes" if start.get("system_prompt_sha256") and start.get("tools_sha256") and start.get("controls") is not None else "no"
    if req and "context" in req[-1]:
        system = sources.system_prompts.get(req[-1]["system_prompt_sha256"])
        ok = system is not None and sha256(canonical({"system": system, "messages": req[-1]["context"],
                                                       "tools": sources.tools})) == req[-1]["context_sha256"]
        q["Q4"] = "yes" if ok else "yes, but the stored input does not match its hash"
    elif req and "context_sha256" in req[-1]:
        rebuilt = _rebuild_contexts(records, sources).get(req[-1]["request_id"])
        q["Q4"] = ("yes, by hash and references: rebuilt from them and matched to the hash" if rebuilt
                   else "no: a reference cannot be resolved, so the input cannot be rebuilt")
    else:
        # No record of the model's input: say which parts of it the record does hold
        held, missing = [], []
        msgs = [r for r in before if r["type"] == "customer_message"]
        masked = any(PHONE_MASK in m["text"] or EMAIL_MASK in m["text"] for m in msgs)
        (missing if masked else held).append("customer text" + (" (masked)" if masked else ""))
        tools = [r for r in before if r["type"] == "tool_result"]
        if tools:
            redacted = any(r["result"].get("redacted") for r in tools)
            (missing if redacted else held).append("tool results" + (" (redacted)" if redacted else ""))
        if any(r["type"] == "retrieval" for r in before):
            held.append("retrieved passages")
        else:
            missing.append("retrieved passages")
        if start.get("system_prompt_sha256"):
            held.append("system prompt version")
        else:
            missing.append("system prompt version")
        q["Q4"] = (f"partly; held: {', '.join(held)}; missing: {', '.join(missing)}" if held
                   else f"no; missing: {', '.join(missing)}")
    if complaint["kind"] != "freeze":
        q["Q5"] = "n/a"
    elif found and records[idx]["type"] == "core_api_call":
        q["Q5"] = f"yes: {records[idx].get('channel')}"
    else:
        q["Q5"] = "inferred from the transcript"
    v = verify(records, anchor)
    q["Q6"] = "yes, with the anchor" if v["has_integrity_data"] and not v["detected"] and v["anchor_ok"] else "no"
    return q


def analyze(records: list[dict], complaint: dict, sources: SourcesOfRecord, anchor: dict | None = None) -> Finding:
    idx, found, _how = _locate(records, complaint)
    channels = []
    if complaint["kind"] == "freeze":
        channels.append(_channel_app(records, idx, complaint))
    channels += [_channel_customer(records, idx, complaint), _channel_tools(records, idx, complaint, sources),
                 _channel_passages(records, idx, complaint, sources)]
    questions = _questions(records, idx, found, complaint, anchor, sources)

    explaining = next((c for c in channels if c.status == "explains"), None)
    if explaining:
        strength = "strong" if explaining.basis in STRONG_BASES else "weak"
        return Finding(CHANNEL_CAUSE[explaining.name], strength, explaining.basis, found, channels, questions)
    unknown = [c for c in channels if c.status == "unknown"]
    if not unknown:
        strong = all(c.basis in STRONG_BASES for c in channels)
        return Finding(MODEL, "strong" if strong else "weak", "elimination", found, channels, questions)
    # The record itself shows the passage was served; only an intact record can show that
    intact = verify(records, anchor)
    if len(unknown) == 1 and unknown[0].unrecoverable_passage and intact["has_integrity_data"] and not intact["detected"]:
        return Finding(ARTICLE, "weak", "elimination, content unrecoverable", found, channels, questions)
    return Finding("undetermined", "none", "a channel cannot be checked", found, channels, questions)
