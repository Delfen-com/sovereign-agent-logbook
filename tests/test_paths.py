"""Per-project log paths: one machine-wide install must keep projects apart."""

import json
from pathlib import Path

from sovereign_agent_logbook.cli import main
from sovereign_agent_logbook.paths import project_name, resolve_path


def test_plain_path_is_unchanged(tmp_path):
    assert resolve_path(str(tmp_path / "a.jsonl"), cwd=tmp_path) == tmp_path / "a.jsonl"


def test_project_is_the_git_root_not_the_subfolder(tmp_path):
    root = tmp_path / "client-portal"
    (root / ".git").mkdir(parents=True)
    sub = root / "src" / "deep"
    sub.mkdir(parents=True)
    assert project_name(sub) == "client-portal"
    assert resolve_path("/logs/{project}.jsonl", cwd=sub) == Path("/logs/client-portal.jsonl")


def test_project_without_git_is_the_working_folder(tmp_path):
    work = tmp_path / "My Project (v2)"
    work.mkdir()
    assert project_name(work) == "My-Project-v2"


def test_cwd_and_home_are_expanded(tmp_path):
    assert resolve_path("{cwd}/log.jsonl", cwd=tmp_path) == tmp_path.resolve() / "log.jsonl"
    assert resolve_path("~/x.jsonl", cwd=tmp_path) == Path.home() / "x.jsonl"


def test_two_projects_one_setting_two_files(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    template = str(logs / "{project}.jsonl")
    for name in ("delfen", "other-client"):
        project = tmp_path / name
        (project / ".git").mkdir(parents=True)
        monkeypatch.chdir(project)
        assert main(["--path", template, "log", "--agent", "a", "--model", "m",
                     "--action", f"work_in_{name}"]) == 0
    assert sorted(p.name for p in logs.glob("*.jsonl")) == ["delfen.jsonl", "other-client.jsonl"]
    for f in logs.glob("*.jsonl"):
        events = [json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines()]
        assert [e["action"] for e in events] == [f"work_in_{f.stem}"]


def test_server_resolves_placeholder_at_first_use(tmp_path, monkeypatch):
    import importlib

    project = tmp_path / "proj"
    (project / ".git").mkdir(parents=True)
    monkeypatch.chdir(project)
    monkeypatch.setenv("LOGBOOK_PATH", str(tmp_path / "logs" / "{project}.jsonl"))
    import sovereign_agent_logbook.server as server
    server = importlib.reload(server)
    server.log_event(agent_id="a", model="m", action="x")
    assert (tmp_path / "logs" / "proj.jsonl").exists()
    assert "proj.jsonl" in server.about()
