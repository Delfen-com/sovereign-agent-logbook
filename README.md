# Sovereign Agent Logbook

**Every AI agent needs a logbook. Yours should stay in Europe.**

An open-source, tamper-evident logbook for AI agents. It records every
action, tool call and human approval — who, what, why, approved by whom,
with what outcome — in an append-only, hash-chained file on **your own
server**. It works with **any model** (Mistral, GPT-NL, Llama, Claude, GPT…)
because it speaks the open [Model Context Protocol](https://modelcontextprotocol.io).

[![CI](https://github.com/Delfen-com/sovereign-agent-logbook/actions/workflows/ci.yml/badge.svg)](https://github.com/Delfen-com/sovereign-agent-logbook/actions/workflows/ci.yml)
![Licence: Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue)
![Status: v0.1 — early, working, tests passing](https://img.shields.io/badge/status-v0.1%20early-orange)

> **v0.1 is a working skeleton, not a finished product.** It logs, chains,
> masks secrets, verifies and exports, and every claim on this page has a
> test behind it. What it does not do yet is listed honestly in
> [ROADMAP.md](ROADMAP.md).

## Why

The EU AI Act requires providers and deployers of high-risk AI systems to
keep logs, keep a human able to intervene, and report serious incidents
(Articles 12, 14, 26(6) and 73). Those duties were due on 2 August 2026; the
Digital Omnibus on AI (Regulation (EU) 2026/1744, in force 27 July 2026)
moved them to 2 December 2027 for most high-risk systems and 2 August 2028
for AI built into regulated products. The clock moved; it did not stop.

Autonomous agents make those duties harder. One task is ten tool calls, and
when something goes wrong nobody can reconstruct which call did what, on
whose approval.

Most tools for this live inside a US cloud platform or are built for one
model vendor. If you run a sovereign setup — an open-weight model on your
own hardware — there is nothing small and neutral to drop in. This is that
thing.

## What you get

- **A tamper-evident log.** Each event carries the hash of the previous one.
  Change, insert, remove or reorder a line and `logbook verify` tells you
  exactly where. ([How, in one file of about 80 lines](src/sovereign_agent_logbook/chain.py))
- **Any model, any host, or no cloud at all.** Four MCP tools:
  `log_event`, `verify_logbook`, `recent_events`, `export_logbook`.
- **Secrets masked before writing.** Keys that look like passwords, tokens,
  API keys, IBANs or BSNs are replaced with `***masked***` before hashing.
- **No outbound network, proven.** A test forbids every outbound socket
  connection in the Python runtime and still completes a full write, verify
  and export cycle; a second test asserts the package imports no HTTP client.
  ([tests/test_no_network.py](tests/test_no_network.py))
- **Audit-ready export.** JSON and CSV your DPO or auditor can read without
  this tool.
- **An open format.** [SPEC.md](SPEC.md) is the log format, separate from
  the code, Apache-licensed, so other tools can write it too.
- **A Skills pack** that teaches any agent when to log, what to write and
  when to stop and ask a human. ([skills/sovereign-agent-logbook/SKILL.md](skills/sovereign-agent-logbook/SKILL.md))

## Five-minute install

```bash
pip install git+https://github.com/Delfen-com/sovereign-agent-logbook
```

Point your MCP-capable agent host at the server over stdio. For Claude
Desktop / Claude Code, Cursor, Continue, or any host with an `mcpServers`
block:

```json
{
  "mcpServers": {
    "logbook": {
      "command": "sovereign-agent-logbook",
      "env": { "LOGBOOK_PATH": "/var/lib/logbook/agent.jsonl" }
    }
  }
}
```

Or run it as a service on your own box with Docker:

```bash
docker build -t sovereign-agent-logbook .
docker run -d --name logbook \
  -p 127.0.0.1:8765:8765 \
  -v logbook-data:/data \
  sovereign-agent-logbook
# MCP endpoint: http://127.0.0.1:8765/mcp   (put TLS in front for anything beyond localhost)
```

Then, at any time, as a human:

```bash
logbook --path /var/lib/logbook/agent.jsonl verify
logbook --path /var/lib/logbook/agent.jsonl export --format csv > audit.csv
logbook --path /var/lib/logbook/agent.jsonl tail --limit 10
```

## What an event looks like

```json
{"spec":"0.1","seq":42,"id":"…","ts":"2026-11-05T20:41:03.123456+00:00",
 "prev_hash":"9f2c…","hash":"3a1b…",
 "agent_id":"invoice-bot","model":"mistral-small-4",
 "action":"pay_invoice","arguments":{"amount":1250,"iban":"***masked***"},
 "reason":"Invoice 2026-118 matches PO 4471 and is under the auto-approval limit",
 "approval":"auto","approved_by":null,"approval_rule":"pay-under-2000-matched-po",
 "outcome":"success","result_summary":"Paid via bank API, ref 88213",
 "run_id":"task-7f3e","tags":["finance"]}
```

Field meanings are normative in [SPEC.md](SPEC.md).

## Trust: no black box

| What we promise | How you can check it yourself |
| --- | --- |
| Tamper-evident | Edit any line of a logbook file, run `logbook verify` |
| No outbound network | `tests/test_no_network.py`; the Dockerfile adds no network tooling |
| Tests are public and run on every change | The CI badge above links to every run |
| We say what it does **not** protect against | [THREAT-MODEL.md](THREAT-MODEL.md) |
| We say which AI Act articles it helps with, and which it does not | [docs/ai-act-mapping.md](docs/ai-act-mapping.md) |
| The format outlives the software | [SPEC.md](SPEC.md), Apache-2.0 |
| Security issues have a process | [SECURITY.md](SECURITY.md) |
| Decisions are recorded | [ROADMAP.md](ROADMAP.md), [CHANGELOG.md](CHANGELOG.md) |

## Not tied to one platform

GitHub is where most developers look, so this is the working repository.
An identical mirror on EU-hosted infrastructure is planned so that the code
never depends on a single platform; the target is being chosen and will be
recorded in [ROADMAP.md](ROADMAP.md). Until then, `git clone` gives you a
complete copy — that is the point of git.

## Hosted version

If you would rather not run a server, a hosted version on EU-only
infrastructure (Hetzner, Germany / Scaleway, France) with retention
policies, daily signed anchoring of the chain and a monthly audit export
is planned. Terms as offered on [delfen.ai/logbook](https://delfen.ai/logbook):
€29 per month excluding VAT, 30-day free trial, cancel any time; if the
hosted version is not live by the end of a trial, the trial is cancelled
rather than charged.

## Licence

Apache License 2.0. Built in the Netherlands by [Delfen](https://delfen.ai).
Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
