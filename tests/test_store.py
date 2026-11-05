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
