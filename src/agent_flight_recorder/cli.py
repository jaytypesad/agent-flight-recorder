"""Command line interface for Agent Flight Recorder."""

from __future__ import annotations

from dataclasses import asdict
import argparse
import json
import sys

from .recorder import read_jsonl
from .signatures import select_eval_candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find high-risk spans in an agent trace.")
    parser.add_argument("trace", help="Path to a JSONL trace file")
    parser.add_argument("--limit", type=int, default=5, help="Maximum findings to print")
    args = parser.parse_args(argv)

    events = read_jsonl(args.trace)
    findings = select_eval_candidates(events, limit=args.limit)
    for finding in findings:
        print(json.dumps(asdict(finding), ensure_ascii=True, sort_keys=True))
    return 1 if any(finding.severity == "high" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
