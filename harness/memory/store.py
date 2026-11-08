"""Long-term memory store for TC-12 (08-memory-poisoning.md). Everything here is fictional.

Two modes:
  baseline  notes kept as text with their creation time and loaded into every later session,
            as a simple memory feature would keep them (design decision 8)
  K19       every note also carries its provenance: session, model and, as references and
            SHA-256 hashes, each item of third-party text that was in the model's context when it
            was written. A note written with third-party text in context is quarantined: kept,
            with its provenance, but not loaded into later sessions until the customer approves it
            in the app (the approval flow is out of scope)
"""
from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class MemoryStore:
    k19: bool = False
    notes: list[dict] = field(default_factory=list)

    def save(self, customer_id: str, text: str, session_id: str, model: str,
             third_party: list[dict], now: str | None = None) -> dict:
        """Store one note. `third_party` lists the third-party items that were in the model's
        context, each {"type", "id", "text"}; only references and hashes are kept, never the text."""
        note = {
            "note_id": f"N-{len(self.notes) + 1:03d}",
            "customer_id": customer_id,
            "text": text,
            "created_at": now or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        if self.k19:
            note["status"] = "quarantined" if third_party else "active"
            note["provenance"] = {
                "session_id": session_id,
                "model": model,
                "third_party_in_context": [{"type": t["type"], "id": t["id"], "sha256": sha256(t["text"])}
                                           for t in third_party],
            }
        self.notes.append(note)
        return note

    def loaded_for(self, customer_id: str) -> list[dict]:
        """Notes that go into the system prompt of a new session."""
        return [n for n in self.notes if n["customer_id"] == customer_id and n.get("status", "active") == "active"]

    def to_list(self) -> list[dict]:
        return [dict(n) for n in self.notes]
