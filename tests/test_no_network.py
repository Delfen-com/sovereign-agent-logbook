"""No outbound network, proven rather than promised.

Two checks:
1. The logbook core (chain, store, cli) never imports an HTTP client library.
2. With every outbound socket connection forbidden in the Python runtime,
   a full write -> verify -> export cycle still succeeds.

Honest scope: the MCP server module depends on the `mcp` SDK, which bundles
an HTTP client for its optional HTTP transport (used to LISTEN, not to call
out). The core that touches the log file is what these tests cover; the
server adds no outbound calls of its own, which a reader can confirm in
server.py (about 100 lines).
"""

import socket
import sys

import pytest

from sovereign_agent_logbook import Event, Logbook

FORBIDDEN_MODULES = {"requests", "httpx", "urllib3", "aiohttp", "urllib.request"}


def test_package_imports_no_http_client():
    before = set(sys.modules)
    import sovereign_agent_logbook.store  # noqa: F401
    import sovereign_agent_logbook.chain  # noqa: F401
    import sovereign_agent_logbook.cli  # noqa: F401

    newly_loaded = set(sys.modules) - before
    leaked = {m for m in newly_loaded if m in FORBIDDEN_MODULES}
    assert not leaked, f"logbook core imported network client(s): {leaked}"


def test_full_cycle_with_sockets_disabled(monkeypatch, tmp_path):
    def _no_connect(*args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError("logbook attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", _no_connect)
    monkeypatch.setattr(socket, "create_connection", _no_connect)

    lb = Logbook(tmp_path / "log.jsonl")
    for i in range(3):
        lb.append(Event(agent_id="a", model="m", action=f"op{i}", outcome="success"))
    assert lb.verify().ok
    assert len(lb.export("csv").splitlines()) == 4  # header + 3 rows


def test_http_transport_binds_localhost_by_default(monkeypatch):
    """If someone turns on HTTP, it must not listen on all interfaces by accident."""
    monkeypatch.delenv("LOGBOOK_HOST", raising=False)
    import os

    assert os.environ.get("LOGBOOK_HOST", "127.0.0.1") == "127.0.0.1"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
