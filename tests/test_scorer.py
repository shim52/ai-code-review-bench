"""Tests for scorer."""

from code_review_benchmark.evaluation.scorer import score_challenge_run
from code_review_benchmark.models.evaluation import MatchResult


def test_perfect_score():
    matches = [
        MatchResult(ground_truth_id="a", matched=True, match_score=1.0),
        MatchResult(ground_truth_id="b", matched=True, match_score=0.8),
    ]
    result = score_challenge_run("test", "tool", 0, 2, matches)
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0


def test_partial_recall():
    matches = [
        MatchResult(ground_truth_id="a", matched=True, match_score=1.0),
        MatchResult(ground_truth_id="b", matched=False, match_score=0.1),
    ]
    result = score_challenge_run("test", "tool", 0, 1, matches)
    assert result.recall == 0.5
    assert result.precision == 1.0


def test_zero_findings():
    matches = [
        MatchResult(ground_truth_id="a", matched=False, match_score=0.0),
    ]
    result = score_challenge_run("test", "tool", 0, 0, matches)
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.f1 == 0.0
