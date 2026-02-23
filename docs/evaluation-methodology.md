# Evaluation Methodology

## Overview

The benchmark uses a two-phase evaluation pipeline to match tool findings against ground truth issues.

## Phase 1: Heuristic Pre-matching

Each ground truth issue is scored against all tool findings using weighted heuristics:

| Factor | Weight | Method |
|--------|--------|--------|
| File path overlap | 0.4 | Exact match (1.0), filename match (0.8), partial path (0.3) |
| Line proximity | 0.2 | Overlapping ranges (1.0), within 5 lines (decay), else 0 |
| Keyword overlap | 0.4 | Fraction of ground truth keywords found in finding text |

A threshold of 0.3 is used for pre-matching. Findings below 0.1 are excluded from LLM evaluation.

## Phase 2: LLM-as-Judge

For each ground truth with a heuristic candidate (score >= 0.1), an LLM evaluates semantic equivalence:

- The LLM receives the ground truth definition and the tool's finding
- It returns a match decision, confidence score, and explanation
- The final score combines heuristic (40%) and LLM (60%) scores

## Scoring

- **Precision**: True positives / total findings
- **Recall**: True positives / total ground truth issues
- **F1**: Harmonic mean of precision and recall

## Handling Non-determinism

Since LLM-based tools produce different outputs across runs:
- Each tool/challenge pair is run multiple times (default: 3)
- Mean and standard deviation are reported for all metrics
- The evaluation LLM uses temperature=0 for consistency

## Fair Comparison

- All tools are given the same model (configurable via `CRB_TOOL_MODEL`)
- All tools see the same repository state
- Tools run in isolation (fresh temp repo per run)
