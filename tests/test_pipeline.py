from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from intap.agent import VerificationReport, prepare_run
from intap.cli import main
from intap.config import Config, load_config
from intap.domain import TaskSpec
from intap.evaluation import evaluate_verification
from intap.profiling import build_profile

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.config = Config("demo", self.root)

    def write(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        return path

    def test_counts_and_provenance(self):
        self.write("orders.py", 'def first_order() -> int:\n    """Explain."""\n    return 1\n\nasync def secondOrder():\n    pass\n')
        profile = build_profile(self.config)
        features = {item.key: item for item in profile.observations}
        self.assertEqual(features["snake_case_functions"].matches, 1)
        self.assertEqual(features["return_annotations"].rate, .5)
        self.assertEqual(features["function_docstrings"].matches, 1)
        self.assertEqual(features["async_functions"].matches, 1)
        evidence = features["return_annotations"].evidence[0]
        self.assertEqual((evidence.path, evidence.line), ("orders.py", 1))
        self.assertEqual(len(evidence.source_sha256), 64)

    def test_excludes_hidden_vendor_and_symlinks(self):
        self.write("normal.py", "def normal(): pass\n")
        self.write(".private/hidden.py", "def hidden(): pass\n")
        self.write("vendor/vendor.py", "def vendor(): pass\n")
        (self.root / "linked.py").symlink_to(self.root / "normal.py")
        (self.root / "linked_dir").symlink_to(self.root / "vendor", target_is_directory=True)
        profile = build_profile(self.config)
        self.assertEqual(profile.files_analyzed, 1)
        self.assertIn({"path": "linked.py", "reason": "symlink"}, profile.skipped_files)

    def test_never_executes_source(self):
        marker = self.root / "executed"
        self.write("danger.py", f"open({str(marker)!r}, 'w').write('bad')\n")
        self.assertEqual(build_profile(self.config).files_analyzed, 1)
        self.assertFalse(marker.exists())

    def test_skips_bad_and_oversized_sources(self):
        self.write("valid.py", "def ok(): pass\n")
        self.write("bad.py", "def unfinished(\n")
        self.write("large.py", "# large\n" * 100)
        profile = build_profile(Config("demo", self.root, max_file_bytes=100))
        self.assertEqual(profile.files_analyzed, 1)
        self.assertEqual({item["reason"] for item in profile.skipped_files}, {"unparseable Python", "file size limit"})

    def test_profile_determinism_and_content_invalidation(self):
        path = self.write("valid.py", "def ok(): pass\n")
        first = build_profile(self.config)
        self.assertEqual(first, build_profile(self.config))
        path.write_text("def ok() -> None: pass\n")
        self.assertNotEqual(first.snapshot_sha256, build_profile(self.config).snapshot_sha256)

    def test_no_sources_and_file_limit_fail_clearly(self):
        with self.assertRaisesRegex(ValueError, "No parseable"):
            build_profile(self.config)
        self.write("one.py", "pass\n")
        self.write("two.py", "pass\n")
        with self.assertRaisesRegex(ValueError, "file limit"):
            build_profile(Config("demo", self.root, max_files=1))

    def test_config_is_relative_to_config_file(self):
        config_file = self.write("intap.toml", '[company]\nid="demo"\n[ingestion]\nroot="source"\n')
        config = load_config(config_file)
        self.assertEqual(config.source_root, (self.root / "source").resolve())
        with self.assertRaises(ValueError):
            Config("demo", self.root, max_files=True)

    def test_prepare_enforces_company_boundary(self):
        self.write("valid.py", "def ok(): pass\n")
        profile = json.loads(json.dumps(build_profile(self.config).to_dict()))
        task = TaskSpec("T-1", "Fix", "Fix an issue", ("Tests pass",))
        bundle = prepare_run(self.config, profile, task)
        self.assertEqual(bundle["status"], "prepared")
        self.assertFalse(any(bundle["capabilities"].values()))
        profile["company_id"] = "other-company"
        with self.assertRaisesRegex(ValueError, "company_id"):
            prepare_run(self.config, profile, task)

    def test_task_requires_acceptance_criteria(self):
        with self.assertRaisesRegex(ValueError, "acceptance_criteria"):
            TaskSpec.from_dict({"task_id": "T-1", "title": "Fix", "description": "Fix", "acceptance_criteria": []})

    def test_gate_never_auto_approves(self):
        report = VerificationReport(10, True, True, True, True)
        self.assertEqual(evaluate_verification(report).status, "human_review_required")
        report = VerificationReport(0, True, False, True, True)
        decision = evaluate_verification(report)
        self.assertEqual(decision.status, "blocked")
        self.assertEqual(set(decision.failures), {"tests_missing", "lint_failed"})

    def test_cli_round_trip_and_invalid_json(self):
        profile_file = self.root / "out/profile.json"
        run_file = self.root / "out/run.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--config", str(ROOT / "intap.toml"), "profile", "--output", str(profile_file)]), 0)
            self.assertEqual(main(["--config", str(ROOT / "intap.toml"), "prepare", "--profile", str(profile_file), "--task", str(ROOT / "examples/task.json"), "--output", str(run_file)]), 0)
        self.assertEqual(json.loads(run_file.read_text())["task"]["task_id"], "DEMO-001")
        profile_file.write_text("[]")
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            code = main(["--config", str(ROOT / "intap.toml"), "prepare", "--profile", str(profile_file), "--task", str(ROOT / "examples/task.json"), "--output", str(run_file)])
        self.assertEqual(code, 1)
        self.assertIn("JSON object", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
