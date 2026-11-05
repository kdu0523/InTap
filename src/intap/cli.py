"""Offline CLI for the first InTap learning-to-context vertical slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from intap.agent import prepare_run
from intap.config import load_config
from intap.contracts import validate_ingestion
from intap.domain import TaskSpec
from intap.profiling import build_profile


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="InTap engineering knowledge framework")
    parser.add_argument("--config", type=Path, default=Path("intap.toml"))
    commands = parser.add_subparsers(dest="command", required=True)
    profile_command = commands.add_parser("profile", help="Observe coding patterns in Python files")
    profile_command.add_argument("--output", type=Path, required=True)
    prepare_command = commands.add_parser("prepare", help="Prepare an agent task context bundle")
    prepare_command.add_argument("--profile", type=Path, required=True)
    prepare_command.add_argument("--task", type=Path, required=True)
    prepare_command.add_argument("--output", type=Path, required=True)
    validate_command = commands.add_parser("validate-ingestion", help="Validate an ingestion event and its feature semantics")
    validate_command.add_argument("--payload", type=Path, required=True)
    validate_command.add_argument("--schema", type=Path, default=Path("schemas/ingestion-event.schema.json"))
    validate_command.add_argument("--catalog", type=Path, default=Path("schemas/feature-catalog.json"))
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-ingestion":
            validate_ingestion(read_object(args.payload), read_object(args.schema), read_object(args.catalog))
            print(f"Valid ingestion event: {args.payload}")
            return 0
        config = load_config(args.config)
        if args.command == "profile":
            value = build_profile(config).to_dict()
        else:
            value = prepare_run(
                config, read_object(args.profile), TaskSpec.from_dict(read_object(args.task))
            )
        write_json(args.output, value)
    except (OSError, ValueError) as error:
        print(f"intap: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {args.command} output to {args.output}")
    return 0
