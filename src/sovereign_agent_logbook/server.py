"""MCP server exposing the logbook as four tools.

Any agent host that speaks the Model Context Protocol can use this — the
server does not know or care which model is on the other side.

Run it:
    sovereign-agent-logbook                 # stdio transport (default)
    LOGBOOK_TRANSPORT=http sovereign-agent-logbook   # HTTP on 127.0.0.1:8765

Configuration (environment variables):
    LOGBOOK_PATH        where the JSON Lines file lives (default ./logbook.jsonl)
    LOGBOOK_TRANSPORT   "stdio" (default) or "http"
    LOGBOOK_HOST        bind address for http (default 127.0.0.1 — never 0.0.0.0 by accident)
    LOGBOOK_PORT        port for http (default 8765)
"""

from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from . import __version__
from .store import Event, Logbook

LOGBOOK_PATH = os.environ.get("LOGBOOK_PATH", "./logbook.jsonl")

mcp = MCPServer(
    "sovereign-agent-logbook",
    version=__version__,
    instructions=(
        "Tamper-evident logbook for AI agents. Call log_event BEFORE every "
        "action with side effects (writes, sends, payments, deletions) and "
        "AFTER it completes to record the outcome. Never skip logging because "
        "an action seems minor. Secrets in arguments are masked automatically."
    ),
)

_logbook: Logbook | None = None


def get_logbook() -> Logbook:
    global _logbook
    if _logbook is None:
        _logbook = Logbook(LOGBOOK_PATH)
    return _logbook


@mcp.tool()
def log_event(
    agent_id: str,
    model: str,
    action: str,
    reason: str = "",
    arguments: dict[str, Any] | None = None,
    approval: Literal["human", "auto", "none"] = "none",
    approved_by: str | None = None,
    approval_rule: str | None = None,
    outcome: Literal["success", "error", "escalated", "pending"] = "pending",
    result_summary: str = "",
    run_id: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Record one agent action in the logbook.

    Who: agent_id (your agent's stable name) and model (e.g. "mistral-small-4").
    What: action (the tool or operation) and arguments (secrets are masked).
    Why: reason — one plain sentence.
    Approval: "human" with approved_by, "auto" with approval_rule, or "none".
    Outcome: "pending" when logging before the action; log again with
    "success", "error" or "escalated" after it.
    Returns the stored record including its seq and hash.
    """
    event = Event(
        agent_id=agent_id,
        model=model,
        action=action,
        arguments=arguments or {},
        reason=reason,
        approval=approval,
        approved_by=approved_by,
        approval_rule=approval_rule,
        outcome=outcome,
        result_summary=result_summary,
        run_id=run_id,
        tags=tags or [],
    )
    return get_logbook().append(event)


@mcp.tool()
def verify_logbook() -> dict[str, Any]:
    """Check the whole logbook's hash chain. Returns ok, event count and any problems in plain English."""
    res = get_logbook().verify()
    return {"ok": res.ok, "events": res.events, "problems": res.problems}


@mcp.tool()
def recent_events(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent events (default 20) for a quick look."""
    return get_logbook().recent(limit=max(1, min(limit, 500)))


@mcp.tool()
def export_logbook(format: Literal["json", "csv"] = "json") -> str:
    """Export the full logbook as JSON or CSV text that an auditor can read without this tool."""
    return get_logbook().export(fmt=format)


@mcp.resource("logbook://about")
def about() -> str:
    """Version and configuration of this logbook server."""
    return (
        f"sovereign-agent-logbook {__version__}\n"
        f"path: {os.path.abspath(LOGBOOK_PATH)}\n"
        "network: none (this server never makes outbound connections)\n"
        "spec: see SPEC.md in the repository"
    )


def main() -> None:
    transport = os.environ.get("LOGBOOK_TRANSPORT", "stdio").lower()
    if transport == "http":
        mcp.run(
            transport="streamable-http",
            host=os.environ.get("LOGBOOK_HOST", "127.0.0.1"),
            port=int(os.environ.get("LOGBOOK_PORT", "8765")),
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
