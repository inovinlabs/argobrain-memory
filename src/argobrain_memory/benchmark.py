from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .extractors import event_text, extract_facts, load_jsonl
from .models import Mode
from .store import MemoryStore, atomic_write


def _load_expected(fixture: Path) -> list[dict[str, str]]:
    return json.loads((fixture / "expected-facts.json").read_text(encoding="utf-8"))


def _score(expected: list[dict[str, str]], haystack: str) -> dict[str, Any]:
    found = []
    missing = []
    lower = haystack.lower()
    for item in expected:
        needle = item["fact"].lower()
        if needle in lower:
            found.append(item)
        else:
            missing.append(item)
    total = len(expected)
    return {
        "expected": total,
        "found": len(found),
        "missing": len(missing),
        "retention": 1.0 if total == 0 else round(len(found) / total, 3),
        "missing_facts": missing,
    }


def _baseline_summary(events: list[dict[str, Any]]) -> str:
    text = "\n\n".join(event_text(event) for event in events if event_text(event))
    return text[:600] + "\n...\n" + text[-600:]


def run_benchmark(fixture: Path, *, mode: Mode, output: Path) -> dict[str, Any]:
    transcript = fixture / "session.jsonl"
    expected = _load_expected(fixture)
    events = load_jsonl(transcript)
    output.mkdir(parents=True, exist_ok=True)

    if mode == "off":
        haystack = ""
    elif mode == "baseline":
        haystack = _baseline_summary(events)
        atomic_write(output / "baseline-summary.md", haystack)
    elif mode == "cortex":
        store_root = output / "memory"
        if store_root.exists():
            shutil.rmtree(store_root)
        store = MemoryStore(store_root)
        store.ingest(transcript, reason="benchmark", scope="benchmark")
        haystack = "\n".join(raw for raw in (store_root / "facts.jsonl").read_text(encoding="utf-8").splitlines())
    elif mode == "external":
        facts = extract_facts(events, source=str(transcript), scope="external-placeholder")
        haystack = "\n".join(f.fact for f in facts if f.fact_type in {"decision", "path"})
    else:
        raise ValueError(f"unsupported mode: {mode}")

    score = _score(expected, haystack)
    result = {"mode": mode, **score}
    atomic_write(output / f"benchmark-{mode}.json", json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

