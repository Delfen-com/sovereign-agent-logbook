"""Hash chain primitives.

Every event carries the hash of the previous event. An edited line fails its
own hash check. An inserted, deleted or reordered line breaks the prev_hash
link of the line after it. Deleting lines at the end is not detected unless
an anchor exists (see anchor_line and THREAT-MODEL.md). This is the whole
trick, and it is deliberately simple enough to re-implement in an afternoon
in any language — see SPEC.md.

What this does NOT protect against is written down in THREAT-MODEL.md.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# The "previous hash" of the very first event. 64 hex zeros.
GENESIS_HASH = "0" * 64


def canonical_json(obj: dict[str, Any]) -> bytes:
    """Serialise exactly as the spec requires: sorted keys, no spaces, UTF-8.

    Two implementations that follow this rule produce byte-identical output,
    which is what makes the hash reproducible across languages.
    """
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def compute_hash(event_without_hash: dict[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the event minus its own `hash` field."""
    body = {k: v for k, v in event_without_hash.items() if k != "hash"}
    return hashlib.sha256(canonical_json(body)).hexdigest()


def iter_events(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (line_number, event) for every non-empty line in a logbook file."""
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            yield lineno, json.loads(line)


def verify_file(path: Path) -> tuple[bool, list[str]]:
    """Walk a logbook file and check every link in the chain.

    Returns (ok, problems). `problems` is a list of plain-English sentences,
    one per broken link, so a non-programmer can read the result.
    """
    problems: list[str] = []
    expected_prev = GENESIS_HASH
    expected_seq = 1

    for lineno, event in iter_events(path):
        seq = event.get("seq")
        if seq != expected_seq:
            problems.append(
                f"line {lineno}: expected seq {expected_seq}, found {seq!r} "
                "(an event was inserted, removed or reordered)"
            )
        if event.get("prev_hash") != expected_prev:
            problems.append(
                f"line {lineno}: prev_hash does not match the previous event "
                "(the chain is broken here)"
            )
        recomputed = compute_hash(event)
        if event.get("hash") != recomputed:
            problems.append(
                f"line {lineno}: stored hash does not match the event content "
                "(this event was altered after it was written)"
            )
        expected_prev = event.get("hash", recomputed)
        expected_seq = (seq if isinstance(seq, int) else expected_seq) + 1

    return (len(problems) == 0, problems)


ANCHOR_VERSION = "0.1"


def anchor_line(path: Path) -> dict[str, Any]:
    """Build an anchor for the last event: file name, seq, hash, UTC time.

    No event content goes into an anchor. Raises ValueError for an empty file.
    """
    last = None
    for _, event in iter_events(path):
        last = event
    if last is None:
        raise ValueError("the logbook has no events yet, nothing to anchor")
    return {
        "anchor": ANCHOR_VERSION,
        "logbook": path.name,
        "seq": last["seq"],
        "hash": last["hash"],
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def check_anchors(path: Path, anchor_path: Path) -> list[str]:
    """Compare a logbook with an anchor file. Returns plain-English problems.

    Only anchor lines whose "logbook" equals the logbook's file name count.
    """
    if not anchor_path.exists():
        return [f"anchor file not found: {anchor_path}"]
    hashes: dict[Any, str] = {}
    last_seq: Any = 0
    for _, event in iter_events(path):
        hashes[event.get("seq")] = event.get("hash")
        last_seq = event.get("seq")
    problems: list[str] = []
    with anchor_path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                a = json.loads(raw)
            except json.JSONDecodeError:
                problems.append(f"anchor file line {lineno}: not valid JSON")
                continue
            if not isinstance(a, dict) or a.get("logbook") != path.name:
                continue
            seq, ts = a.get("seq"), a.get("ts")
            if seq not in hashes:
                problems.append(
                    f"truncated: anchor at seq {seq}, file ends at seq {last_seq}"
                )
            elif hashes[seq] != a.get("hash"):
                problems.append(
                    f"rewritten: event {seq} has a different hash than anchored on {ts}"
                )
    return problems
