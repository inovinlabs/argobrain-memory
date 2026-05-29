from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_benchmark
from .models import Mode
from .store import MemoryStore


def cmd_ingest(args: argparse.Namespace) -> int:
    store = MemoryStore(Path(args.output))
    result = store.ingest(Path(args.transcript), reason=args.reason, scope=args.scope)
    print(json.dumps(result, sort_keys=True))
    return 0


def cmd_recall(args: argparse.Namespace) -> int:
    store = MemoryStore(Path(args.memory_root))
    for row in store.recall(args.query, limit=args.limit):
        print(json.dumps(row, sort_keys=True))
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    modes: list[Mode]
    if args.mode == "all":
        modes = ["off", "baseline", "cortex", "external"]
    else:
        modes = [args.mode]
    results = [run_benchmark(Path(args.fixture), mode=mode, output=Path(args.output)) for mode in modes]
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="argobrain-memory")
    sub = parser.add_subparsers(required=True)

    ingest = sub.add_parser("ingest", help="ingest a transcript into a memory root")
    ingest.add_argument("--transcript", required=True)
    ingest.add_argument("--output", required=True)
    ingest.add_argument("--reason", default="ingest")
    ingest.add_argument("--scope", default="session")
    ingest.set_defaults(func=cmd_ingest)

    recall = sub.add_parser("recall", help="query a memory root")
    recall.add_argument("--memory-root", required=True)
    recall.add_argument("--query", required=True)
    recall.add_argument("--limit", type=int, default=5)
    recall.set_defaults(func=cmd_recall)

    bench = sub.add_parser("benchmark", help="score retention for one or more memory modes")
    bench.add_argument("--fixture", required=True)
    bench.add_argument("--output", required=True)
    bench.add_argument("--mode", choices=["off", "baseline", "cortex", "external", "all"], default="all")
    bench.set_defaults(func=cmd_benchmark)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

