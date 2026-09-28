"""Tamper-evident audit log.

A land-record system that cannot prove its own history has not been edited is
not an audit trail, it is a list. This makes the difference concrete: every
entry carries a SHA-256 over its own canonical content *and the hash of the
entry before it*, so the log is a hash chain. Changing any historical field
changes that entry's hash, which breaks every link after it, and
:meth:`AuditLog.verify` reports the exact sequence number where the chain
first fails.

This does not stop a determined attacker with write access to the file -- they
could recompute the whole chain. It makes silent, selective edits impossible,
which is the realistic threat: a record quietly altered after the fact. Pair it
with append-only storage or periodic anchoring for a stronger guarantee.

Two properties are deliberate:

*Canonical serialisation.* The hash is taken over JSON with sorted keys and no
insignificant whitespace, so a re-serialised entry hashes identically and the
chain does not break for cosmetic reasons.

*Before/after values are recorded, not just the action.* "Officer accepted
C0042" is not reviewable. "Officer changed owner from X to Y on parcel P00391,
because the revenue record is authoritative" is.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Iterator

__all__ = ["AuditEntry", "AuditLog", "GENESIS"]

GENESIS = "0" * 64


def _canonical(obj: Any) -> str:
    """Stable JSON: sorted keys, compact separators, no floats surprises."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


@dataclass
class AuditEntry:
    seq: int
    ts: str
    actor: str
    role: str
    action: str
    target: str
    reason: str = ""
    before: Any = None
    after: Any = None
    prev_hash: str = GENESIS
    hash: str = ""

    def payload(self) -> dict:
        """Everything the hash covers. Excludes ``hash`` itself."""
        d = asdict(self)
        d.pop("hash", None)
        return d

    def compute_hash(self) -> str:
        return hashlib.sha256(_canonical(self.payload()).encode("utf-8")).hexdigest()


class AuditLog:
    """Append-only hash-chained log, optionally persisted as JSONL."""

    def __init__(self, path: str | None = None):
        self.path = path
        self.entries: list[AuditEntry] = []
        if path and os.path.exists(path):
            self.load()

    # --- writing ------------------------------------------------------
    def append(self, actor: str, role: str, action: str, target: str,
               reason: str = "", before: Any = None, after: Any = None
               ) -> AuditEntry:
        prev = self.entries[-1].hash if self.entries else GENESIS
        e = AuditEntry(
            seq=len(self.entries) + 1,
            ts=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            actor=actor, role=role, action=action, target=target,
            reason=reason, before=before, after=after, prev_hash=prev,
        )
        e.hash = e.compute_hash()
        self.entries.append(e)
        if self.path:
            self._append_line(e)
        return e

    def _append_line(self, e: AuditEntry) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(_canonical(asdict(e)) + "\n")

    # --- reading ------------------------------------------------------
    def load(self) -> None:
        self.entries = []
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self.entries.append(AuditEntry(**json.loads(line)))

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[AuditEntry]:
        return iter(self.entries)

    # --- integrity ----------------------------------------------------
    def verify(self) -> dict:
        """Walk the chain and report the first break, if any.

        Two failure modes are distinguished, because they mean different
        things: a *content* break means an entry's own fields were altered; a
        *link* break means an entry was inserted, removed or reordered.
        """
        prev = GENESIS
        for e in self.entries:
            if e.prev_hash != prev:
                return {
                    "intact": False, "broken_at": e.seq, "kind": "link",
                    "detail": (f"entry {e.seq} expects previous hash "
                               f"{e.prev_hash[:12]}… but the chain is at "
                               f"{prev[:12]}… — an entry was inserted, removed "
                               f"or reordered"),
                    "verified": e.seq - 1, "total": len(self.entries),
                }
            if e.compute_hash() != e.hash:
                return {
                    "intact": False, "broken_at": e.seq, "kind": "content",
                    "detail": (f"entry {e.seq} hashes to "
                               f"{e.compute_hash()[:12]}… but stores "
                               f"{e.hash[:12]}… — its contents were altered "
                               f"after it was written"),
                    "verified": e.seq - 1, "total": len(self.entries),
                }
            prev = e.hash
        return {
            "intact": True, "broken_at": None, "kind": None,
            "detail": f"all {len(self.entries)} entries verified",
            "verified": len(self.entries), "total": len(self.entries),
            "head": prev,
        }

    def head(self) -> str:
        """Current chain head. Publishing this externally anchors the log."""
        return self.entries[-1].hash if self.entries else GENESIS

    # --- demonstration -------------------------------------------------
    def simulate_tamper(self, seq: int, field_name: str, new_value: Any) -> dict:
        """Alter a historical entry in memory and show the chain break.

        Exists so the guarantee can be *demonstrated* rather than asserted.
        Returns the verification result after tampering; the caller is
        expected to reload from disk afterwards.
        """
        idx = seq - 1
        if not (0 <= idx < len(self.entries)):
            return {"error": f"no entry {seq}"}
        old = getattr(self.entries[idx], field_name, None)
        setattr(self.entries[idx], field_name, new_value)
        result = self.verify()
        result["tampered"] = {"seq": seq, "field": field_name,
                              "from": old, "to": new_value}
        return result

    def to_dicts(self) -> list[dict]:
        return [asdict(e) for e in self.entries]
