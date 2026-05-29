from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .models import Evidence, Fact

PATH_RE = re.compile(r"(?<![\w.])(?:/tmp|/workspace|\./fixtures|\.\/demo|[A-Za-z0-9_.-]+/)[^\s`'\"\]\)]+")
COMMAND_RE = re.compile(r"\b(?:python(?:3)?|pytest|npm|pnpm|uv|git|argobrain-memory)\b[^\n.;]*")
DECISION_RE = re.compile(r"\bdecision\s*:\s*(.+)", re.IGNORECASE)
BLOCKER_RE = re.compile(r"\bblocker\s*:\s*(.+)", re.IGNORECASE)
PREFERENCE_RE = re.compile(r"\bpreference\s*:\s*(.+)", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        events.append(json.loads(raw))
    return events


def event_text(event: dict[str, Any]) -> str:
    content = event.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return ""


def stable_id(*parts: str) -> str:
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]


def _fact(
    *,
    fact_type: str,
    fact: str,
    what_for: str,
    why_it_matters: str,
    scope: str,
    evidence: Evidence,
    status: str = "active",
) -> Fact:
    return Fact(
        id=stable_id(fact_type, fact, evidence.pointer()),
        fact_type=fact_type,
        fact=fact.strip(),
        what_for=what_for,
        why_it_matters=why_it_matters,
        scope=scope,
        status=status,
        evidence=evidence.pointer(),
    )


def extract_facts(events: list[dict[str, Any]], *, source: str, scope: str = "session") -> list[Fact]:
    facts: list[Fact] = []
    seen: set[str] = set()

    def add(fact: Fact) -> None:
        key = f"{fact.fact_type}:{fact.fact}:{fact.evidence}"
        if key not in seen:
            seen.add(key)
            facts.append(fact)

    for idx, event in enumerate(events):
        text = event_text(event)
        evidence = Evidence(source, idx)

        for match in DECISION_RE.findall(text):
            add(
                _fact(
                    fact_type="decision",
                    fact=match,
                    what_for="preserving explicit session decisions",
                    why_it_matters="decisions are easy to lose in prose summaries",
                    scope=scope,
                    evidence=evidence,
                )
            )
        for match in BLOCKER_RE.findall(text):
            add(
                _fact(
                    fact_type="blocker",
                    fact=match,
                    what_for="continuation planning",
                    why_it_matters="future agents need unresolved blockers",
                    scope=scope,
                    evidence=evidence,
                )
            )
        for match in PREFERENCE_RE.findall(text):
            add(
                _fact(
                    fact_type="preference",
                    fact=match,
                    what_for="user/workflow preference retention",
                    why_it_matters="preferences should not depend on summary wording",
                    scope=scope,
                    evidence=evidence,
                )
            )
        for match in PATH_RE.findall(text):
            add(
                _fact(
                    fact_type="path",
                    fact=match.rstrip(".,"),
                    what_for="locating referenced files or artifacts",
                    why_it_matters="paths are compact and high-value continuation facts",
                    scope=scope,
                    evidence=evidence,
                )
            )
        for match in COMMAND_RE.findall(text):
            add(
                _fact(
                    fact_type="command",
                    fact=match.strip(),
                    what_for="replaying verification or build steps",
                    why_it_matters="commands provide concrete operational evidence",
                    scope=scope,
                    evidence=evidence,
                )
            )

    return facts

