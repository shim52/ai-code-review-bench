"""Generate markdown comparison reports."""

from __future__ import annotations

from code_review_benchmark.models.evaluation import BenchmarkReport


def generate_markdown_report(report: BenchmarkReport) -> str:
    """Generate a markdown comparison table from a BenchmarkReport."""
    lines: list[str] = []

    lines.append("# Code Review Benchmark Results")
    lines.append("")
    lines.append(f"**Date**: {report.timestamp}")
    if report.judge_model:
        lines.append(f"**Judge Model**: {report.judge_model}")
    if report.tool_model:
        lines.append(f"**Tool Model**: {report.tool_model}")
    lines.append(f"**Runs per pair**: {report.num_runs}")
    lines.append(f"**Challenges**: {len(report.challenges)}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Tool | Precision | Recall | F1 | Findings | Matched |")
    lines.append("|------|-----------|--------|-----|----------|---------|")

    for tool in sorted(report.tools, key=lambda t: t.mean_f1, reverse=True):
        p = f"{tool.mean_precision:.2%} (+/-{tool.stddev_precision:.2%})"
        r = f"{tool.mean_recall:.2%} (+/-{tool.stddev_recall:.2%})"
        f1 = f"{tool.mean_f1:.2%} (+/-{tool.stddev_f1:.2%})"
        lines.append(
            f"| {tool.tool} | {p} | {r} | {f1} | "
            f"{tool.total_findings} | {tool.total_matched}/{tool.total_ground_truths} |"
        )

    lines.append("")

    # Per-challenge breakdown
    lines.append("## Per-Challenge Breakdown")
    lines.append("")

    for challenge_id in sorted(report.challenges):
        lines.append(f"### {challenge_id}")
        lines.append("")
        lines.append("| Tool | Run | Findings | Precision | Recall | F1 |")
        lines.append("|------|-----|----------|-----------|--------|-----|")

        for tool in report.tools:
            for result in tool.per_challenge:
                if result.challenge_id != challenge_id:
                    continue
                lines.append(
                    f"| {result.tool} | {result.run_index} | {result.findings} | "
                    f"{result.precision:.2%} | {result.recall:.2%} | {result.f1:.2%} |"
                )

                # Show match details
                for m in result.matches:
                    status = "FOUND" if m.matched else "MISSED"
                    lines.append(
                        f"|  |  | {status}: {m.ground_truth_id} "
                        f"(score={m.match_score:.2f}, {m.match_method}) | | | |"
                    )

        lines.append("")

    return "\n".join(lines)
