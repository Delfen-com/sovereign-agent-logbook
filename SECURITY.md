# Security policy

## Reporting a vulnerability

Email **security@delfen.ai** with a description and, if possible, a
reproduction. Please do not open a public issue for an unreported
vulnerability.

What you can expect from us:

- Acknowledgement within **3 working days**.
- An assessment and a planned fix date within **10 working days**.
- Credit in `CHANGELOG.md` when the fix ships, unless you prefer otherwise.

## Scope

In scope: the chain verification, secret masking, the MCP server, the
CLI, the Dockerfile.

Out of scope (documented, not a bug): the limits listed in
`THREAT-MODEL.md` — truncation without anchoring, an attacker with root on
the host, an agent that is not configured to log.

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes, until 0.2 ships |

## Fixed issues

None yet. This section lists every fixed security issue, with date and
reporter credit.
