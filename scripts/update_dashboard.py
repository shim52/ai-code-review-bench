#!/usr/bin/env python3
"""Update dashboard data from latest benchmark results."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file safely."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None


def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to JSON file with proper formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def format_challenge_for_dashboard(challenge: Dict[str, Any]) -> Dict[str, Any]:
    """Format challenge data for dashboard display."""
    return {
        'id': challenge['id'],
        'name': challenge['name'],
        'category': challenge.get('category', 'General'),
        'difficulty': challenge.get('difficulty', 'Medium'),
        'ground_truth_issues': challenge.get('ground_truth_issues', 0),
        'description': challenge.get('description', ''),
        'language': challenge.get('language', 'Unknown')
    }


def format_tool_for_dashboard(tool_name: str, overall_score: Dict[str, Any]) -> Dict[str, Any]:
    """Format tool data for dashboard display."""
    # Default tool info (will be enriched if available)
    tool_info = {
        'name': tool_name,
        'version': 'latest',
        'github_url': '',
        'stars': 0,
        'license': 'Unknown',
        'install_cmd': '',
        'description': f'AI code review tool: {tool_name}'
    }

    # Try to get tool metadata from known tools
    known_tools = {
        'PR-Agent': {
            'github_url': 'https://github.com/qodo-ai/pr-agent',
            'stars': 10300,
            'license': 'AGPL-3.0',
            'install_cmd': 'pip install pr-agent',
            'description': 'AI-powered code review assistant with comprehensive analysis capabilities'
        },
        'Shippie': {
            'github_url': 'https://github.com/mattzcarey/shippie',
            'stars': 2300,
            'license': 'MIT',
            'install_cmd': 'npx shippie',
            'description': 'Fast and lightweight AI reviewer focused on catching common issues'
        },
        'AI Review': {
            'github_url': 'https://github.com/Nikita-Filonov/ai-review',
            'stars': 269,
            'license': 'Apache-2.0',
            'install_cmd': 'pip install xai-review',
            'description': 'Extensible AI code review framework with custom rule support'
        },
        'Claude Reviewer': {
            'github_url': 'https://docs.anthropic.com/en/docs/about-claude/models',
            'stars': 0,
            'license': 'Proprietary',
            'install_cmd': 'pip install anthropic',
            'description': 'General-purpose Claude model (Opus) used as a code reviewer via API'
        }
    }

    if tool_name in known_tools:
        tool_info.update(known_tools[tool_name])

    return tool_info


def update_dashboard_data():
    """Update the dashboard's benchmark-results.json with latest data."""
    project_root = Path(__file__).resolve().parents[1]

    # Paths
    latest_report = project_root / 'results' / 'latest' / 'report.json'
    dashboard_data = project_root / 'docs' / 'site' / 'data' / 'benchmark-results.json'
    historical_data = project_root / 'docs' / 'site' / 'data' / 'historical.json'

    if not latest_report.exists():
        print("No latest report found, skipping dashboard update")
        return

    # Load latest report
    report = load_json_file(latest_report)
    if not report:
        print("Failed to load latest report")
        return

    # Load historical data for trends
    historical = load_json_file(historical_data) or {'entries': [], 'trends': {}}

    # Prepare dashboard data
    dashboard = {
        'metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            'benchmark_version': report.get('metadata', {}).get('benchmark_version', '1.0.0'),
            'total_runs': report.get('metadata', {}).get('num_runs', 3),
            'llm_judge_model': report.get('metadata', {}).get('llm_judge_model', 'gpt-4o'),
            'challenges_count': len(report.get('challenges', [])),
            'tools_count': len(report.get('overall_scores', [])),
            'historical_runs': len(historical.get('entries', []))
        },
        'tools': [],
        'challenges': [],
        'overall_scores': [],
        'challenge_results': {},
        'trends': historical.get('trends', {}),
        'recent_history': []
    }

    # Format tools
    for score in report.get('overall_scores', []):
        tool_name = score['tool']
        dashboard['tools'].append(format_tool_for_dashboard(tool_name, score))

    # Format challenges
    for challenge in report.get('challenges', []):
        dashboard['challenges'].append(format_challenge_for_dashboard(challenge))

    # Copy overall scores with enhanced metrics
    dashboard['overall_scores'] = report.get('overall_scores', [])

    # Copy challenge results (detailed per-challenge scores)
    dashboard['challenge_results'] = report.get('challenge_results', {})

    # Add recent history (last 8 weeks for chart display)
    if historical.get('entries'):
        recent_entries = historical['entries'][-8:]
        dashboard['recent_history'] = [
            {
                'date': entry['date'],
                'timestamp': entry['timestamp'],
                'metrics': entry['metrics']
            }
            for entry in recent_entries
        ]

    # Calculate additional statistics
    if dashboard['overall_scores']:
        best_f1 = max(s['metrics']['avg_f1_score'] for s in dashboard['overall_scores'])
        best_tool = next(s['tool'] for s in dashboard['overall_scores']
                         if s['metrics']['avg_f1_score'] == best_f1)

        dashboard['metadata']['best_performer'] = {
            'tool': best_tool,
            'f1_score': best_f1,
            'improvement': dashboard['trends'].get(best_tool, {}).get('f1_score_change', 0)
        }

    # Save updated dashboard data
    save_json_file(dashboard_data, dashboard)
    print(f"Dashboard data updated at {dashboard['metadata']['last_updated']}")
    print(f"  - Tools: {dashboard['metadata']['tools_count']}")
    print(f"  - Challenges: {dashboard['metadata']['challenges_count']}")
    print(f"  - Historical runs: {dashboard['metadata']['historical_runs']}")


if __name__ == '__main__':
    update_dashboard_data()