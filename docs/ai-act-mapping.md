# EU AI Act — what this tool helps with, and what it does not

**This is not legal advice.** It is a plain-language map from features in
this repository to the obligations people ask about. Your own classification
of your AI system (minimal / limited / high-risk) is yours to make, and an
obligation is met by your organisation's process, not by installing a tool.
Please copy this table into your own evidence file and strike out what does
not apply.

Regulation (EU) 2024/1689, as amended by Regulation (EU) 2026/1744 (the
Digital Omnibus on AI, adopted 8 July 2026, in force 27 July 2026). The
Omnibus amended Article 113: the high-risk obligations in Chapter III
(including Articles 12, 14 and 26) apply from **2 December 2027** for
systems under Article 6(2) / Annex III, and from **2 August 2028** for
systems under Article 6(1) / Annex I (AI built into regulated products).
Until then these are duties to prepare for, not duties in force. Check the
current text before relying on a date.

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

- Regulation (EU) 2024/1689 (AI Act), Official Journal, 12 July 2024 — https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- Regulation (EU) 2026/1744 (Digital Omnibus on AI), 8 July 2026, in force 27 July 2026 — https://eur-lex.europa.eu/eli/reg/2026/1744/oj
- Article 113 as amended, consolidated text — https://artificialintelligenceact.eu/article/113/

If you are a lawyer and this table is wrong, please open an issue. It will
be fixed in the open.
