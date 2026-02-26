#!/usr/bin/env python3
"""Process benchmark results to maintain historical data."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Maximum number of historical entries to keep
MAX_HISTORY_ENTRIES = 52  # One year of weekly runs


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load JSON file safely."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def extract_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from a benchmark report."""
    metrics = {}

    # Extract overall scores
    if 'overall_scores' in report:
        for tool_score in report['overall_scores']:
            tool_name = tool_score['tool']
            metrics[tool_name] = {
                'f1_score': tool_score['metrics']['avg_f1_score'],
                'precision': tool_score['metrics']['avg_precision'],
                'recall': tool_score['metrics']['avg_recall'],
                'response_time_ms': tool_score['metrics']['avg_response_time_ms'],
                'success_rate': tool_score['metrics'].get('success_rate', 1.0)
            }

    return metrics


def process_historical_data():
    """Process latest benchmark results and update historical data."""
    project_root = Path(__file__).resolve().parents[1]

    # Paths
    latest_report = project_root / 'results' / 'latest' / 'report.json'
    historical_file = project_root / 'docs' / 'data' / 'historical.json'

    if not latest_report.exists():
        print("No latest report found, skipping historical processing")
        return

    # Load latest report
    report = load_json_file(latest_report)

    # Load existing historical data
    historical = load_json_file(historical_file)
    if 'entries' not in historical:
        historical['entries'] = []

    # Create new entry
    timestamp = datetime.now(timezone.utc).isoformat()
    new_entry = {
        'timestamp': timestamp,
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'metrics': extract_metrics(report),
        'metadata': {
            'benchmark_version': report.get('metadata', {}).get('benchmark_version', '1.0.0'),
            'num_runs': report.get('metadata', {}).get('num_runs', 3),
            'challenges_count': len(report.get('challenges', [])),
            'tools_count': len(report.get('overall_scores', []))
        }
    }

    # Add to historical data
    historical['entries'].append(new_entry)

    # Keep only the most recent entries
    if len(historical['entries']) > MAX_HISTORY_ENTRIES:
        historical['entries'] = historical['entries'][-MAX_HISTORY_ENTRIES:]

    # Calculate trends (last 4 weeks)
    if len(historical['entries']) >= 2:
        historical['trends'] = calculate_trends(historical['entries'][-4:])

    # Update metadata
    historical['metadata'] = {
        'last_updated': timestamp,
        'total_runs': len(historical['entries']),
        'oldest_run': historical['entries'][0]['timestamp'] if historical['entries'] else None,
        'newest_run': timestamp
    }

    # Save historical data
    save_json_file(historical_file, historical)
    print(f"Historical data updated with {len(historical['entries'])} entries")


def calculate_trends(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate performance trends from historical entries."""
    if len(entries) < 2:
        return {}

    trends = {}
    tools = set()

    # Get all tool names
    for entry in entries:
        tools.update(entry['metrics'].keys())

    # Calculate trends for each tool
    for tool in tools:
        tool_data = []
        for entry in entries:
            if tool in entry['metrics']:
                tool_data.append(entry['metrics'][tool])

        if len(tool_data) >= 2:
            first = tool_data[0]
            last = tool_data[-1]

            trends[tool] = {
                'f1_score_change': last['f1_score'] - first['f1_score'],
                'precision_change': last['precision'] - first['precision'],
                'recall_change': last['recall'] - first['recall'],
                'response_time_change': last['response_time_ms'] - first['response_time_ms'],
                'direction': 'improving' if last['f1_score'] > first['f1_score'] else 'declining'
            }

    return trends


if __name__ == '__main__':
    process_historical_data()
