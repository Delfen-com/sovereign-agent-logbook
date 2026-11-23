"""Anchors: a second place that makes truncation and rewrites visible."""

import json

from sovereign_agent_logbook import Event, Logbook
from sovereign_agent_logbook.cli import main


def _fill(path, n):
    lb = Logbook(path)
    for i in range(n):
        lb.append(Event(agent_id="a", model="m", action=f"s{i}", reason="secret-reason"))
    return lb


def test_anchor_line_has_no_content_and_is_printed(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 3)
    anchors = tmp_path / "anchors.jsonl"
    assert main(["--path", str(lb.path), "anchor", "--to", str(anchors)]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed == anchors.read_text(encoding="utf-8").strip()
    a = json.loads(printed)
    assert set(a) == {"anchor", "logbook", "seq", "hash", "ts"}
    assert a["anchor"] == "0.1" and a["logbook"] == "log.jsonl" and a["seq"] == 3
    assert "secret-reason" not in printed


def test_anchor_on_empty_logbook_is_refused(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        main(["--path", str(tmp_path / "log.jsonl"), "anchor", "--to", str(tmp_path / "a")])


def test_matching_anchor_verifies(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 3)
    anchors = tmp_path / "anchors.jsonl"
    main(["--path", str(lb.path), "anchor", "--to", str(anchors)])
    lb.append(Event(agent_id="a", model="m", action="later"))
    assert main(["--path", str(lb.path), "verify", "--anchor", str(anchors)]) == 0


def test_truncation_is_detected(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 4)
    anchors = tmp_path / "anchors.jsonl"
    main(["--path", str(lb.path), "anchor", "--to", str(anchors)])
    lines = lb.path.read_text(encoding="utf-8").splitlines()
    lb.path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    capsys.readouterr()
    assert main(["--path", str(lb.path), "verify"]) == 0  # chain alone cannot see it
    assert main(["--path", str(lb.path), "verify", "--anchor", str(anchors)]) == 1
    assert "truncated: anchor at seq 4, file ends at seq 3" in capsys.readouterr().out


def test_rewrite_with_fresh_valid_chain_is_detected(tmp_path, capsys):
    path = tmp_path / "log.jsonl"
    lb = _fill(path, 3)
    anchors = tmp_path / "anchors.jsonl"
    main(["--path", str(path), "anchor", "--to", str(anchors)])
    path.unlink()
    lb2 = Logbook(path)
    for i in range(3):
        lb2.append(Event(agent_id="a", model="m", action=f"forged{i}"))
    capsys.readouterr()
    assert main(["--path", str(path), "verify"]) == 0
    assert main(["--path", str(path), "verify", "--anchor", str(anchors)]) == 1
    assert "rewritten: event 3 has a different hash than anchored on" in capsys.readouterr().out


def test_anchors_for_other_logbooks_are_not_counted(tmp_path, capsys):
    a = _fill(tmp_path / "one.jsonl", 5)
    b = _fill(tmp_path / "two.jsonl", 2)
    anchors = tmp_path / "anchors.jsonl"
    main(["--path", str(a.path), "anchor", "--to", str(anchors)])
    capsys.readouterr()
    assert main(["--path", str(b.path), "verify", "--anchor", str(anchors)]) == 1
    out = capsys.readouterr().out
    assert f'no anchor for "two.jsonl" in {anchors} (anchors found for: one.jsonl)' in out


def test_renamed_copy_does_not_pass(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 4)
    anchors = tmp_path / "anchors.jsonl"
    main(["--path", str(lb.path), "anchor", "--to", str(anchors)])
    lines = lb.path.read_text(encoding="utf-8").splitlines()
    cut = tmp_path / "cut.jsonl"
    cut.write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
    capsys.readouterr()
    assert main(["--path", str(cut), "verify", "--anchor", str(anchors)]) == 1
    assert 'no anchor for "cut.jsonl"' in capsys.readouterr().out


def test_empty_anchor_file_is_not_a_pass(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 1)
    anchors = tmp_path / "anchors.jsonl"
    anchors.write_text("", encoding="utf-8")
    assert main(["--path", str(lb.path), "verify", "--anchor", str(anchors)]) == 1
    assert "anchors found for: none" in capsys.readouterr().out


def test_ok_message_names_how_many_anchors_were_checked(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 1)
    anchors = tmp_path / "anchors.jsonl"
    for _ in range(3):
        main(["--path", str(lb.path), "anchor", "--to", str(anchors)])
    capsys.readouterr()
    assert main(["--path", str(lb.path), "verify", "--anchor", str(anchors)]) == 0
    assert capsys.readouterr().out.strip() == "OK — 1 events, chain intact, 3 anchors checked"


def test_missing_anchor_file_fails(tmp_path):
    lb = _fill(tmp_path / "log.jsonl", 1)
    assert main(["--path", str(lb.path), "verify", "--anchor", str(tmp_path / "none")]) == 1


def test_verify_without_anchor_unchanged(tmp_path, capsys):
    lb = _fill(tmp_path / "log.jsonl", 2)
    assert main(["--path", str(lb.path), "verify"]) == 0
    assert capsys.readouterr().out.strip() == "OK — 2 events, chain intact"
