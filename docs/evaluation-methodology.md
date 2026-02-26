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

> **Note on judge model**: The default judge model is Claude Sonnet 4 (`claude-sonnet-4-20250514`). We chose an Anthropic model because the majority of benchmarked tools use OpenAI models — using an independent judge provider reduces same-provider scoring bias. The judge model is configurable via `CRB_JUDGE_MODEL`. We plan to add a calibration dataset with manually labeled matches to validate judge accuracy in a future release.

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

1. **Judge model bias**: The LLM judge defaults to Claude Sonnet 4 (`claude-sonnet-4-20250514`), chosen because most benchmarked tools use OpenAI models. This reduces but does not eliminate potential scoring bias. Configurable via `CRB_JUDGE_MODEL`.
2. **Heuristic thresholds**: The 0.3 pre-match and 0.1 skip thresholds are hand-tuned. A calibration dataset would allow data-driven threshold selection.
3. **Single best candidate**: The LLM judge evaluates only the best heuristic match per ground truth. If the heuristic selects the wrong finding, a better candidate is never evaluated.
4. **Language coverage**: Current challenges are primarily TypeScript. Tool performance may differ across languages.
