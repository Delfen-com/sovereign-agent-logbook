# Roadmap and decision log

What is planned, what was decided, and what was rejected — in the open.

## Planned

| Item | Why | Status |
| --- | --- | --- |
| **Anchoring with pluggable targets** — on a schedule, write the latest `(seq, hash)` (64 characters, no content) to a place the log owner cannot edit alone. One interface, several targets: (1) a plain second place — signed email to the DPO, a ticket, a second host; (2) an eIDAS qualified timestamp, legally recognised across the EU; (3) OpenTimestamps (public, free); (4) EBSI, the EU member-state blockchain, for public-sector buyers. Ships with (1) and (2) first. | Closes the truncation gap in `THREAT-MODEL.md`; gives a verifiable "blockchain" answer without putting the log on a blockchain | Next — v0.2 |
| **Conversation fingerprinting** — optional field holding the hash of a full transcript stored elsewhere, so the logbook proves a conversation was not altered without containing it | Keeps personal data out of the audit log while still covering it | v0.2 |
| **Gateway mode** — sit between the agent and its tools so logging cannot be skipped | Closes the "agent didn't log" gap | v0.3 |
| **Retention policy** — rotate files by month, keep the chain across files | Needed for real deployments | v0.2 |
| **MCP conformance report** — run the official MCP conformance suite in CI and publish the result | "Agnostic" should be verifiable | When the suite is stable enough to run unattended |
| **Signed container + SBOM** — sign the image, publish a software bill of materials | Reproducibility for auditors | v0.2 |
| **A2A agent card** — describe the logbook as an A2A-discoverable service | Agent-to-agent setups | v0.3 |
| **EU-hosted mirror** — candidates: self-hosted Forgejo on a Hetzner box (full control, ~€5/month), CodeFloe (Swiss, young), an EU-hosted GitLab | Platform independence that matches the sovereignty claim | Decide in week 2 |
| **Dutch README** | Half the first audience reads Dutch first | Soon |

## Decided

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-05 | Format is JSON Lines + SHA-256 hash chain, nothing fancier | Re-implementable in any language in an afternoon; auditors can read it with `cat` |
| 2026-11-05 | The log format is a separate, Apache-licensed spec (`SPEC.md`) | A standard is earned when other people's tools write to it |
| 2026-11-05 | Public from the first commit | Trust claims only mean something when the code is readable |
| 2026-11-05 | Python reference implementation, MCP SDK 2.x | Widest reach among people building agents today |
| 2026-11-05 | Keep an EU-hosted mirror; **not** on Codeberg (its terms are written for non-commercial free-software projects, and this project has a company behind it and a paid hosted version planned) | Do not depend on one platform, without building on a host that could reasonably ask us to leave |

## Rejected

| Idea | Why not |
| --- | --- |
| Storing the log **on** a blockchain | Slow, costly, and every entry becomes public and permanent — a privacy problem. Anchoring a fingerprint to one (see Planned) gives the guarantee without the cost |
| Storing the log in a database by default | A plain file is easier to audit, back up and verify independently |
| Sending logs to a Delfen-hosted service by default | The whole point is that the log stays with the owner |
