# ArgoBrain-Memory

Portable, evidence-linked memory for AI agent sessions.

Argobrain Memory keeps raw session transcripts authoritative and writes all memory as rebuildable derived artifacts:

- append-only compression episodes;
- typed fact ledgers with evidence pointers;
- active derived summaries;
- SQLite FTS recall indexes;
- replay benchmarks for retention across repeated compaction.

This repository is the OSS-clean extraction of a private Cortex/Hermes memory design. It ships with synthetic fixtures only. It does not include private transcripts, operator paths, credentials, host inventory, or live agent hooks.

## Why

Naive agent memory often recursively summarizes summaries. That loses small but operationally important details: paths, commands, decisions, blockers, preferences, and routing facts.

Argobrain Memory uses a different contract:

1. Raw transcript/event log is the source of truth.
2. Episodes and typed facts are append-only derived memory.
3. Summaries and indexes are rebuildable views.
4. Every fact points back to evidence.
5. Benchmarks compare memory modes before adoption.

## Modes

Use modes to compare behavior:

```text
off       no enhanced memory; raw transcript only
baseline  old-style rolling prose summary
cortex    full typed ledger, episodes, active summary, FTS recall
external  placeholder adapter mode for future GBrain/Mem0/Graphiti comparisons
```

CLI example:

```bash
python -m argobrain_memory.cli benchmark \
  --fixture fixtures/demo-session \
  --mode cortex \
  --output /tmp/argobrain-memory-demo
```

Run all modes:

```bash
python -m argobrain_memory.cli benchmark \
  --fixture fixtures/demo-session \
  --mode all \
  --output /tmp/argobrain-memory-demo
```

## Artifact Layout

```text
memory-root/
  active-derived-summary.md
  facts.jsonl
  recall.sqlite
  episodes/
    <episode-id>.json
```

## Safety

- No hooks run by default.
- No cloud calls are made by this core package.
- No generated summary is doctrine.
- SQLite indexes are rebuildable and non-authoritative.
- Public examples use synthetic data only.

## Status

Initial 0.1.0 release. The core architecture is stable enough for benchmarking and adapter development. Public package publishing should still wait for a fresh-clone/fake-HOME release gate.
