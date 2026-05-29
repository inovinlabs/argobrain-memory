from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .extractors import event_text, extract_facts, load_jsonl
from .models import Episode, Fact


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


class MemoryStore:
    def __init__(self, root: Path, *, lock_timeout: float = 10.0):
        self.root = root
        self.lock_timeout = lock_timeout
        self.facts_path = root / "facts.jsonl"
        self.episodes_dir = root / "episodes"
        self.summary_path = root / "active-derived-summary.md"
        self.index_path = root / "recall.sqlite"
        self.lock_path = root / ".memory.lock"

    @contextmanager
    def lock(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        while True:
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode("ascii"))
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() - start > self.lock_timeout:
                    raise TimeoutError(f"memory store locked: {self.lock_path}")
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass

    def ingest(self, transcript: Path, *, reason: str = "ingest", scope: str = "session") -> dict[str, str | int]:
        events = load_jsonl(transcript)
        with self.lock():
            facts = extract_facts(events, source=str(transcript), scope=scope)
            self._append_facts(facts)
            episode = self._write_episode(events, source=str(transcript), reason=reason)
            self._write_active_summary(facts, episode)
            self.rebuild_index()
        return {
            "facts": len(facts),
            "episode": episode.id,
            "root": str(self.root),
        }

    def _append_facts(self, facts: list[Fact]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.facts_path.open("a", encoding="utf-8") as handle:
            for fact in facts:
                handle.write(json.dumps(fact.to_dict(), sort_keys=True) + "\n")

    def _write_episode(self, events: list[dict[str, object]], *, source: str, reason: str) -> Episode:
        text = "\n\n".join(event_text(event) for event in events if event_text(event))
        episode = Episode(
            id=f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:12]}",
            reason=reason,
            start_event=0,
            end_event=len(events),
            source=source,
            text=text[:12000],
            token_estimate=max(1, len(text) // 4),
        )
        path = self.episodes_dir / f"{episode.id}.json"
        atomic_write(path, json.dumps(episode.to_dict(), indent=2, sort_keys=True) + "\n")
        return episode

    def _write_active_summary(self, facts: list[Fact], episode: Episode) -> None:
        lines = [
            "# Active Derived Summary",
            "",
            "Status: derived/not doctrine. Raw transcript remains authoritative.",
            "",
            f"Latest episode: `{episode.id}`",
            "",
            "## Open Facts",
        ]
        for fact in facts[:40]:
            lines.append(f"- **{fact.fact_type}** `{fact.status}`: {fact.fact} ({fact.evidence})")
        atomic_write(self.summary_path, "\n".join(lines) + "\n")

    def rebuild_index(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.index_path)
        try:
            con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(kind, ref, text)")
            con.execute("DELETE FROM memory_fts")
            if self.facts_path.exists():
                for raw in self.facts_path.read_text(encoding="utf-8").splitlines():
                    fact = json.loads(raw)
                    con.execute(
                        "INSERT INTO memory_fts(kind, ref, text) VALUES (?, ?, ?)",
                        ("fact", fact["evidence"], f"{fact['fact_type']}: {fact['fact']}"),
                    )
            for path in sorted(self.episodes_dir.glob("*.json")):
                episode = json.loads(path.read_text(encoding="utf-8"))
                con.execute(
                    "INSERT INTO memory_fts(kind, ref, text) VALUES (?, ?, ?)",
                    ("episode", str(path), episode.get("text", "")),
                )
            con.commit()
        finally:
            con.close()

    def recall(self, query: str, *, limit: int = 5) -> list[dict[str, str]]:
        match_query = query
        if any(ch in query for ch in '-/:."\''):
            match_query = '"' + query.replace('"', '""') + '"'
        con = sqlite3.connect(self.index_path)
        try:
            rows = con.execute(
                "SELECT kind, ref, snippet(memory_fts, 2, '[', ']', ' ... ', 12) "
                "FROM memory_fts WHERE memory_fts MATCH ? LIMIT ?",
                (match_query, limit),
            ).fetchall()
        finally:
            con.close()
        return [{"kind": row[0], "ref": row[1], "snippet": row[2]} for row in rows]
