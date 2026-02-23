"""Precision, recall, and F1 calculation."""

from __future__ import annotations

from code_review_benchmark.models.evaluation import ChallengeToolResult, MatchResult


def score_challenge_run(
    challenge_id: str,
    tool: str,
    run_index: int,
    num_findings: int,
    match_results: list[MatchResult],
) -> ChallengeToolResult:
    """Calculate precision, recall, F1 for a single challenge/tool/run."""
    true_positives = sum(1 for m in match_results if m.matched)
    total_ground_truths = len(match_results)

    recall = true_positives / total_ground_truths if total_ground_truths > 0 else 0.0

    # Precision: of the findings the tool produced, how many matched a ground truth?
    # A finding can match at most one ground truth.
    precision = true_positives / num_findings if num_findings > 0 else 0.0

    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return ChallengeToolResult(
        challenge_id=challenge_id,
        tool=tool,
        run_index=run_index,
        findings=num_findings,
        matches=match_results,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
    )
