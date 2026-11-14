"""The `logbook log` command and appends from several processes at once."""

import json
import multiprocessing as mp
import sys

import pytest

from sovereign_agent_logbook import Event, Logbook
from sovereign_agent_logbook.cli import main


def test_cli_log_appends_and_masks(tmp_path, capsys):
    path = tmp_path / "log.jsonl"
    rc = main([
        "--path", str(path), "log",
        "--agent", "cron-job", "--model", "none", "--action", "nightly_backup",
        "--approval", "auto", "--approval-rule", "runbook 4",
        "--outcome", "success", "--arg", "target=db1", "--arg", "api_key=sk-123",
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["seq"] == 1
    raw = path.read_text(encoding="utf-8")
    assert "sk-123" not in raw and "db1" in raw
    assert main(["--path", str(path), "verify"]) == 0


def test_cli_log_rejects_bad_arg(tmp_path):
    with pytest.raises(SystemExit):
        main(["--path", str(tmp_path / "l.jsonl"), "log", "--agent", "a",
              "--model", "m", "--action", "x", "--arg", "novalue"])


def _writer(path: str, n: int, who: str) -> None:
    lb = Logbook(path)
    for i in range(n):
        lb.append(Event(agent_id=who, model="m", action=f"step_{i}"))


@pytest.mark.skipif(sys.platform == "win32", reason="cross-process lock is POSIX only")
def test_parallel_processes_keep_one_chain(tmp_path):
    path = str(tmp_path / "shared.jsonl")
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_writer, args=(path, 25, f"p{k}")) for k in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=60)
        assert p.exitcode == 0
    res = Logbook(path).verify()
    assert res.ok, res.problems
    assert res.events == 100
