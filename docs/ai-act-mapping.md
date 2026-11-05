# EU AI Act — what this tool helps with, and what it does not

**This is not legal advice.** It is a plain-language map from features in
this repository to the obligations people ask about. Your own classification
of your AI system (minimal / limited / high-risk) is yours to make, and an
obligation is met by your organisation's process, not by installing a tool.
Please copy this table into your own evidence file and strike out what does
not apply.

Regulation (EU) 2024/1689. Article numbers follow the final text. Dates
reflect the general application date of 2 August 2026; the Digital Omnibus
may shift some high-risk deadlines — check the current state before relying
on a date.

| Obligation (plain words) | Article | What the logbook contributes | What it does NOT do |
| --- | --- | --- | --- |
| Keep records of what a high-risk system did, so events can be traced afterwards | Art. 12 (record-keeping, providers) and Art. 26(6) (deployers keep the logs the system generates) | Every agent action is written with who / what / why / approval / outcome, append-only, tamper-evident, exportable | It does not decide retention periods or store the logs for you (the hosted version does) |
| Humans must be able to oversee the system and intervene | Art. 14 (human oversight) and Art. 26(2) | Records which human approved which action, or which rule allowed it automatically; `escalated` outcome marks hand-offs to a person | It does not implement the approval step itself; it records it |
| Report serious incidents | Art. 73 | A verified, exportable timeline of events around the incident | It does not detect incidents or file reports |
| Give deployers the documentation they need | Art. 13, Art. 25 | `SPEC.md`, `THREAT-MODEL.md` and this file are documents you can hand over | It does not describe *your* system |
| Transparency to people interacting with AI | Art. 50 | Nothing directly | — |
| AI literacy of staff | Art. 4 | Nothing directly; `THREAT-MODEL.md` is written to be readable by non-engineers | — |

## Honest summary

The logbook is **evidence infrastructure**. It makes "show me what the
agent did and who approved it" a one-command answer (`logbook export`).
It does not make a system compliant, and a vendor who tells you a tool
does is the vendor to avoid.

## Sources used for this mapping

- Regulation (EU) 2024/1689, Official Journal, 12 July 2024
- EU AI Act compliance for SMEs: 2026 checklist — trooper.ai
- EU AI Act: what European SMEs must do before 2 August 2026 — First AI Movers

If you are a lawyer and this table is wrong, please open an issue. It will
be fixed in the open.
