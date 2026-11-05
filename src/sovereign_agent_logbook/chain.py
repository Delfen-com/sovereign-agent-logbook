"""Hash chain primitives.

Every event carries the hash of the previous event. Change, insert or delete
one line and every hash after it stops matching. This is the whole trick, and
it is deliberately simple enough to re-implement in an afternoon in any
language — see SPEC.md.

What this does NOT protect against is written down in THREAT-MODEL.md.
"""

from __future__ import annotations

import hashlib
import json
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
