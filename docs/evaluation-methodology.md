# Evaluation Methodology

## Overview

The benchmark uses a two-phase evaluation pipeline to match tool findings against ground truth issues. Results are aggregated per-challenge to ensure fair weighting regardless of how many issues a challenge contains.

## Phase 1: Heuristic Pre-matching

Each ground truth issue is scored against all tool findings using weighted heuristics:

| Factor | Weight | Method |
|--------|--------|--------|
| File path overlap | 0.4 | Exact match (1.0), filename match (0.8), partial path (0.3) |
| Line proximity | 0.2 | Overlapping ranges (1.0), within 5 lines (decay), else 0 |
| Keyword overlap | 0.4 | Fraction of ground truth keywords found in finding text |

**One-to-one matching**: Ground truths and findings are assigned using greedy one-to-one matching by descending score. Each finding can match at most one ground truth issue — this prevents inflated precision when a tool produces a single finding that covers multiple ground truth issues.

A threshold of 0.3 is used for pre-matching. Findings below 0.1 are excluded from LLM evaluation.

## Phase 2: LLM-as-Judge

For each ground truth with a heuristic candidate (score >= 0.1), an LLM evaluates semantic equivalence:

- The LLM receives the ground truth definition and the tool's finding (including file, line range, severity, and description)
- It returns a match decision, confidence score, and explanation
- The final score combines heuristic (40%) and LLM (60%) scores

> **Note on judge model**: The default judge model is GPT-4o (`gpt-4o`). When evaluating tools that also use OpenAI models, this creates a potential same-provider bias — the judge may be more generous toward outputs phrased in a similar style. We recommend using `CRB_JUDGE_MODEL` to configure an alternative provider (e.g., Claude, Gemini) for cross-provider fairness. We plan to add a calibration dataset with manually labeled matches to validate judge accuracy in a future release.

## Scoring

- **Precision**: True positives / total findings produced by the tool
- **Recall**: True positives / total ground truth issues
- **F1**: Harmonic mean of precision and recall

Per-challenge scores are averaged first, then the mean across challenges is reported. This ensures challenges with many ground truth issues don't dominate the overall score.

## Handling Non-determinism

Since LLM-based tools produce different outputs across runs:
- Each tool/challenge pair is run multiple times (default: 3)
- Mean and standard deviation are reported for all metrics
- The evaluation LLM uses temperature=0 for consistency

## Fair Comparison

- All tools are given the same model (configurable via `CRB_TOOL_MODEL`)
- All tools see the same repository state
- Tools run in isolation (fresh temp repo per run)

## Known Limitations

1. **Judge model bias**: The LLM judge defaults to GPT-4o, which may introduce same-provider scoring bias for OpenAI-based review tools (see note above).
2. **Heuristic thresholds**: The 0.3 pre-match and 0.1 skip thresholds are hand-tuned. A calibration dataset would allow data-driven threshold selection.
3. **Single best candidate**: The LLM judge evaluates only the best heuristic match per ground truth. If the heuristic selects the wrong finding, a better candidate is never evaluated.
4. **Language coverage**: Current challenges are primarily TypeScript. Tool performance may differ across languages.
