"""Validate the ingestion shape and cross-field feature invariants."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any


def validate_ingestion(
    payload: dict[str, Any], schema: dict[str, Any], catalog: dict[str, Any]
) -> None:
    def finite_json(value: Any) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        if isinstance(value, dict):
            for item in value.values():
                finite_json(item)
        elif isinstance(value, list):
            for item in value:
                finite_json(item)

    finite_json(payload)
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as error:
        raise ValueError("Install InTap's schema extra: python -m pip install -e '.[schema]'") from error

    Draft202012Validator.check_schema(schema)
    checker = FormatChecker()
    if not {"date-time", "uuid", "uri"}.issubset(checker.checkers):
        raise ValueError("Missing JSON Schema format validators; install InTap's .[schema] extra")
    validator = Draft202012Validator(schema, format_checker=checker)
    errors = sorted(validator.iter_errors(payload), key=lambda error: str(list(error.path)))
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.path) or "<root>"
        raise ValueError(f"Schema violation at {location}: {error.message}")
    if payload["feature_catalog_version"] != catalog.get("catalog_version"):
        raise ValueError("Feature catalog version mismatch")

    def timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00").replace("z", "+00:00"))

    occurred = timestamp(payload["occurred_at"])
    available = timestamp(payload["available_at"])
    ingested = timestamp(payload["ingested_at"])
    if not occurred <= available <= ingested:
        raise ValueError("Expected occurred_at <= available_at <= ingested_at")
    if timestamp(payload["retention"]["expires_at"]) <= ingested:
        raise ValueError("retention.expires_at must be later than ingested_at")
    for link in payload["links"]:
        if timestamp(link["available_at"]) > ingested:
            raise ValueError("A link cannot be known after its enclosing ingestion revision")

    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    for feature in payload["features"]:
        definition = catalog["features"].get(feature["name"])
        if definition is None:
            raise ValueError(f"Unknown catalog feature: {feature['name']}")
        if feature["definition_version"] != definition["definition_version"]:
            raise ValueError(f"Definition version mismatch: {feature['name']}")
        if feature["unit"] != definition["unit"]:
            raise ValueError(f"Unit mismatch: {feature['name']}")
        if feature["phase"] not in definition["allowed_phases"]:
            raise ValueError(f"Invalid phase: {feature['name']}")
        if feature["method"] not in definition["allowed_methods"]:
            raise ValueError(f"Invalid extraction method: {feature['name']}")
        if timestamp(feature["available_at"]) < ingested:
            raise ValueError("Feature available_at must be at or after ingested_at")
        key = (feature["name"], feature["entity_id"], feature["phase"])
        if key in seen:
            raise ValueError(f"Duplicate feature measurement: {key}")
        seen[key] = feature
        scope = feature["scope"]
        if "start_line" in scope and scope["end_line"] < scope["start_line"]:
            raise ValueError("Feature scope end_line cannot precede start_line")
        for pointer in feature["evidence"]:
            current: Any = payload
            try:
                for part in pointer[1:].split("/"):
                    part = part.replace("~1", "/").replace("~0", "~")
                    current = current[int(part)] if isinstance(current, list) else current[part]
            except (KeyError, IndexError, ValueError, TypeError) as error:
                raise ValueError(f"Unresolved evidence pointer: {pointer}") from error
        if feature["status"] == "unavailable":
            continue
        value = feature["value"]
        if not Draft202012Validator(definition["value_schema"]).is_valid(value):
            raise ValueError(f"Value outside feature definition: {feature['name']}")
        if isinstance(value, (int, float)) and not math.isfinite(value):
            raise ValueError("Feature values must be finite")
        if feature["phase"] != "delta" and "absolute_minimum" in definition:
            if value < definition["absolute_minimum"]:
                raise ValueError(f"Value below absolute minimum: {feature['name']}")
        if definition.get("requires_fraction"):
            if "numerator" not in feature or "denominator" not in feature:
                raise ValueError(f"Ratio requires numerator and denominator: {feature['name']}")
            if not math.isclose(value, feature["numerator"] / feature["denominator"], rel_tol=1e-6, abs_tol=1e-9):
                raise ValueError(f"Ratio does not match its counts: {feature['name']}")

    for (name, entity, phase), feature in seen.items():
        if phase != "delta" or feature["status"] == "unavailable":
            continue
        before = seen.get((name, entity, "before"), {})
        after = seen.get((name, entity, "after"), {})
        if not all(type(side.get("value")) in (int, float) for side in (before, after)):
            raise ValueError(f"A numeric delta requires matched before/after values: {name}")
        if not math.isclose(feature["value"], after["value"] - before["value"], rel_tol=1e-6, abs_tol=1e-9):
            raise ValueError(f"Inconsistent before/after delta: {name}")
