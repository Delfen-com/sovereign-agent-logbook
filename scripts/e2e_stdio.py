"""End-to-end check used by CI: a real MCP client talks to the server over
stdio, logs an event with a secret in it, and verifies the chain.
Run:  LOGBOOK_PATH=/tmp/e2e.jsonl python scripts/e2e_stdio.py
"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(command="sovereign-agent-logbook", env={**os.environ})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            assert tools == {"log_event", "verify_logbook", "recent_events", "export_logbook"}, tools

            res = await session.call_tool(
                "log_event",
                {
                    "agent_id": "e2e-agent",
                    "model": "any-model",
                    "action": "pay_invoice",
                    "reason": "end-to-end check",
                    "arguments": {"amount": 1, "iban": "NL00TEST0000000000"},
                    "approval": "human",
                    "approved_by": "ci",
                },
            )
            rec = json.loads(res.content[0].text)
            assert rec["seq"] == 1 and rec["arguments"]["iban"] == "***masked***", rec

            ver = json.loads((await session.call_tool("verify_logbook", {})).content[0].text)
            assert ver["ok"] is True and ver["events"] == 1, ver
            print("e2e OK:", rec["hash"][:12], "…")


if __name__ == "__main__":
    asyncio.run(main())
