"""The four ways of keeping the record, as projections of the raw event stream, and their integrity.

L0  Minimized: K08 as worded. Phone numbers and e-mail addresses masked, tool results reduced to a status.
L1  As designed: C8 in 01-system.md. The conversation as the customer saw it, tool calls and results.
L2  Forensic, full: every raw event, hash-chained.
L3  Forensic, by reference: as L2, with third-party free text replaced by its hash and a reference to
    its system of record (transaction ID, help center article ID), hash-chained.

Each projection only drops or transforms fields of the raw stream.
"""
from __future__ import annotations

import copy
import json
import re

from .capture import canonical, sha256

LEVELS = ["L0", "L1", "L2", "L3"]
LEVEL_NAMES = {"L0": "Minimized", "L1": "As designed", "L2": "Forensic, full", "L3": "Forensic, by reference"}
CHAINED = {"L2", "L3"}
GENESIS = "0" * 64

_PHONE = re.compile(r"(?<![\w-])\+?\d[\d\s-]{6,}\d(?![\w-])")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_MASK = "[TEL REDACTADO]"
EMAIL_MASK = "[EMAIL REDACTADO]"


def mask(text: str | None) -> str | None:
    """K08's 'redact personal data', read as: mask phone numbers and e-mail addresses."""
    if not text:
        return text

    def phone(m: re.Match) -> str:
        s = m.group(0)
        if _DATE.fullmatch(s) or sum(ch.isdigit() for ch in s) < 8:
            return s
        return PHONE_MASK

    return _EMAIL.sub(EMAIL_MASK, _PHONE.sub(phone, text))


def _l1(events: list[dict]) -> list[dict]:
    out = []
    for e in events:
        t, ts = e["type"], e["ts"]
        if t == "session_start":
            out.append({"type": t, "ts": ts, "session_id": e["session_id"], "customer_id": e["customer_id"]})
        elif t == "customer_message":
            out.append({"type": t, "ts": ts, "text": e["text"]})
        elif t == "app_native_confirmation":
            out.append({"type": "app_message", "ts": ts, "text": e["app_message"]})
        elif t == "tool_call":
            out.append({"type": t, "ts": ts, "name": e["name"], "args": e["args"]})
        elif t == "tool_result":
            out.append({"type": t, "ts": ts, "name": e["name"], "result": e["result"]})
        elif t == "reply":
            out.append({"type": t, "ts": ts, "text": e["rendered"]})
    return out


def _status(result: dict) -> dict:
    if "transactions" in result:
        return {"redacted": True, "n_transactions": len(result["transactions"])}
    return {k: result[k] for k in ("ok", "status") if k in result} | {"redacted": True}


def _l0(events: list[dict]) -> list[dict]:
    out = []
    for r in _l1(events):
        r = copy.deepcopy(r)
        if r["type"] in ("customer_message", "app_message", "reply"):
            r["text"] = mask(r["text"])
        elif r["type"] == "tool_result":
            r["result"] = _status(r["result"])
        out.append(r)
    return out


def _l2(events: list[dict]) -> list[dict]:
    return copy.deepcopy(events)


def _ref_transactions(result: dict) -> dict:
    result = copy.deepcopy(result)
    for tx in result.get("transactions", []):
        for field in ("description", "descripcion_de_tercero"):
            if field in tx:
                tx[f"{field}_sha256"] = sha256(tx.pop(field))
    return result


def _l3(events: list[dict]) -> list[dict]:
    out = []
    for e in copy.deepcopy(events):
        if e["type"] == "model_request":
            refs = {"transactions": [], "passages": []}
            for m in e.pop("context"):
                if m["role"] == "tool":
                    try:
                        data = json.loads(m["content"])
                    except ValueError:
                        continue
                    refs["transactions"] += [t["id"] for t in data.get("transactions", [])]
            e["context_refs"] = refs
        elif e["type"] == "tool_result":
            e["result"] = _ref_transactions(e["result"])
        elif e["type"] == "retrieval":
            e["passages"] = [{"article_id": p["article_id"], "sha256": p["sha256"]} for p in e["passages"]]
        out.append(e)
    # passages each model call saw: those retrieved for the customer messages before it
    seen: list[str] = []
    for e in out:
        if e["type"] == "retrieval":
            seen += [f"{p['article_id']}@{p['sha256'][:12]}" for p in e["passages"]]
        elif e["type"] == "model_request":
            e["context_refs"]["passages"] = list(dict.fromkeys(seen))
    return out


PROJECT = {"L0": _l0, "L1": _l1, "L2": _l2, "L3": _l3}


def record_hash(rec: dict) -> str:
    return sha256(canonical({k: v for k, v in rec.items() if k != "hash"}))


def chain(records: list[dict]) -> list[dict]:
    prev = GENESIS
    out = []
    for i, r in enumerate(records, 1):
        r = {"seq": i, **r, "prev_hash": prev}
        r["hash"] = record_hash(r)
        prev = r["hash"]
        out.append(r)
    return out


def build(events: list[dict], level: str) -> list[dict]:
    records = PROJECT[level](events)
    if level in CHAINED:
        return chain(records)
    return [{"seq": i, **r} for i, r in enumerate(records, 1)]


def anchor_for(records: list[dict]) -> dict | None:
    """Head of the chain, written after each session to a separate store (here, a separate file)."""
    if not records or "hash" not in records[-1]:
        return None
    return {"session_id": records[0].get("session_id"), "last_seq": records[-1]["seq"], "head_hash": records[-1]["hash"]}


def verify(records: list[dict], anchor: dict | None = None) -> dict:
    """Check a record's integrity with what it carries: its chain, and the anchor if one is given."""
    if not records or "hash" not in records[0]:
        return {"has_integrity_data": False, "chain_ok": None, "anchor_ok": None, "detected": False,
                "detail": "no hashes: the record carries nothing to check it against"}
    problems = []
    prev = GENESIS
    for i, r in enumerate(records, 1):
        if r.get("seq") != i:
            problems.append(f"sequence: expected {i}, found {r.get('seq')}")
        if r.get("prev_hash") != prev:
            problems.append(f"record {r.get('seq')}: link to the previous record broken")
        if record_hash(r) != r.get("hash"):
            problems.append(f"record {r.get('seq')}: content does not match its hash")
        prev = r.get("hash")
    chain_ok = not problems
    anchor_ok = None
    if anchor is not None:
        anchor_ok = records[-1]["seq"] == anchor["last_seq"] and records[-1]["hash"] == anchor["head_hash"]
        if not anchor_ok:
            problems.append("head of the chain does not match the anchor")
    return {"has_integrity_data": True, "chain_ok": chain_ok, "anchor_ok": anchor_ok,
            "detected": (not chain_ok) or (anchor_ok is False), "detail": "; ".join(problems[:3]) or "intact"}
