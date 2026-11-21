# Changelog

## Unreleased

- Anchors, step 1: `logbook anchor --to FILE` appends the latest `seq` and
  hash (no event content) to a second place and prints the line.
  `logbook verify --anchor FILE` then reports a truncated or rewritten file
  and exits 1. SPEC §3 "Anchors" has the line format. Verify without
  `--anchor` behaves as before
- The `chain.py` docstring now says what verify detects: an edited line
  fails its own hash; an inserted, deleted or reordered line breaks the link
  after it; deleted last lines need an anchor

## 0.1.3 — 2026-11-16

Two more fixes found by using the logbook for Delfen's own agents. Files
written by 0.1.2 verify the same way; events without the new field are
written exactly as before.

- Per-project log paths: `LOGBOOK_PATH` and `logbook --path` accept
  `{project}` (the project folder's name, found by its `.git`) and `{cwd}`.
  One machine-wide install with `~/logbooks/{project}.jsonl` keeps each
  project in its own file. `logbook://about` shows the resolved path
- Corrections: an optional `corrects` field points to an earlier event that
  a new event corrects. `logbook log --corrects SEQ` and the MCP tool's
  `corrects` argument set it; a value that does not point to an earlier
  event is refused. Events without it are written exactly as before, so
  existing files and readers are unaffected
- SPEC §2 "Corrections" and a README section on correcting an entry

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
