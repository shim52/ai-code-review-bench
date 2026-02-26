"""LLM-as-judge for semantic matching between findings and ground truth.

Uses Claude Sonnet 4 by default — chosen because most benchmarked tools
use OpenAI models, so an Anthropic judge reduces same-provider scoring bias.
Configurable via CRB_JUDGE_MODEL (any Anthropic model name).
"""

from __future__ import annotations

import json
import os

from code_review_benchmark.models.challenge import GroundTruthIssue
from code_review_benchmark.models.evaluation import MatchResult
from code_review_benchmark.models.finding import NormalizedFinding

DEFAULT_JUDGE_MODEL = "claude-sonnet-4-20250514"

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


def _get_judge_model(model: str | None = None) -> str:
    """Resolve the judge model from argument, env var, or default."""
    if model:
        return model
    return os.environ.get("CRB_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)

# Bedrock model ID mapping (same as claude_reviewer.py)
_BEDROCK_MODEL_MAP = {
    "claude-sonnet-4-20250514": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "claude-opus-4-20250514": "us.anthropic.claude-opus-4-20250514-v1:0",
}


def _get_client():
    """Create the appropriate Anthropic client (direct API or Bedrock)."""
    import anthropic

    use_bedrock = os.environ.get("CRB_CLAUDE_USE_BEDROCK", "").lower() == "true"
    aws_profile = os.environ.get("AWS_PROFILE", "")

    if use_bedrock or (aws_profile and not os.environ.get("ANTHROPIC_API_KEY")):
        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        return anthropic.AnthropicBedrock(
            aws_region=region,
            aws_profile=aws_profile or None,
        ), True
    return anthropic.Anthropic(), False


def _call_judge(model: str, system_prompt: str, user_msg: str) -> dict:
    """Call the Anthropic API (direct or Bedrock) and return the parsed JSON response."""
    client, is_bedrock = _get_client()
    api_model = _BEDROCK_MODEL_MAP.get(model, model) if is_bedrock else model

    response = client.messages.create(
        model=api_model,
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
        temperature=0.0,
    )
    content = response.content[0].text
    return _extract_json(content)


def _extract_json(text: str) -> dict:
    """Extract JSON from text that may be wrapped in markdown code fences."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [ln for ln in lines[1:] if ln.strip() != "```"]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {
            "matched": False,
            "confidence": 0.0,
            "explanation": "Failed to parse judge response",
        }


def llm_judge_match(
    ground_truth: GroundTruthIssue,
    finding: NormalizedFinding,
    model: str | None = None,
) -> MatchResult:
    """Use an LLM to judge whether a finding matches a ground truth issue."""
    resolved_model = _get_judge_model(model)

    user_msg = _build_user_message(ground_truth, finding)
    result = _call_judge(resolved_model, _SYSTEM_PROMPT, user_msg)

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
- **Keywords**: {", ".join(gt.keywords)}

## Tool Finding
- **Tool**: {finding.tool}
- **File**: {finding.file} (lines {finding.line_start}-{finding.line_end or finding.line_start})
- **Severity**: {finding.severity.value if finding.severity else "N/A"}
- **Title**: {finding.title}
- **Description**: {finding.description}

Does this finding match the ground truth issue? Respond with JSON only."""
