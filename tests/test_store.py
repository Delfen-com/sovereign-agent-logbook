"""Secret masking, export formats, and the MCP tool surface."""

import csv
import io
import json

from sovereign_agent_logbook import Event, Logbook
from sovereign_agent_logbook.store import MASK, mask_secrets


def test_secrets_are_masked_before_writing(tmp_path):
    lb = Logbook(tmp_path / "log.jsonl")
    lb.append(
        Event(
            agent_id="a",
            model="m",
            action="call_api",
            arguments={
                "url": "https://example.org",
                "api_key": "sk-live-123",
                "nested": {"Authorization": "Bearer xyz", "fine": 1},
                "list": [{"password": "hunter2"}],
            },
        )
    )
    raw = lb.path.read_text(encoding="utf-8")
    assert "sk-live-123" not in raw
    assert "Bearer xyz" not in raw
    assert "hunter2" not in raw
    assert "https://example.org" in raw
    rec = json.loads(raw.splitlines()[0])
    assert rec["arguments"]["api_key"] == MASK
    assert rec["arguments"]["nested"]["fine"] == 1


def test_mask_is_pure():
    src = {"token": "t", "ok": {"iban": "NL00", "x": 2}}
    out = mask_secrets(src)
    assert out == {"token": MASK, "ok": {"iban": MASK, "x": 2}}
    assert src["token"] == "t"  # input untouched


def test_export_json_and_csv(tmp_path):
    lb = Logbook(tmp_path / "log.jsonl")
    lb.append(Event(agent_id="a", model="m", action="x", tags=["t1", "t2"]))
    lb.append(Event(agent_id="a", model="m", action="y", outcome="success"))
    js = json.loads(lb.export("json"))
    assert len(js) == 2 and js[1]["outcome"] == "success"
    rows = list(csv.DictReader(io.StringIO(lb.export("csv"))))
    assert rows[0]["tags"] == "t1;t2"
    assert rows[1]["action"] == "y"


def test_mcp_tools_are_registered(monkeypatch, tmp_path):
    import asyncio

    monkeypatch.setenv("LOGBOOK_PATH", str(tmp_path / "log.jsonl"))
    import importlib

    from sovereign_agent_logbook import server as srv

    importlib.reload(srv)
    tools = asyncio.run(srv.mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {"log_event", "verify_logbook", "recent_events", "export_logbook"}

    rec = srv.log_event(agent_id="a", model="m", action="write_file", reason="test")
    assert rec["seq"] == 1 and len(rec["hash"]) == 64
    assert srv.verify_logbook()["ok"] is True
    assert srv.recent_events(5)[0]["action"] == "write_file"


def test_unknown_outcome_value_still_verifies(tmp_path):
    """Compatibility: verify does not check the outcome value, so a reader
    that predates `refused` (0.1.3, 0.1.4) still accepts a file that has it."""
    from sovereign_agent_logbook.chain import compute_hash, verify_file

    path = tmp_path / "log.jsonl"
    Logbook(path).append(Event(agent_id="a", model="m", action="x"))
    rec = json.loads(path.read_text().splitlines()[0])
    rec["outcome"] = "some-future-value"
    rec["hash"] = compute_hash(rec)
    path.write_text(json.dumps(rec, ensure_ascii=False) + "\n")
    ok, problems = verify_file(path)
    assert ok, problems


def test_refused_outcome_cli_mcp_verify_and_tamper(tmp_path, capsys, monkeypatch):
    import importlib

    from sovereign_agent_logbook import server as srv
    from sovereign_agent_logbook.cli import main

    path = tmp_path / "log.jsonl"
    rc = main([
        "--path", str(path), "log", "--agent", "a", "--model", "m",
        "--action", "delete_file", "--approval", "human", "--approved-by", "jan",
        "--outcome", "refused", "--summary", "not allowed",
    ])
    assert rc == 0
    capsys.readouterr()
    assert json.loads(path.read_text().splitlines()[0])["outcome"] == "refused"

    monkeypatch.setenv("LOGBOOK_PATH", str(path))
    importlib.reload(srv)
    rec = srv.log_event(
        agent_id="a", model="m", action="send_mail", approval="auto",
        approval_rule="no external mail", outcome="refused",
    )
    assert rec["outcome"] == "refused"
    assert srv.verify_logbook()["ok"] is True

    lines = path.read_text().splitlines()
    first = json.loads(lines[0])
    first["outcome"] = "success"
    lines[0] = json.dumps(first, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n")
    assert srv.verify_logbook()["ok"] is False
