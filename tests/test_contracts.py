from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from intap.contracts import validate_ingestion

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("jsonschema"), "Install .[dev] for ingestion-contract tests")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "schemas/ingestion-event.schema.json").read_text())
        cls.catalog = json.loads((ROOT / "schemas/feature-catalog.json").read_text())
        cls.fixture = json.loads((ROOT / "examples/ingestion/git-diff.json").read_text())

    def setUp(self):
        self.payload = copy.deepcopy(self.fixture)

    def validate(self):
        validate_ingestion(self.payload, self.schema, self.catalog)

    def test_all_source_fixtures(self):
        for path in (ROOT / "examples/ingestion").glob("*.json"):
            with self.subTest(source=path.name):
                validate_ingestion(json.loads(path.read_text()), self.schema, self.catalog)

    def test_rejects_wrong_source_and_unknown_properties(self):
        self.payload["source"]["system"] = "jira"
        with self.assertRaisesRegex(ValueError, "Schema violation"):
            self.validate()
        self.payload = copy.deepcopy(self.fixture)
        self.payload["personality_score"] = .9
        with self.assertRaisesRegex(ValueError, "Schema violation"):
            self.validate()

    def test_enforces_real_timestamp_formats_and_order(self):
        self.payload["occurred_at"] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "Schema violation"):
            self.validate()
        self.payload["occurred_at"] = "2026-12-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "occurred_at"):
            self.validate()

    def test_missing_is_not_zero(self):
        feature = self.payload["features"][0]
        feature.update(status="unavailable", value=None, missing_reason="parse_failure")
        self.payload["features"] = [feature]
        self.validate()
        feature["value"] = 0
        with self.assertRaisesRegex(ValueError, "Schema violation"):
            self.validate()

    def test_inconsistent_delta_is_rejected(self):
        self.payload["features"][2]["value"] = 3
        with self.assertRaisesRegex(ValueError, "delta"):
            self.validate()

    def test_delta_needs_both_matched_sides(self):
        del self.payload["features"][0]
        with self.assertRaisesRegex(ValueError, "matched before/after"):
            self.validate()

    def test_ratio_arithmetic_and_zero_denominator(self):
        self.payload["features"][3]["value"] = .3
        with self.assertRaisesRegex(ValueError, "Ratio"):
            self.validate()
        self.payload["features"][3]["denominator"] = 0
        with self.assertRaisesRegex(ValueError, "Schema violation"):
            self.validate()

    def test_evidence_must_resolve(self):
        self.payload["features"][0]["evidence"] = ["/payload/files/99"]
        with self.assertRaisesRegex(ValueError, "Unresolved evidence"):
            self.validate()

    def test_duplicates_and_unknown_features(self):
        self.payload["features"].append(copy.deepcopy(self.payload["features"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.validate()
        self.payload = copy.deepcopy(self.fixture)
        self.payload["features"][0]["name"] = "personality.intelligence"
        with self.assertRaisesRegex(ValueError, "Unknown catalog"):
            self.validate()

    def test_units_ranges_and_nonfinite_numbers(self):
        self.payload["features"][0]["value"] = 0
        with self.assertRaisesRegex(ValueError, "absolute minimum"):
            self.validate()
        self.payload["features"][0]["value"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            self.validate()
        self.payload["features"][0]["value"] = 8
        self.payload["features"][0]["unit"] = "hours"
        with self.assertRaisesRegex(ValueError, "Unit mismatch"):
            self.validate()

    def test_features_cannot_predate_ingestion(self):
        self.payload["features"][0]["available_at"] = "2026-11-04T14:00:00Z"
        with self.assertRaisesRegex(ValueError, "Feature available_at"):
            self.validate()

    def test_model_annotations_need_model_provenance(self):
        self.payload = json.loads((ROOT / "examples/ingestion/pr-comment.json").read_text())
        del self.payload["features"][0]["extractor"]["model_id"]
        with self.assertRaisesRegex(ValueError, "Schema violation"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
