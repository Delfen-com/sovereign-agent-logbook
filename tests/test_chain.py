"""The hash chain must detect every kind of tampering we claim it detects."""

import json

from sovereign_agent_logbook import Event, Logbook, GENESIS_HASH, verify_file


def _ev(i: int) -> Event:
    return Event(agent_id="agent-a", model="test-model", action=f"step-{i}", reason="test")


def _write(tmp_path, n=5):
    lb = Logbook(tmp_path / "log.jsonl")
    for i in range(n):
        lb.append(_ev(i))
    return lb


def test_empty_logbook_verifies(tmp_path):
    lb = Logbook(tmp_path / "log.jsonl")
    res = lb.verify()
    assert res.ok and res.events == 0


def test_chain_links_from_genesis(tmp_path):
    lb = _write(tmp_path, 3)
    events = lb.recent(10)
    assert events[0]["prev_hash"] == GENESIS_HASH
    assert events[1]["prev_hash"] == events[0]["hash"]
    assert events[2]["prev_hash"] == events[1]["hash"]
    assert [e["seq"] for e in events] == [1, 2, 3]
    assert lb.verify().ok


def test_altered_line_is_detected(tmp_path):
    lb = _write(tmp_path, 4)
    lines = lb.path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[1])
    rec["reason"] = "I never said that"
    lines[1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    lb.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, problems = verify_file(lb.path)
    assert not ok
    assert any("altered" in p for p in problems)


def test_deleted_line_is_detected(tmp_path):
    lb = _write(tmp_path, 4)
    lines = lb.path.read_text(encoding="utf-8").splitlines()
    del lines[2]
    lb.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, problems = verify_file(lb.path)
    assert not ok
    assert any("inserted, removed or reordered" in p for p in problems)


def test_reordered_lines_are_detected(tmp_path):
    lb = _write(tmp_path, 4)
    lines = lb.path.read_text(encoding="utf-8").splitlines()
    lines[1], lines[2] = lines[2], lines[1]
    lb.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert not verify_file(lb.path)[0]


def test_truncation_at_end_is_still_a_valid_shorter_chain(tmp_path):
    """Honest limit: removing the LAST lines cannot be detected by the chain
    alone. THREAT-MODEL.md explains why and what to do about it (anchoring)."""
    lb = _write(tmp_path, 4)
    lines = lb.path.read_text(encoding="utf-8").splitlines()
    lb.path.write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
    assert verify_file(lb.path)[0]


def test_append_survives_reopen(tmp_path):
    p = tmp_path / "log.jsonl"
    Logbook(p).append(_ev(1))
    Logbook(p).append(_ev(2))
    lb = Logbook(p)
    assert lb.verify().ok and lb.verify().events == 2
