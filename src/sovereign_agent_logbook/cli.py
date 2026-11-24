"""Command-line helper for people who are not running an agent right now.

    logbook verify  [--path logbook.jsonl] [--anchor anchors.jsonl]
    logbook anchor  [--path logbook.jsonl] --to anchors.jsonl
    logbook export  [--path logbook.jsonl] [--format json|csv]
    logbook tail    [--path logbook.jsonl] [--limit 20]
    logbook log     [--path logbook.jsonl] --agent ID --model M --action A [...]

`log` writes one event, for scripts, cron jobs, CI and agents that do not
speak MCP. It prints the stored record (seq, hash) as one JSON line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .chain import anchor_line, check_anchors
from .paths import resolve_path
from .store import Event, Logbook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logbook")
    parser.add_argument(
        "--path", default="./logbook.jsonl",
        help="logbook file; may contain {project} or {cwd}",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    ver = sub.add_parser("verify", help="check the hash chain")
    ver.add_argument("--anchor", metavar="FILE", help="also check this anchor file")
    anc = sub.add_parser("anchor", help="append the latest (seq, hash) to a second place")
    anc.add_argument("--to", required=True, metavar="FILE", help="anchor file to append to")
    exp = sub.add_parser("export", help="dump the logbook")
    exp.add_argument("--format", choices=["json", "csv"], default="json")
    tail = sub.add_parser("tail", help="show recent events")
    tail.add_argument("--limit", type=int, default=20)
    log = sub.add_parser("log", help="append one event")
    log.add_argument("--agent", required=True, dest="agent_id")
    log.add_argument("--model", required=True)
    log.add_argument("--action", required=True)
    log.add_argument("--reason", default="")
    log.add_argument("--approval", choices=["human", "auto", "none"], default="none")
    log.add_argument("--approved-by")
    log.add_argument("--approval-rule")
    log.add_argument(
        "--outcome",
        choices=["success", "error", "escalated", "refused", "pending"],
        default="pending",
    )
    log.add_argument("--summary", default="", dest="result_summary")
    log.add_argument("--run-id")
    log.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE")
    log.add_argument("--tag", action="append", default=[])
    log.add_argument(
        "--corrects", type=int, metavar="SEQ",
        help="seq of an earlier event this one corrects; the earlier line stays as it is",
    )

    args = parser.parse_args(argv)
    lb = Logbook(resolve_path(args.path))

    if args.cmd == "verify":
        res = lb.verify()
        problems = list(res.problems)
        checked = 0
        if args.anchor:
            anchor_problems, checked = check_anchors(lb.path, Path(args.anchor))
            problems += anchor_problems
        if not problems:
            note = ""
            if args.anchor:
                note = f", {checked} anchor{'s' if checked != 1 else ''} checked"
            print(f"OK — {res.events} events, chain intact{note}")
            return 0
        print(f"BROKEN — {res.events} events, {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.cmd == "anchor":
        try:
            line = json.dumps(anchor_line(lb.path), separators=(",", ":"))
        except ValueError as exc:
            parser.error(str(exc))
        target = Path(args.to)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        print(line)
        return 0

    if args.cmd == "export":
        sys.stdout.write(lb.export(fmt=args.format))
        return 0

    if args.cmd == "log":
        arguments = {}
        for kv in args.arg:
            if "=" not in kv:
                parser.error(f"--arg expects KEY=VALUE, got {kv!r}")
            key, value = kv.split("=", 1)
            arguments[key] = value
        try:
            rec = lb.append(
                Event(
                    agent_id=args.agent_id,
                    model=args.model,
                    action=args.action,
                    arguments=arguments,
                    reason=args.reason,
                    approval=args.approval,
                    approved_by=args.approved_by,
                    approval_rule=args.approval_rule,
                    outcome=args.outcome,
                    result_summary=args.result_summary,
                    run_id=args.run_id,
                    tags=args.tag,
                    corrects=args.corrects,
                )
            )
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps({"seq": rec["seq"], "hash": rec["hash"]}))
        return 0

    if args.cmd == "tail":
        for e in lb.recent(limit=args.limit):
            print(json.dumps(e, ensure_ascii=False))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
