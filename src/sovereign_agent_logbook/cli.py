"""Command-line helper for people who are not running an agent right now.

    logbook verify  [--path logbook.jsonl]
    logbook export  [--path logbook.jsonl] [--format json|csv]
    logbook tail    [--path logbook.jsonl] [--limit 20]
"""

from __future__ import annotations

import argparse
import json
import sys

from .store import Logbook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logbook")
    parser.add_argument("--path", default="./logbook.jsonl")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify", help="check the hash chain")
    exp = sub.add_parser("export", help="dump the logbook")
    exp.add_argument("--format", choices=["json", "csv"], default="json")
    tail = sub.add_parser("tail", help="show recent events")
    tail.add_argument("--limit", type=int, default=20)

    args = parser.parse_args(argv)
    lb = Logbook(args.path)

    if args.cmd == "verify":
        res = lb.verify()
        if res.ok:
            print(f"OK — {res.events} events, chain intact")
            return 0
        print(f"BROKEN — {res.events} events, {len(res.problems)} problem(s):")
        for p in res.problems:
            print(f"  - {p}")
        return 1

    if args.cmd == "export":
        sys.stdout.write(lb.export(fmt=args.format))
        return 0

    if args.cmd == "tail":
        for e in lb.recent(limit=args.limit):
            print(json.dumps(e, ensure_ascii=False))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
