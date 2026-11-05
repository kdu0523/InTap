"""Contracts shared by ingestion, profiling, and agent adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Evidence:
    path: str
    line: int
    source_sha256: str


@dataclass(frozen=True)
class Observation:
    key: str
    description: str
    matches: int
    total: int
    evidence: tuple[Evidence, ...]

    @property
    def rate(self) -> float:
        """Observed frequency, not statistical confidence or an approved rule."""
        return self.matches / self.total if self.total else 0.0


@dataclass(frozen=True)
class EngineeringProfile:
    company_id: str
    source_name: str
    snapshot_sha256: str
    files_analyzed: int
    observations: tuple[Observation, ...]
    skipped_files: tuple[dict[str, str], ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def text_list(value: Any, field: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f"{field} must be a {'nonempty ' if required else ''}list")
    return tuple(nonempty_text(item, field) for item in value)


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    title: str
    description: str
    acceptance_criteria: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> TaskSpec:
        return cls(
            task_id=nonempty_text(value.get("task_id"), "task_id"),
            title=nonempty_text(value.get("title"), "title"),
            description=nonempty_text(value.get("description"), "description"),
            acceptance_criteria=text_list(
                value.get("acceptance_criteria"), "acceptance_criteria", required=True
            ),
        )
