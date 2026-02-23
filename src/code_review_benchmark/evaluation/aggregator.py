"""Aggregate scores across challenges and runs into a BenchmarkReport."""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from code_review_benchmark.models.challenge import Challenge
from code_review_benchmark.models.evaluation import (
    BenchmarkReport,
    CategoryMetrics,
    ChallengeToolResult,
    MetricsBreakdown,
    ToolScore,
)


def compute_group_metrics(
    results: List[ChallengeToolResult],
) -> Tuple[float, float, float, int, int, int]:
    """Compute aggregated metrics for a group of results.

    Returns:
        (precision, recall, f1, total_findings, total_matched, total_gt)
    """
    if not results:
        return 0.0, 0.0, 0.0, 0, 0, 0

    total_findings = sum(r.findings for r in results)
    total_matched = sum(sum(1 for m in r.matches if m.matched) for r in results)
    total_gt = sum(len(r.matches) for r in results)

    # Calculate weighted averages based on ground truths
    weighted_precision = 0.0
    weighted_recall = 0.0
    total_weight = 0

    for r in results:
        weight = len(r.matches)
        if weight > 0:
            weighted_precision += r.precision * weight
            weighted_recall += r.recall * weight
            total_weight += weight

    if total_weight > 0:
        precision = weighted_precision / total_weight
        recall = weighted_recall / total_weight
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    else:
        precision = recall = f1 = 0.0

    return (
        round(precision, 4),
        round(recall, 4),
        round(f1, 4),
        total_findings,
        total_matched,
        total_gt,
    )


def compute_tool_breakdown(
    tool_results: List[ChallengeToolResult], challenges_map: Dict[str, Challenge]
) -> MetricsBreakdown:
    """Compute metrics breakdown by category, severity, and language for a tool."""

    # Group by category
    by_category: Dict[str, List[ChallengeToolResult]] = {}
    by_severity: Dict[str, List[ChallengeToolResult]] = {}
    by_language: Dict[str, List[ChallengeToolResult]] = {}

    for result in tool_results:
        challenge = challenges_map.get(result.challenge_id)
        if not challenge:
            continue

        # Group by categories (a challenge can have multiple)
        for category in challenge.categories:
            by_category.setdefault(category, []).append(result)

        # Group by severities from ground truth issues
        for issue in challenge.issues:
            severity = issue.severity.value
            by_severity.setdefault(severity, []).append(result)

        # Group by language
        by_language.setdefault(challenge.language, []).append(result)

    # Compute metrics for each category
    category_metrics = []
    for cat_name, cat_results in sorted(by_category.items()):
        p, r, f1, findings, matched, gt = compute_group_metrics(cat_results)
        category_metrics.append(
            CategoryMetrics(
                name=cat_name,
                total_ground_truths=gt,
                total_findings=findings,
                total_matched=matched,
                precision=p,
                recall=r,
                f1=f1,
                challenges_count=len(set(r.challenge_id for r in cat_results)),
            )
        )

    # Compute metrics for each severity
    severity_metrics = []
    severity_order = ["critical", "high", "medium", "low", "info"]
    for sev in severity_order:
        if sev in by_severity:
            sev_results = by_severity[sev]
            p, r, f1, findings, matched, gt = compute_group_metrics(sev_results)
            severity_metrics.append(
                CategoryMetrics(
                    name=sev,
                    total_ground_truths=gt,
                    total_findings=findings,
                    total_matched=matched,
                    precision=p,
                    recall=r,
                    f1=f1,
                    challenges_count=len(set(r.challenge_id for r in sev_results)),
                )
            )

    # Compute metrics for each language
    language_metrics = []
    for lang_name, lang_results in sorted(by_language.items()):
        p, r, f1, findings, matched, gt = compute_group_metrics(lang_results)
        language_metrics.append(
            CategoryMetrics(
                name=lang_name,
                total_ground_truths=gt,
                total_findings=findings,
                total_matched=matched,
                precision=p,
                recall=r,
                f1=f1,
                challenges_count=len(set(r.challenge_id for r in lang_results)),
            )
        )

    return MetricsBreakdown(
        by_category=category_metrics, by_severity=severity_metrics, by_language=language_metrics
    )


def aggregate_results(
    results: list[ChallengeToolResult],
    judge_model: str = "",
    tool_model: str = "",
    num_runs: int = 1,
    challenges: list[Challenge] | None = None,
    compute_breakdown: bool = True,
) -> BenchmarkReport:
    """Aggregate per-challenge per-tool results into a BenchmarkReport.

    Args:
        results: List of challenge tool results
        judge_model: Model used for judging
        tool_model: Model used by the tool
        num_runs: Number of runs performed
        challenges: Optional list of Challenge objects for computing breakdowns
        compute_breakdown: Whether to compute metrics breakdown by category/severity/language
    """
    # Group by tool
    by_tool: dict[str, list[ChallengeToolResult]] = {}
    all_challenges: set[str] = set()
    for r in results:
        by_tool.setdefault(r.tool, []).append(r)
        all_challenges.add(r.challenge_id)

    # Create challenge map if challenges provided
    challenges_map: Dict[str, Challenge] = {}
    if challenges and compute_breakdown:
        challenges_map = {c.id: c for c in challenges}

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

        # Compute breakdown if challenges provided
        tool_breakdown = None
        if challenges_map and compute_breakdown:
            tool_breakdown = compute_tool_breakdown(tool_results, challenges_map)

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
                stddev_recall=(round(statistics.stdev(recalls), 4) if len(recalls) > 1 else 0.0),
                stddev_f1=(round(statistics.stdev(f1s), 4) if len(f1s) > 1 else 0.0),
                per_challenge=tool_results,
                metrics_breakdown=tool_breakdown,
            )
        )

    # Compute overall breakdown across all tools
    overall_breakdown = None
    if challenges_map and compute_breakdown:
        overall_breakdown = compute_tool_breakdown(results, challenges_map)

    return BenchmarkReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        judge_model=judge_model,
        tool_model=tool_model,
        num_runs=num_runs,
        challenges=sorted(all_challenges),
        tools=tool_scores,
        metrics_breakdown=overall_breakdown,
    )
