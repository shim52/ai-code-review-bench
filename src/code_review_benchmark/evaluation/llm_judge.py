"""LLM-as-judge for semantic matching between findings and ground truth."""

from __future__ import annotations

import json
import os

from openai import OpenAI

from code_review_benchmark.models.challenge import GroundTruthIssue
from code_review_benchmark.models.evaluation import MatchResult
from code_review_benchmark.models.finding import NormalizedFinding

_SYSTEM_PROMPT = """\
You are a code review evaluation judge. Given a ground truth issue that should \
be found in a code review and a finding produced by an automated review tool, \
determine whether the finding addresses the same issue as the ground truth.

Respond with a JSON object:
{
  "matched": true/false,
  "confidence": 0.0-1.0,
  "explanation": "brief reason"
}

Be generous: the finding doesn't need to use the exact same words. If the core \
issue (same file, same class of problem) is identified, that counts as a match. \
Minor differences in line numbers or wording are acceptable.
"""


def llm_judge_match(
    ground_truth: GroundTruthIssue,
    finding: NormalizedFinding,
    model: str | None = None,
) -> MatchResult:
    """Use an LLM to judge whether a finding matches a ground truth issue."""
    model = model or os.environ.get("CRB_JUDGE_MODEL", "gpt-4o")
    client = OpenAI()

    user_msg = _build_user_message(ground_truth, finding)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    result = json.loads(content)

    return MatchResult(
        ground_truth_id=ground_truth.id,
        matched=result.get("matched", False),
        match_score=result.get("confidence", 0.0),
        match_method="llm_judge",
        explanation=result.get("explanation", ""),
    )


def llm_judge_batch(
    ground_truths: list[GroundTruthIssue],
    findings: list[NormalizedFinding],
    heuristic_results: list[MatchResult],
    model: str | None = None,
) -> list[MatchResult]:
    """Run LLM judge on findings that heuristic pre-matched (or nearly matched).

    For each ground truth, the LLM judges the best heuristic-matched finding.
    If the heuristic found no match at all (score < 0.1), skip the LLM call.
    """
    results: list[MatchResult] = []

    for gt, heuristic in zip(ground_truths, heuristic_results):
        if heuristic.finding_index is None or heuristic.match_score < 0.1:
            # No plausible match — mark as unmatched
            results.append(
                MatchResult(
                    ground_truth_id=gt.id,
                    matched=False,
                    match_score=0.0,
                    match_method="llm_judge",
                    explanation="No heuristic candidate to judge",
                )
            )
            continue

        finding = findings[heuristic.finding_index]
        llm_result = llm_judge_match(gt, finding, model=model)
        llm_result.finding_index = heuristic.finding_index

        # Combine heuristic and LLM scores
        combined_score = 0.4 * heuristic.match_score + 0.6 * llm_result.match_score
        llm_result.match_score = round(combined_score, 3)
        llm_result.match_method = "heuristic+llm_judge"

        results.append(llm_result)

    return results


def _build_user_message(gt: GroundTruthIssue, finding: NormalizedFinding) -> str:
    return f"""\
## Ground Truth Issue
- **ID**: {gt.id}
- **Title**: {gt.title}
- **File**: {gt.file} (lines {gt.line_start}-{gt.line_end})
- **Severity**: {gt.severity.value}
- **Category**: {gt.category}
- **Description**: {gt.description}
- **Keywords**: {', '.join(gt.keywords)}

## Tool Finding
- **Tool**: {finding.tool}
- **File**: {finding.file} (line {finding.line_start})
- **Severity**: {finding.severity.value if finding.severity else 'N/A'}
- **Title**: {finding.title}
- **Description**: {finding.description}

Does this finding match the ground truth issue?"""
