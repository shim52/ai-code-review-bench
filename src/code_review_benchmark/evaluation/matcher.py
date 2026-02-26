"""Heuristic pre-matching between findings and ground truth."""

from __future__ import annotations

from code_review_benchmark.models.challenge import GroundTruthIssue
from code_review_benchmark.models.evaluation import MatchResult
from code_review_benchmark.models.finding import NormalizedFinding


def heuristic_match(
    ground_truths: list[GroundTruthIssue],
    findings: list[NormalizedFinding],
    file_weight: float = 0.4,
    line_weight: float = 0.2,
    keyword_weight: float = 0.4,
) -> list[MatchResult]:
    """Score each ground truth against all findings using heuristic overlap.

    Returns one MatchResult per ground truth, linked to the best-matching finding.
    Enforces one-to-one assignment: each finding can match at most one ground truth.
    Uses greedy assignment by descending score.
    """
    # Compute all pairwise scores
    all_pairs: list[tuple[int, int, float]] = []  # (gt_idx, finding_idx, score)
    for gt_idx, gt in enumerate(ground_truths):
        for f_idx, finding in enumerate(findings):
            score = _score_pair(gt, finding, file_weight, line_weight, keyword_weight)
            if score > 0.0:
                all_pairs.append((gt_idx, f_idx, score))

    # Sort by score descending for greedy assignment
    all_pairs.sort(key=lambda x: x[2], reverse=True)

    # Greedy one-to-one assignment
    assigned_gts: set[int] = set()
    assigned_findings: set[int] = set()
    gt_assignments: dict[int, tuple[int, float]] = {}  # gt_idx -> (finding_idx, score)

    for gt_idx, f_idx, score in all_pairs:
        if gt_idx in assigned_gts or f_idx in assigned_findings:
            continue
        gt_assignments[gt_idx] = (f_idx, score)
        assigned_gts.add(gt_idx)
        assigned_findings.add(f_idx)

    # Build results for all ground truths
    results: list[MatchResult] = []
    for gt_idx, gt in enumerate(ground_truths):
        if gt_idx in gt_assignments:
            f_idx, score = gt_assignments[gt_idx]
            matched = score >= 0.3  # threshold for heuristic pre-match
            results.append(
                MatchResult(
                    ground_truth_id=gt.id,
                    finding_index=f_idx,
                    matched=matched,
                    match_score=round(score, 3),
                    match_method="heuristic",
                    explanation=f"heuristic score {score:.3f}",
                )
            )
        else:
            results.append(
                MatchResult(
                    ground_truth_id=gt.id,
                    finding_index=None,
                    matched=False,
                    match_score=0.0,
                    match_method="heuristic",
                    explanation="no match found",
                )
            )

    return results


def _score_pair(
    gt: GroundTruthIssue,
    finding: NormalizedFinding,
    file_w: float,
    line_w: float,
    keyword_w: float,
) -> float:
    file_score = _file_overlap(gt.file, finding.file)
    line_score = _line_overlap(gt.line_start, gt.line_end, finding.line_start, finding.line_end)
    keyword_score = _keyword_overlap(gt, finding)

    return file_w * file_score + line_w * line_score + keyword_w * keyword_score


def _file_overlap(gt_file: str, finding_file: str | None) -> float:
    if not finding_file:
        return 0.0
    # Normalize paths
    gt_parts = gt_file.replace("\\", "/").split("/")
    finding_parts = finding_file.replace("\\", "/").split("/")

    # Exact match
    if gt_parts == finding_parts:
        return 1.0

    # Filename match (last component)
    if gt_parts[-1] == finding_parts[-1]:
        return 0.8

    # Partial path overlap
    common = set(gt_parts) & set(finding_parts)
    if common:
        return 0.3 * len(common) / max(len(gt_parts), len(finding_parts))

    return 0.0


def _line_overlap(
    gt_start: int | None,
    gt_end: int | None,
    f_start: int | None,
    f_end: int | None,
) -> float:
    if gt_start is None or f_start is None:
        return 0.0

    gt_s = gt_start
    gt_e = gt_end or gt_start
    f_s = f_start
    f_e = f_end or f_start

    # Exact or overlapping range
    if f_s <= gt_e and f_e >= gt_s:
        return 1.0

    # Within 5 lines
    distance = min(abs(gt_s - f_e), abs(f_s - gt_e))
    if distance <= 5:
        return max(0.0, 1.0 - distance * 0.15)

    return 0.0


def _keyword_overlap(gt: GroundTruthIssue, finding: NormalizedFinding) -> float:
    if not gt.keywords:
        return 0.0

    search_text = (
        f"{finding.title} {finding.description} {finding.raw_text} {finding.category or ''}"
    ).lower()

    hits = sum(1 for kw in gt.keywords if kw.lower() in search_text)
    return hits / len(gt.keywords)
