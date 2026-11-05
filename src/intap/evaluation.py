"""A release-policy skeleton; supplied reports are not authenticated evidence."""

from dataclasses import dataclass

from intap.agent import VerificationReport


@dataclass(frozen=True)
class GateDecision:
    status: str
    failures: tuple[str, ...]


def evaluate_verification(report: VerificationReport) -> GateDecision:
    checks = {
        "tests_missing": type(report.tests_run) is int and report.tests_run > 0,
        "tests_failed": report.tests_passed is True,
        "lint_failed": report.lint_passed is True,
        "acceptance_failed": report.acceptance_passed is True,
        "security_failed": report.security_passed is True,
    }
    failures = tuple(key for key, passed in checks.items() if not passed)
    return GateDecision("blocked" if failures else "human_review_required", failures)
