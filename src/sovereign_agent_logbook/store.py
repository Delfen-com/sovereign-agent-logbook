"""Append-only logbook store (JSON Lines on local disk).

Design rules, in order of importance:
1. Never modify or delete a line. Only append.
2. Every event links to the previous one by hash (see chain.py).
3. No network. This module imports nothing that can open a socket.
4. Secrets are masked before they are written, never after.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .chain import GENESIS_HASH, canonical_json, compute_hash, iter_events, verify_file

Outcome = Literal["success", "error", "escalated", "pending"]
ApprovalKind = Literal["human", "auto", "none"]

# Keys whose values are masked wherever they appear in `arguments`.
# Matching is case-insensitive and substring-based on the key name.
SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|cookie|"
    r"private[_-]?key|credential|bsn|iban|ssn)",
    re.IGNORECASE,
)
MASK = "***masked***"


def mask_secrets(value: Any) -> Any:
    """Recursively replace values under sensitive-looking keys with a marker."""
    if isinstance(value, dict):
        return {
            k: (MASK if SENSITIVE_KEY_PATTERN.search(str(k)) else mask_secrets(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [mask_secrets(v) for v in value]
    return value


@dataclass
class Event:
    """One logged action. Field meanings are normative in SPEC.md."""

    # Who
    agent_id: str
    model: str
    # What
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    # Why
    reason: str = ""
    # Approval
    approval: ApprovalKind = "none"
    approved_by: str | None = None
    approval_rule: str | None = None
    # Outcome
    outcome: Outcome = "pending"
    result_summary: str = ""
    # Context
    run_id: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        rec = asdict(self)
        rec["arguments"] = mask_secrets(rec["arguments"])
        return rec


@dataclass
class VerificationResult:
    ok: bool
    events: int
    problems: list[str]


class Logbook:
    """A single append-only logbook file."""

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    # ---- writing -------------------------------------------------------

    def _tail(self) -> tuple[int, str]:
        """Return (last_seq, last_hash) by reading the final line only."""
        last_seq, last_hash = 0, GENESIS_HASH
        with self.path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            if size == 0:
                return last_seq, last_hash
            # Walk backwards to the last newline-delimited record.
            chunk = 4096
            data = b""
            pos = size
            while pos > 0:
                step = min(chunk, pos)
                pos -= step
                fh.seek(pos)
                data = fh.read(step) + data
                lines = [ln for ln in data.split(b"\n") if ln.strip()]
                if len(lines) >= 1 and (pos == 0 or b"\n" in data[:-1]):
                    last = json.loads(lines[-1].decode("utf-8"))
                    return int(last["seq"]), str(last["hash"])
        return last_seq, last_hash

    def append(self, event: Event) -> dict[str, Any]:
        """Append one event, link it to the chain, return the stored record."""
        with self._lock:
            last_seq, last_hash = self._tail()
            record: dict[str, Any] = {
                "spec": "0.1",
                "seq": last_seq + 1,
                "id": str(uuid.uuid4()),
                "ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                "prev_hash": last_hash,
                **event.to_record(),
            }
            record["hash"] = compute_hash(record)
            line = canonical_json(record) + b"\n"
            with self.path.open("ab") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
            return record

    # ---- reading -------------------------------------------------------

    def verify(self) -> VerificationResult:
        ok, problems = verify_file(self.path)
        count = sum(1 for _ in iter_events(self.path))
        return VerificationResult(ok=ok, events=count, problems=problems)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        events = [e for _, e in iter_events(self.path)]
        return events[-limit:]

    def export(self, fmt: Literal["json", "csv"] = "json") -> str:
        events = [e for _, e in iter_events(self.path)]
        if fmt == "json":
            return json.dumps(events, ensure_ascii=False, indent=2)
        buf = io.StringIO()
        columns = [
            "seq", "ts", "id", "agent_id", "model", "action", "reason",
            "approval", "approved_by", "approval_rule", "outcome",
            "result_summary", "run_id", "tags", "prev_hash", "hash",
        ]
        writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for e in events:
            row = dict(e)
            row["tags"] = ";".join(row.get("tags", []))
            writer.writerow(row)
        return buf.getvalue()
