"""Aggregate scores across challenges and runs into a BenchmarkReport."""

from __future__ import annotations

import statistics
from datetime import datetime, timezone

from code_review_benchmark.models.evaluation import (
    BenchmarkReport,
    ChallengeToolResult,
    ToolScore,
)


def aggregate_results(
    results: list[ChallengeToolResult],
    judge_model: str = "",
    tool_model: str = "",
    num_runs: int = 1,
) -> BenchmarkReport:
    """Aggregate per-challenge per-tool results into a BenchmarkReport."""
    # Group by tool
    by_tool: dict[str, list[ChallengeToolResult]] = {}
    all_challenges: set[str] = set()
    for r in results:
        by_tool.setdefault(r.tool, []).append(r)
        all_challenges.add(r.challenge_id)

    tool_scores: list[ToolScore] = []
    for tool_name, tool_results in sorted(by_tool.items()):
        # Group by challenge to compute per-challenge stats
        by_challenge: dict[str, list[ChallengeToolResult]] = {}
        for r in tool_results:
            by_challenge.setdefault(r.challenge_id, []).append(r)

        precisions: list[float] = []
        recalls: list[float] = []
        f1s: list[float] = []
        total_findings = 0
        total_matched = 0
        total_gt = 0

        for challenge_runs in by_challenge.values():
            # Average across runs for this challenge
            avg_p = statistics.mean(r.precision for r in challenge_runs)
            avg_r = statistics.mean(r.recall for r in challenge_runs)
            avg_f1 = statistics.mean(r.f1 for r in challenge_runs)
            precisions.append(avg_p)
            recalls.append(avg_r)
            f1s.append(avg_f1)

            for r in challenge_runs:
                total_findings += r.findings
                total_matched += sum(1 for m in r.matches if m.matched)
                total_gt += len(r.matches)

        tool_scores.append(
            ToolScore(
                tool=tool_name,
                challenges_run=len(by_challenge),
                total_ground_truths=total_gt,
                total_findings=total_findings,
                total_matched=total_matched,
                mean_precision=round(statistics.mean(precisions), 4) if precisions else 0.0,
                mean_recall=round(statistics.mean(recalls), 4) if recalls else 0.0,
                mean_f1=round(statistics.mean(f1s), 4) if f1s else 0.0,
                stddev_precision=(
                    round(statistics.stdev(precisions), 4) if len(precisions) > 1 else 0.0
                ),
                stddev_recall=(
                    round(statistics.stdev(recalls), 4) if len(recalls) > 1 else 0.0
                ),
                stddev_f1=(
                    round(statistics.stdev(f1s), 4) if len(f1s) > 1 else 0.0
                ),
                per_challenge=tool_results,
            )
        )

    return BenchmarkReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        judge_model=judge_model,
        tool_model=tool_model,
        num_runs=num_runs,
        challenges=sorted(all_challenges),
        tools=tool_scores,
    )
