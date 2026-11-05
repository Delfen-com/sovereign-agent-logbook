# Threat model

Written in plain language so a compliance lead can read it, with enough
precision that a security engineer can disagree with it.

## What we are protecting

The **integrity** of the logbook: once an agent's action is written, nobody
can quietly change, remove, reorder or insert lines without it being
detectable.

We are **not** protecting the confidentiality of the logbook (that is the
operator's file permissions and disk encryption), and we are **not**
guaranteeing that every action was logged (that depends on the agent being
configured to log — see the Skills pack).

## Who the attacker is

| Attacker | Can they cheat? | How we handle it |
| --- | --- | --- |
| Someone who gets a copy of the file later (auditor's "was this edited?" question) | No. Any edit to the content breaks the chain. | Hash chain, `logbook verify`. |
| An agent that wants to hide an action by not logging it | Yes, if the agent host does not force logging. | The Skills pack instructs the agent to log every side-effecting action; the real fix is to put the logbook between the agent and its tools (a gateway), which is on the roadmap. |
| An operator with write access who deletes the **last** lines | Yes. A shorter chain is still a valid chain. | **Anchoring**: periodically record the latest `seq` and `hash` somewhere the operator cannot edit alone — a signed email to the DPO, a line in a ticket system, a second machine, or a public timestamping service. The hosted version does this daily. A verifier that knows the anchored hash can then prove truncation. Not implemented in v0.1; tracked in `ROADMAP.md`. |
| An operator with write access who rewrites the **entire** file from scratch | Yes, if there is no anchor. | Same as above. Anchoring is the answer to every "the owner of the machine is the attacker" case. |
| Someone who tampers with the running server process | Yes. Root on the box wins. | Out of scope for software alone. Run the server under its own user, make the file append-only at the OS level (`chattr +a` on Linux), ship the file to a second host. |
| A secret that slips through masking because its key name is unusual | Partially. | The masking list is a baseline and is documented; operators should extend it. Secrets never belong in `reason` or `result_summary` — the Skills pack says so. |

## What the hash chain proves, exactly

Given a file that verifies, and an anchored `(seq, hash)` pair from time T:
every event with `seq` ≤ anchored `seq` is byte-for-byte what it was at
time T. Nothing more.

## Assumptions

- SHA-256 is collision-resistant for the lifetime of the log.
- The system clock is roughly right (timestamps are informative, not part
  of the integrity guarantee).
- Python's `json.dumps` with sorted keys and compact separators is a
  faithful canonical encoder for the field types we use (strings, numbers,
  booleans, null, arrays, objects).

## Reporting a weakness

See `SECURITY.md`.
