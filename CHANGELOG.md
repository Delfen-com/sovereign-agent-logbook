# Changelog

## 0.1.2 — 2026-11-14

Fixes found by using the logbook for Delfen's own agents. No change to the
log format: files written by 0.1.1 verify the same way.

- `logbook log`: write one event from the command line, for scripts, cron
  jobs, CI and agents without MCP. It masks secrets the same way as the MCP
  tool
- Appends take an exclusive file lock (POSIX), so several processes on one
  machine can write to the same file without forking the chain. A new test
  runs four processes in parallel
- README: how to log without MCP, and why writers on different machines
  should each keep their own file
- Skill metadata for ClawHub (`metadata.openclaw`) and
  `glama.json`

## 0.1.1 — 2026-11-08

First release on PyPI and in the official MCP registry. No change to the
logbook's behaviour or format.

- Release workflow: tests, then publish to PyPI with trusted publishing (no
  stored password), then publish `server.json` to the MCP registry with
  GitHub OIDC
- `server.json` describing the server for the MCP registry
- README: registry ownership line; narrower claims on logged actions, the
  no-network test and the AI Act dates (pull request #1)

## 0.1.0 — 2026-11-05

First public release. A working skeleton:

- Append-only JSON Lines logbook with SHA-256 hash chain (`SPEC.md` v0.1)
- Tamper detection for altered, inserted, removed and reordered lines
- Secret masking before hashing
- MCP server with four tools (`log_event`, `verify_logbook`, `recent_events`, `export_logbook`), stdio and HTTP transports
- CLI: `logbook verify | export | tail`
- Skills pack for agents
- Threat model, AI Act mapping, security policy
- Public test suite including a zero-network proof; CI on Python 3.11–3.13 and a container build
