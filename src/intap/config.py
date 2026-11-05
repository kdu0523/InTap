"""Load an explicit company scope and human-authored engineering rules."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from intap.domain import nonempty_text, text_list

DEFAULT_EXCLUDES = (
    "vendor", "node_modules", "build", "dist", "venv", "__pycache__", "site-packages"
)


@dataclass(frozen=True)
class Config:
    company_id: str
    source_root: Path
    rules: tuple[str, ...] = ()
    max_file_bytes: int = 200_000
    max_files: int = 1_000
    exclude_dirs: tuple[str, ...] = DEFAULT_EXCLUDES

    def __post_init__(self) -> None:
        nonempty_text(self.company_id, "company.id")
        for name, value in (("max_file_bytes", self.max_file_bytes), ("max_files", self.max_files)):
            if type(value) is not int or value <= 0:
                raise ValueError(f"ingestion.{name} must be a positive integer")


def load_config(path: Path) -> Config:
    with path.open("rb") as handle:
        value = tomllib.load(handle)
    company = value.get("company", {})
    ingestion = value.get("ingestion", {})
    agent = value.get("agent", {})
    if not all(isinstance(section, dict) for section in (company, ingestion, agent)):
        raise ValueError("company, ingestion, and agent must be TOML tables")
    source = nonempty_text(ingestion.get("root"), "ingestion.root")
    excludes = text_list(ingestion.get("exclude_dirs", []), "ingestion.exclude_dirs")
    return Config(
        company_id=nonempty_text(company.get("id"), "company.id"),
        source_root=(path.resolve().parent / source).resolve(),
        rules=text_list(agent.get("rules", []), "agent.rules"),
        max_file_bytes=ingestion.get("max_file_bytes", 200_000),
        max_files=ingestion.get("max_files", 1_000),
        exclude_dirs=tuple(sorted(set(DEFAULT_EXCLUDES + excludes))),
    )
