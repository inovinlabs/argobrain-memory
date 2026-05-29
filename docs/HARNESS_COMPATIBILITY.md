# Harness Compatibility

Argobrain Memory is designed to be harness-neutral.

## Contract

Any harness can use it if it can provide a JSONL transcript with events like:

```json
{"role":"user","content":"Decision: raw transcript remains authoritative."}
{"role":"assistant","content":"Command: python3 -m pytest tests."}
```

Required fields:

- `role`: usually `user`, `assistant`, `tool`, or harness-specific labels.
- `content`: string content, or a list of text blocks with `{"text": "..."}`.

Optional fields:

- `timestamp`
- `session_id`
- `model`
- `cwd`
- `metadata`

## Works With

The core package can be wrapped by:

- Codex
- Hermes
- Claude Code
- Gemini CLI
- OpenCode
- Kimi-style session exporters
- custom agent harnesses
- CI jobs replaying saved transcripts

The harness-specific adapter only needs to normalize its transcript into JSONL and call:

```bash
argobrain-memory ingest --transcript session.jsonl --output memory/
```

## What Is Not Required

- No daemon.
- No MCP server.
- No cloud model.
- No live hooks.
- No specific agent runtime.
- No private file layout.

## Adapter Pattern

Recommended adapter responsibilities:

1. Export or stream raw events to `session.jsonl`.
2. Call `argobrain-memory ingest`.
3. Store returned artifacts beside the session archive.
4. Inject `active-derived-summary.md` only as derived context.
5. Keep raw transcript as authority.

## Mode Benchmarking

Harnesses should support a mode switch:

```text
off       raw transcript only
baseline  rolling prose summary only
cortex    Argobrain Memory typed facts + episodes + recall
external  external adapter comparison
```

This makes it possible to compare default harness behavior against Argobrain Memory and against future adapters for systems like GBrain, Mem0, or Graphiti.

