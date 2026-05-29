from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Mode = Literal["off", "baseline", "cortex", "external"]


@dataclass(frozen=True)
class Evidence:
    source: str
    event_index: int | None = None

    def pointer(self) -> str:
        if self.event_index is None:
            return self.source
        return f"{self.source}#event={self.event_index}"


@dataclass(frozen=True)
class Fact:
    id: str
    fact_type: str
    fact: str
    what_for: str
    why_it_matters: str
    scope: str
    status: str
    evidence: str
    extracted_by: str = "argobrain-memory.heuristic-v1"
    record_type: str = "typed_fact_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Episode:
    id: str
    reason: str
    start_event: int
    end_event: int
    source: str
    text: str
    token_estimate: int
    schema: str = "compaction_episode_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

