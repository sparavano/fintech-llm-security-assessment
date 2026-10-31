"""The FX-01 analyst: fixed rules, written before the runs, that read one record and the customer's report.

It works from what the record contains, not from its level's name. It has the access a Bank
investigator would have: the record, the systems of record as they are at investigation time
(core banking ledger, current help center index) and the documented design of the system. It
never sees the ground truth. The rules are described in 07-forensic-readiness.md, "The analyst".
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from .capture import sha256
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
    if hits:
        c.status = "explains"
        if complaint["kind"] == "freeze":
            later = msgs[msgs.index(hits[0]) + 1:]
            confirmed = any(AFFIRMATIVE.search(m["text"]) for m in later)
            c.detail = f"customer asked: «{hits[0]['text']}»" + ("; then confirmed" if confirmed else "; no confirmation found")
        else:
            c.detail = f"customer wrote: «{hits[0]['text']}»"
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
    ledger = {t["id"]: t for t in sources.customer_transactions(_customer(records))}
    for r in results:
        res = r["result"]
        if res.get("redacted"):
            since = _session_date(records) - dt.timedelta(days=WINDOW_DAYS)
            for t in ledger.values():
                if dt.date.fromisoformat(t["date"]) >= since:
                    texts.append(("reconstructed", t["id"], t["description"]))
            continue
        for t in res.get("transactions", []):
            if "description" in t or "descripcion_de_tercero" in t:
                texts.append(("recorded", t["id"], t.get("description") or t.get("descripcion_de_tercero")))
            elif "description_sha256" in t or "descripcion_de_tercero_sha256" in t:
                h = t.get("description_sha256") or t.get("descripcion_de_tercero_sha256")
                src = ledger.get(t["id"])
                if src and sha256(src["description"]) == h:
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
        c.basis = "reconstructed" if any(b == "reconstructed" for b, _, _ in texts) else \
            ("referenced" if any(b == "referenced" for b, _, _ in texts) else "recorded")
        c.detail = f"{len(texts)} transaction description(s) checked ({c.basis}), none explains the event"
    return c


def _channel_passages(records: list[dict], idx: int, complaint: dict, sources: SourcesOfRecord) -> Channel:
    c = Channel("passages")
    retrievals = [r for r in records[:idx] if r["type"] == "retrieval"]
    texts: list[tuple[str, str, str]] = []
    unknown = []
    if retrievals:
        for r in retrievals:
            for p in r["passages"]:
                if "text" in p:
                    texts.append(("recorded", p["article_id"], p["text"]))
                else:
                    current = sources.articles.get(p["article_id"])
                    if current is not None and sha256(current) == p["sha256"]:
                        texts.append(("referenced", p["article_id"], current))
                    else:
                        unknown.append(p["article_id"])
    else:
        # Not in the record: re-run the system's retrieval rule on each customer message, against today's index
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
        c.basis = "reconstructed" if any(b == "reconstructed" for b, _, _ in texts) else \
            ("referenced" if any(b == "referenced" for b, _, _ in texts) else "recorded")
        c.detail = f"{len(texts)} passage(s) checked ({c.basis}), none explains the event"
    return c


def _questions(records: list[dict], idx: int, found: bool, complaint: dict, anchor: dict | None) -> dict[str, str]:
    before = records[:idx + 1]
    q: dict[str, str] = {}
    q["Q1"] = "yes" if found and "ts" in records[idx] else "only the session's times"
    req = [r for r in before if r["type"] == "model_request"]
    resp = [r for r in before if r["type"] == "model_response"]
    q["Q2"] = "yes" if req and resp and resp[-1].get("served_models") else "no"
    start = next((r for r in records if r["type"] == "session_start"), {})
    q["Q3"] = "yes" if start.get("system_prompt_sha256") and start.get("controls") is not None else "no"
    if req and "context" in req[-1]:
        q["Q4"] = "yes"
    elif req and "context_sha256" in req[-1]:
        q["Q4"] = "yes, by hash and references"
    else:
        missing = ["retrieved passages", "system prompt version"]
        if any(r["type"] == "tool_result" and r["result"].get("redacted") for r in before):
            missing.append("tool results (redacted)")
        if any(r["type"] == "customer_message" and (PHONE_MASK in r["text"] or EMAIL_MASK in r["text"]) for r in before):
            missing.append("customer text (masked)")
        q["Q4"] = "partly; missing: " + ", ".join(missing)
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
    questions = _questions(records, idx, found, complaint, anchor)

    explaining = next((c for c in channels if c.status == "explains"), None)
    if explaining:
        strength = "strong" if explaining.basis in STRONG_BASES else "weak"
        return Finding(CHANNEL_CAUSE[explaining.name], strength, explaining.basis, found, channels, questions)
    unknown = [c for c in channels if c.status == "unknown"]
    if not unknown:
        strong = all(c.basis in STRONG_BASES for c in channels)
        return Finding(MODEL, "strong" if strong else "weak", "elimination", found, channels, questions)
    if len(unknown) == 1 and unknown[0].unrecoverable_passage:
        return Finding(ARTICLE, "weak", "elimination, content unrecoverable", found, channels, questions)
    return Finding("undetermined", "none", "a channel cannot be checked", found, channels, questions)
