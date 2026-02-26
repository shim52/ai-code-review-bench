#!/usr/bin/env python3
"""Update dashboard data from latest benchmark results.

Transforms the evaluator's report.json into the benchmark-results.json
format expected by the docs/site UI.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

# ── Tool metadata (enriched info not in report.json) ──

TOOL_METADATA: Dict[str, Dict[str, Any]] = {
    "pr-agent": {
        "display_name": "PR-Agent",
        "github_url": "https://github.com/qodo-ai/pr-agent",
        "stars": 10254,
        "license": "AGPL-3.0",
        "install_cmd": "pip install 'git+https://github.com/qodo-ai/pr-agent.git@main'",
        "description": (
            "AI-powered code review and suggestions by Qodo,"
            " using LLMs to analyze pull requests"
        ),
        "llm_model": "gpt-5.2-2025-12-11 (default)",
        "tool_type": "agent",
    },
    "shippie": {
        "display_name": "Shippie",
        "github_url": "https://github.com/mattzcarey/shippie",
        "stars": 2333,
        "license": "MIT",
        "install_cmd": "npm install -g shippie",
        "description": "Open-source, extensible AI code review agent with local and CI support",
        "llm_model": "gpt-4.1-mini (default)",
        "tool_type": "agent",
    },
    "claude-reviewer": {
        "display_name": "Claude Reviewer",
        "github_url": "https://docs.anthropic.com/en/docs/about-claude/models",
        "stars": 0,
        "license": "Proprietary",
        "install_cmd": "pip install anthropic",
        "description": (
            "General-purpose Claude Opus model prompted to do code review"
            " via API — not a dedicated code review agent"
        ),
        "llm_model": "claude-opus-4-20250514",
        "tool_type": "pure_model",
    },
    "openai-reviewer": {
        "display_name": "OpenAI Reviewer",
        "github_url": "https://platform.openai.com/docs/models",
        "stars": 0,
        "license": "Proprietary",
        "install_cmd": "pip install openai",
        "description": (
            "General-purpose GPT-4o model prompted to do code review"
            " via API — not a dedicated code review agent"
        ),
        "llm_model": "gpt-4o",
        "tool_type": "pure_model",
    },
    "gemini-reviewer": {
        "display_name": "Gemini Reviewer",
        "github_url": "https://ai.google.dev/gemini-api/docs",
        "stars": 0,
        "license": "Proprietary",
        "install_cmd": "pip install google-genai",
        "description": (
            "General-purpose Gemini Pro model prompted to do code review"
            " via API — not a dedicated code review agent"
        ),
        "llm_model": "gemini-2.5-pro",
        "tool_type": "pure_model",
    },
}

# The shared system prompt used by pure model baselines
SYSTEM_PROMPT = (
    "You are an expert code reviewer. You will receive a git diff representing "
    "changes in a pull request. Analyze the diff carefully and identify all issues, "
    "bugs, security vulnerabilities, performance problems, and other concerns.\n\n"
    "For each finding, output it in this exact format:\n\n"
    "### Finding N\n"
    "- **File**: <file path>\n"
    "- **Lines**: <start_line>-<end_line> (or just <line> if single line)\n"
    "- **Severity**: <critical|high|medium|low|info>\n"
    "- **Category**: <security|bug|performance|error-handling|type-safety|style|other>\n"
    "- **Title**: <short title>\n"
    "- **Description**: <detailed explanation of the issue and why it matters>\n\n"
    "Focus on:\n"
    "- Security vulnerabilities (injection, XSS, CSRF, etc.)\n"
    "- Bugs and logic errors\n"
    "- Missing error handling\n"
    "- Performance issues (N+1 queries, memory leaks, etc.)\n"
    "- Race conditions\n"
    "- Type safety issues\n"
    "- Information disclosure\n\n"
    "Do NOT report:\n"
    "- Style preferences or formatting\n"
    "- Missing documentation (unless it hides a real issue)\n"
    "- Minor naming suggestions\n\n"
    "If there are no significant issues, output:\n### No Issues Found"
)


def load_challenge_metadata(challenges_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load challenge metadata from YAML files."""
    challenges = {}
    for challenge_dir in sorted(challenges_dir.iterdir()):
        yaml_path = challenge_dir / "challenge.yaml"
        if not yaml_path.exists():
            continue
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        challenges[data["id"]] = {
            "id": data["id"],
            "name": data["name"],
            "category": data.get("categories", ["General"])[0].title(),
            "difficulty": data.get("difficulty", "Medium").title(),
            "ground_truth_issues": len(data.get("issues", [])),
            "description": data.get("description", ""),
            "language": data.get("language", "Unknown"),
        }
    return challenges


def tool_display_name(tool_id: str) -> str:
    """Convert tool slug to display name, using metadata if available."""
    meta = TOOL_METADATA.get(tool_id)
    return meta["display_name"] if meta else tool_id


def transform_report(
    report: Dict[str, Any],
    challenges_meta: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Transform evaluator report.json into the UI's benchmark-results.json format."""

    # ── Metadata ──
    challenge_ids = report.get("challenges", [])
    tool_entries = report.get("tools", [])

    metadata = {
        "timestamp": report.get("timestamp", ""),
        "benchmark_version": "1.0.0",
        "total_runs": report.get("num_runs", 1),
        "evaluation_method": (
            "heuristic"
            if "heuristic" in report.get("judge_model", "")
            else "heuristic+llm_judge"
        ),
        "challenges_count": len(challenge_ids),
        "tools_count": len(tool_entries),
        "llm_note": "Each tool ran with its default LLM model",
        "llm_judge_model": report.get("judge_model", ""),
    }

    # ── Tools (metadata) ──
    tools: List[Dict[str, Any]] = []
    for t in tool_entries:
        tool_id = t["tool"]
        meta = TOOL_METADATA.get(tool_id, {})
        tools.append({
            "name": tool_display_name(tool_id),
            "version": meta.get("llm_model", "latest"),
            "github_url": meta.get("github_url", ""),
            "stars": meta.get("stars", 0),
            "license": meta.get("license", "Unknown"),
            "install_cmd": meta.get("install_cmd", ""),
            "description": meta.get("description", f"AI code review tool: {tool_id}"),
            "llm_model": meta.get("llm_model", ""),
            "tool_type": meta.get("tool_type", "agent"),
        })

    # ── Challenges (metadata) ──
    challenges: List[Dict[str, Any]] = []
    for cid in challenge_ids:
        if cid in challenges_meta:
            challenges.append(challenges_meta[cid])
        else:
            challenges.append({
                "id": cid,
                "name": cid.replace("-", " ").title(),
                "category": "General",
                "difficulty": "Medium",
                "ground_truth_issues": 0,
                "description": "",
            })

    # ── Results (flat per-tool-per-challenge) ──
    # Report has tools[].per_challenge[] with multiple runs per challenge.
    # UI expects one result per tool × challenge, averaged across runs.
    results: List[Dict[str, Any]] = []
    overall_scores: List[Dict[str, Any]] = []

    for t in tool_entries:
        tool_id = t["tool"]
        display = tool_display_name(tool_id)
        per_challenge = t.get("per_challenge", [])

        # Group per_challenge entries by challenge_id (may have multiple runs)
        by_challenge: Dict[str, List[Dict[str, Any]]] = {}
        for pc in per_challenge:
            cid = pc["challenge_id"]
            by_challenge.setdefault(cid, []).append(pc)

        total_tp = 0
        total_fp = 0
        total_fn = 0

        for cid, runs in sorted(by_challenge.items()):
            # Average metrics across runs
            avg_precision = sum(r["precision"] for r in runs) / len(runs)
            avg_recall = sum(r["recall"] for r in runs) / len(runs)
            avg_f1 = sum(r["f1"] for r in runs) / len(runs)

            # Sum counts across runs, then average
            total_findings = sum(r["findings"] for r in runs) / len(runs)
            matched_per_run = [
                sum(1 for m in r["matches"] if m["matched"])
                for r in runs
            ]
            gt_per_run = [len(r["matches"]) for r in runs]
            avg_tp = sum(matched_per_run) / len(runs)
            avg_gt = sum(gt_per_run) / len(runs)
            avg_fp = total_findings - avg_tp
            avg_fn = avg_gt - avg_tp

            tp = round(avg_tp)
            fp = round(avg_fp)
            fn = round(avg_fn)

            total_tp += tp
            total_fp += fp
            total_fn += fn

            # Per-run F1 scores for the "run consistency" display
            run_scores = [{"f1_score": r["f1"]} for r in runs]

            results.append({
                "tool": display,
                "challenge": cid,
                "metrics": {
                    "precision": round(avg_precision, 4),
                    "recall": round(avg_recall, 4),
                    "f1_score": round(avg_f1, 4),
                    "true_positives": tp,
                    "false_positives": fp,
                    "false_negatives": fn,
                    "runs": run_scores if len(runs) > 1 else None,
                },
            })

        overall_scores.append({
            "tool": display,
            "metrics": {
                "avg_precision": t["mean_precision"],
                "avg_recall": t["mean_recall"],
                "avg_f1_score": t["mean_f1"],
                "total_true_positives": total_tp,
                "total_false_positives": total_fp,
                "total_false_negatives": total_fn,
            },
        })

    return {
        "metadata": metadata,
        "system_prompt": SYSTEM_PROMPT,
        "tools": tools,
        "challenges": challenges,
        "results": results,
        "overall_scores": overall_scores,
    }


def update_dashboard_data():
    """Update the dashboard's benchmark-results.json with latest data."""
    project_root = Path(__file__).resolve().parents[1]

    latest_report_path = project_root / "results" / "latest" / "report.json"
    dashboard_path = project_root / "docs" / "site" / "data" / "benchmark-results.json"
    challenges_dir = project_root / "challenges"

    if not latest_report_path.exists():
        print("No latest report found, skipping dashboard update")
        return

    # Load report
    with open(latest_report_path) as f:
        report = json.load(f)

    # Load challenge metadata from YAML files
    challenges_meta = load_challenge_metadata(challenges_dir)

    # Transform
    dashboard = transform_report(report, challenges_meta)

    # Save
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dashboard_path, "w") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)

    print(f"Dashboard data updated: {dashboard_path}")
    print(f"  Tools: {dashboard['metadata']['tools_count']}")
    print(f"  Challenges: {dashboard['metadata']['challenges_count']}")
    print(f"  Results: {len(dashboard['results'])} entries")


if __name__ == "__main__":
    update_dashboard_data()
