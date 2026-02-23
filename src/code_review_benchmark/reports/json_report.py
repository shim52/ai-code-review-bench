"""Generate machine-readable JSON reports."""

from __future__ import annotations

import json
from typing import Dict, Any, List

from code_review_benchmark.models.evaluation import BenchmarkReport


def generate_json_report(report: BenchmarkReport) -> str:
    """Serialize a BenchmarkReport to formatted JSON."""
    return json.dumps(report.model_dump(), indent=2)


def generate_dashboard_json(
    report: BenchmarkReport,
    challenges: List[Dict[str, Any]] | None = None,
    tools_metadata: List[Dict[str, Any]] | None = None,
) -> str:
    """Generate JSON in the dashboard format with breakdown metrics.

    Args:
        report: The benchmark report with results
        challenges: Optional list of challenge metadata
        tools_metadata: Optional list of tool metadata

    Returns:
        JSON string in dashboard format
    """
    dashboard_data = {
        "metadata": {
            "timestamp": report.timestamp,
            "benchmark_version": "1.1.0",  # Updated for breakdown support
            "total_runs": report.num_runs,
            "llm_judge_model": report.judge_model,
            "challenges_count": len(report.challenges),
            "tools_count": len(report.tools)
        },
        "tools": tools_metadata or [],
        "challenges": challenges or [],
        "results": [],
        "overall_scores": [],
        "metrics_breakdown": None
    }

    # Add per-challenge results
    for tool_score in report.tools:
        # Overall score for this tool
        overall = {
            "tool": tool_score.tool,
            "metrics": {
                "avg_precision": tool_score.mean_precision,
                "avg_recall": tool_score.mean_recall,
                "avg_f1_score": tool_score.mean_f1,
                "total_true_positives": tool_score.total_matched,
                "total_false_positives": tool_score.total_findings - tool_score.total_matched,
                "total_false_negatives": tool_score.total_ground_truths - tool_score.total_matched,
            }
        }

        # Add breakdown if available
        if tool_score.metrics_breakdown:
            overall["metrics"]["breakdown"] = {
                "by_category": [
                    {
                        "name": cat.name,
                        "precision": cat.precision,
                        "recall": cat.recall,
                        "f1_score": cat.f1,
                        "challenges": cat.challenges_count
                    }
                    for cat in tool_score.metrics_breakdown.by_category
                ],
                "by_severity": [
                    {
                        "name": sev.name,
                        "precision": sev.precision,
                        "recall": sev.recall,
                        "f1_score": sev.f1,
                        "issues": sev.total_ground_truths
                    }
                    for sev in tool_score.metrics_breakdown.by_severity
                ],
                "by_language": [
                    {
                        "name": lang.name,
                        "precision": lang.precision,
                        "recall": lang.recall,
                        "f1_score": lang.f1,
                        "challenges": lang.challenges_count
                    }
                    for lang in tool_score.metrics_breakdown.by_language
                ]
            }

        dashboard_data["overall_scores"].append(overall)

        # Add per-challenge results
        for challenge_result in tool_score.per_challenge:
            dashboard_data["results"].append({
                "tool": tool_score.tool,
                "challenge": challenge_result.challenge_id,
                "metrics": {
                    "precision": challenge_result.precision,
                    "recall": challenge_result.recall,
                    "f1_score": challenge_result.f1,
                    "true_positives": sum(1 for m in challenge_result.matches if m.matched),
                    "false_positives": challenge_result.findings - sum(1 for m in challenge_result.matches if m.matched),
                    "false_negatives": len(challenge_result.matches) - sum(1 for m in challenge_result.matches if m.matched),
                }
            })

    # Add overall breakdown across all tools
    if report.metrics_breakdown:
        dashboard_data["metrics_breakdown"] = {
            "by_category": [
                {
                    "name": cat.name,
                    "total_issues": cat.total_ground_truths,
                    "total_found": cat.total_matched,
                    "precision": cat.precision,
                    "recall": cat.recall,
                    "f1_score": cat.f1,
                    "challenges": cat.challenges_count
                }
                for cat in report.metrics_breakdown.by_category
            ],
            "by_severity": [
                {
                    "name": sev.name,
                    "total_issues": sev.total_ground_truths,
                    "total_found": sev.total_matched,
                    "precision": sev.precision,
                    "recall": sev.recall,
                    "f1_score": sev.f1
                }
                for sev in report.metrics_breakdown.by_severity
            ],
            "by_language": [
                {
                    "name": lang.name,
                    "total_issues": lang.total_ground_truths,
                    "total_found": lang.total_matched,
                    "precision": lang.precision,
                    "recall": lang.recall,
                    "f1_score": lang.f1,
                    "challenges": lang.challenges_count
                }
                for lang in report.metrics_breakdown.by_language
            ]
        }

    return json.dumps(dashboard_data, indent=2)
