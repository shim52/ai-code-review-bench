"""Tests for heuristic matcher."""

from code_review_benchmark.evaluation.matcher import heuristic_match
from code_review_benchmark.models.challenge import GroundTruthIssue, Severity
from code_review_benchmark.models.finding import NormalizedFinding


def test_exact_file_and_keyword_match():
    gt = [
        GroundTruthIssue(
            id="test-1",
            severity=Severity.HIGH,
            category="security",
            file="src/routes/users.ts",
            line_start=12,
            title="SQL injection",
            keywords=["sql injection", "parameterized"],
        )
    ]
    findings = [
        NormalizedFinding(
            tool="test",
            file="src/routes/users.ts",
            line_start=12,
            title="SQL injection vulnerability found",
            description="Use parameterized queries instead",
        )
    ]

    results = heuristic_match(gt, findings)
    assert len(results) == 1
    assert results[0].matched is True
    assert results[0].match_score > 0.5


def test_no_match():
    gt = [
        GroundTruthIssue(
            id="test-1",
            severity=Severity.HIGH,
            category="security",
            file="src/auth.ts",
            line_start=50,
            title="Missing auth check",
            keywords=["authentication", "authorization"],
        )
    ]
    findings = [
        NormalizedFinding(
            tool="test",
            file="src/utils/format.ts",
            line_start=5,
            title="Use const instead of let",
            description="Variable is never reassigned",
        )
    ]

    results = heuristic_match(gt, findings)
    assert len(results) == 1
    assert results[0].matched is False
