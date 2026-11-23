# Sovereign Agent Logbook — Log Format Specification

**Version 0.1 — draft, open for comment.**
Licence: Apache 2.0, same as the code. Anyone may implement this format.

The format is deliberately small enough to re-implement in an afternoon in
any language. The reference implementation in this repository is one
implementation of it, not the definition of it.

## 1. File

A logbook is a UTF-8 text file in [JSON Lines](https://jsonlines.org/)
format: one JSON object per line, lines separated by `\n`. The file is
**append-only**. Implementations MUST NOT modify or delete existing lines.

Recommended filename extension: `.jsonl`.

## 2. Event

Each line is one **event**: a record of one action an agent took or is
about to take. All fields are required unless marked optional.

| Field | Type | Meaning |
| --- | --- | --- |
| `spec` | string | Spec version this event follows. `"0.1"`. |
| `seq` | integer | 1 for the first event, then +1 per event. Never reused. |
| `id` | string | UUID (version 4) unique to this event. |
| `ts` | string | ISO 8601 timestamp in UTC with microseconds, e.g. `2026-11-05T20:41:03.123456+00:00`. |
| `prev_hash` | string | `hash` of the previous event, or 64 `0` characters for the first event. |
| `hash` | string | SHA-256 of this event (see §3), lowercase hex. |
| `agent_id` | string | Stable name of the agent, chosen by its operator. |
| `model` | string | Model name and version as the operator knows it, e.g. `mistral-small-4`, `gpt-nl-1`, `claude-fable-5-1`. |
| `action` | string | The tool, function or operation performed. |
| `arguments` | object | The arguments passed, after secret masking (§4). May be empty. |
| `reason` | string | The agent's stated reason, one sentence. May be empty. |
| `approval` | string | `"human"`, `"auto"` or `"none"`. |
| `approved_by` | string or null | Who approved, when `approval` is `"human"`. |
| `approval_rule` | string or null | Which rule allowed it, when `approval` is `"auto"`. |
| `outcome` | string | `"pending"`, `"success"`, `"error"` or `"escalated"`. |
| `result_summary` | string | One line describing the result. May be empty. |
| `run_id` | string or null | Optional. Groups events of one task or conversation. |
| `tags` | array of strings | Optional labels. May be empty. |
| `corrects` | integer | Optional, and absent unless used. The `seq` of an earlier event in the same file that this event corrects (§2, Corrections). |

Implementations MAY add further fields. Unknown fields MUST be preserved and
MUST be included in the hash.

### Recommended usage pattern

Log twice per action with side effects: once **before** with
`outcome: "pending"`, once **after** with the real outcome and the same
`run_id`. Read-only actions MAY be logged once, after.

### Corrections

An event is never edited or removed once written: that would break the
chain. If an event turns out to be wrong, for example an outcome logged as
`"success"` for an action that did not run, the writer appends a new event
with `corrects` set to the wrong event's `seq` and says what was wrong in
`result_summary`. A reader takes the newest correction of an event as the
current state; the wrong event stays visible.

`corrects` MUST point to an event that already exists in the same file
(1 ≤ `corrects` < own `seq`). A writer MUST refuse other values.

## 3. Hash chain

`hash` = SHA-256 over the **canonical JSON** of the event with the `hash`
field removed.

Canonical JSON means:

1. Object keys sorted by Unicode code point, recursively.
2. No whitespace: separators are `,` and `:` only.
3. Strings encoded as UTF-8 without escaping non-ASCII characters.
4. Numbers as the shortest representation that round-trips (JSON default).

`prev_hash` of event *n* MUST equal `hash` of event *n − 1*. The first
event's `prev_hash` is the **genesis value**: `"0000…0000"` (64 zeros).

A verifier walks the file from the first line, recomputes each hash, and
checks `seq`, `prev_hash` and `hash`. Any mismatch means the file was
altered after writing.

### What the chain proves and does not prove

It proves: no line was changed, inserted, removed or reordered **inside**
the file after it was written.

It does not prove: that the **last** lines were not deleted (truncation),
or that the writer itself was honest. See `THREAT-MODEL.md` for the
mitigations (periodic anchoring of the latest hash to an external place).

### Anchors

An anchor records the latest `seq` and `hash` in a second place, so that
truncation and full rewrites can be seen. One anchor is one JSON line:

```json
{"anchor":"0.1","logbook":"backup.jsonl","seq":41,"hash":"<64 hex>","ts":"2026-11-21T10:00:00Z"}
```

`logbook` is the file name of the logbook, without folders. `ts` is UTC.
An anchor never contains event content. A verifier given an anchor file
checks every line whose `logbook` equals the file name: the event with that
`seq` MUST exist (else the file was truncated) and MUST have that `hash`
(else it was rewritten). Lines for other file names are ignored. If no line
matches the file name, the verifier MUST report a problem: nothing was
checked. A passing result SHOULD say how many anchors were compared.

## 4. Secret masking

Before computing the hash and writing, implementations MUST replace the
value of any key in `arguments` (at any depth) whose name contains, case-
insensitively, one of:

`password`, `passwd`, `secret`, `token`, `api_key`/`api-key`/`apikey`,
`authorization`, `cookie`, `private_key`/`private-key`, `credential`,
`bsn`, `iban`, `ssn`

with the exact string `"***masked***"`. Operators MAY extend this list.
Masking happens **before** hashing, so the hash covers the masked value.

## 5. Transport

How events reach the writer is out of scope. The reference implementation
exposes the writer as an MCP server with four tools (`log_event`,
`verify_logbook`, `recent_events`, `export_logbook`). Other transports
(HTTP, syslog, a library call) are conformant as long as the file obeys
§1–§4.

## 6. Conformance

An implementation conforms if a file it writes verifies under the
reference verifier (`logbook verify`), and if it detects every tampering
case in `tests/test_chain.py`. Those tests are the conformance suite for
this version.

## 7. Change process

Changes to this specification are proposed as pull requests to this file,
discussed in the open, and recorded in `CHANGELOG.md`. Version 0.x may
change in incompatible ways; from 1.0 the format is frozen except for
additive fields.
