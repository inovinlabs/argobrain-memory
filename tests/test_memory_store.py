from __future__ import annotations

from pathlib import Path

from argobrain_memory.benchmark import run_benchmark
from argobrain_memory.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "demo-session"


def test_ingest_writes_facts_episode_summary_and_index(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "memory")
    result = store.ingest(FIXTURE / "session.jsonl", reason="test", scope="test")

    assert result["facts"] >= 5
    assert (tmp_path / "memory" / "facts.jsonl").is_file()
    assert (tmp_path / "memory" / "active-derived-summary.md").is_file()
    assert (tmp_path / "memory" / "recall.sqlite").is_file()
    assert list((tmp_path / "memory" / "episodes").glob("*.json"))


def test_recall_finds_path_fact(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "memory")
    store.ingest(FIXTURE / "session.jsonl", reason="test", scope="test")

    rows = store.recall("demo-memory")
    assert rows
    assert any("/tmp/" in row["snippet"] and "session.jsonl" in row["snippet"] for row in rows)


def test_benchmark_cortex_outscores_off(tmp_path: Path) -> None:
    off = run_benchmark(FIXTURE, mode="off", output=tmp_path / "off")
    cortex = run_benchmark(FIXTURE, mode="cortex", output=tmp_path / "cortex")

    assert off["retention"] == 0
    assert cortex["retention"] >= 0.8
