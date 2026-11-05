# Roadmap and decision log

What is planned, what was decided, and what was rejected — in the open.

## Planned

| Item | Why | Status |
| --- | --- | --- |
| **Anchoring** — write the latest `(seq, hash)` to an external place on a schedule (email, ticket, second host, public timestamp) | Closes the truncation gap in `THREAT-MODEL.md` | Next — v0.2 |
| **Gateway mode** — sit between the agent and its tools so logging cannot be skipped | Closes the "agent didn't log" gap | v0.3 |
| **Retention policy** — rotate files by month, keep the chain across files | Needed for real deployments | v0.2 |
| **MCP conformance report** — run the official MCP conformance suite in CI and publish the result | "Agnostic" should be verifiable | When the suite is stable enough to run unattended |
| **Signed container + SBOM** — sign the image, publish a software bill of materials | Reproducibility for auditors | v0.2 |
| **A2A agent card** — describe the logbook as an A2A-discoverable service | Agent-to-agent setups | v0.3 |
| **Dutch README** | Half the first audience reads Dutch first | Soon |

## Decided

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-05 | Format is JSON Lines + SHA-256 hash chain, nothing fancier | Re-implementable in any language in an afternoon; auditors can read it with `cat` |
| 2026-11-05 | The log format is a separate, Apache-licensed spec (`SPEC.md`) | A standard is earned when other people's tools write to it |
| 2026-11-05 | Public from the first commit | Trust claims only mean something when the code is readable |
| 2026-11-05 | Python reference implementation, MCP SDK 2.x | Widest reach among people building agents today |
| 2026-11-05 | Mirror on Codeberg | Do not depend on one platform; practise what we sell |

## Rejected

| Idea | Why not |
| --- | --- |
| Blockchain / distributed ledger | Adds cost and complexity for a problem a hash chain plus anchoring solves |
| Storing the log in a database by default | A plain file is easier to audit, back up and verify independently |
| Sending logs to a Delfen-hosted service by default | The whole point is that the log stays with the owner |
