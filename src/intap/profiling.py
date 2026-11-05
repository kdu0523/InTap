"""Build reproducible repository observations with source provenance."""

from __future__ import annotations

import ast
import hashlib
import json
import re

from intap.config import Config
from intap.domain import EngineeringProfile, Evidence, Observation
from intap.ingestion import collect_sources

FEATURES = {
    "snake_case_functions": "Function names follow lowercase snake_case.",
    "return_annotations": "Functions declare a return annotation.",
    "function_docstrings": "Functions include a docstring.",
    "async_functions": "Functions use async def.",
}


def build_profile(config: Config) -> EngineeringProfile:
    sources, skipped = collect_sources(config)
    if not sources:
        raise ValueError("No parseable Python files found in the configured source root")
    totals = {key: 0 for key in FEATURES}
    examples: dict[str, list[Evidence]] = {key: [] for key in FEATURES}
    functions = 0
    for source in sources:
        for node in ast.walk(source.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            functions += 1
            checks = {
                "snake_case_functions": bool(re.fullmatch(r"_*[a-z][a-z0-9_]*", node.name)),
                "return_annotations": node.returns is not None,
                "function_docstrings": ast.get_docstring(node) is not None,
                "async_functions": isinstance(node, ast.AsyncFunctionDef),
            }
            for key, matches in checks.items():
                if matches:
                    totals[key] += 1
                    if len(examples[key]) < 20:
                        examples[key].append(Evidence(source.path, node.lineno, source.sha256))
    manifest = [(source.path, source.sha256) for source in sources]
    snapshot = hashlib.sha256(json.dumps(manifest).encode()).hexdigest()
    return EngineeringProfile(
        company_id=config.company_id,
        source_name=config.source_root.name,
        snapshot_sha256=snapshot,
        files_analyzed=len(sources),
        observations=tuple(
            Observation(key, description, totals[key], functions, tuple(examples[key]))
            for key, description in FEATURES.items()
        ),
        skipped_files=tuple(skipped),
    )
