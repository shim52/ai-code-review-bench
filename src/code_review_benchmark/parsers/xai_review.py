"""Parse xai-review (AI Review) output into normalized findings."""

from __future__ import annotations

import json
import re

from code_review_benchmark.models.challenge import Severity
from code_review_benchmark.models.finding import NormalizedFinding
from code_review_benchmark.parsers.base import AbstractOutputParser
from code_review_benchmark.runners.base import RunResult

_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "major": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "moderate": Severity.MEDIUM,
    "low": Severity.LOW,
    "minor": Severity.LOW,
    "info": Severity.INFO,
    "informational": Severity.INFO,
}


class XAIReviewParser(AbstractOutputParser):
    @property
    def tool_name(self) -> str:
        return "xai-review"

    def parse(self, result: RunResult) -> list[NormalizedFinding]:
        if not result.output_text:
            return []

        text = result.output_text.strip()

        # Try JSON first (xai-review may output structured JSON)
        findings = self._try_parse_json(text)
        if findings:
            return findings

        # Fallback to markdown/text parsing
        return self._parse_markdown(text)

    def _try_parse_json(self, text: str) -> list[NormalizedFinding]:
        # Look for JSON array or object in the output
        for match in re.finditer(r"(\[[\s\S]*?\]|\{[\s\S]*?\})", text):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    return [self._json_to_finding(item) for item in data if isinstance(item, dict)]
                if isinstance(data, dict) and "comments" in data:
                    return [
                        self._json_to_finding(c) for c in data["comments"] if isinstance(c, dict)
                    ]
                if isinstance(data, dict) and "findings" in data:
                    return [
                        self._json_to_finding(f) for f in data["findings"] if isinstance(f, dict)
                    ]
            except (json.JSONDecodeError, KeyError):
                continue
        return []

    def _json_to_finding(self, item: dict) -> NormalizedFinding:
        severity_str = str(item.get("severity", item.get("level", ""))).lower()
        severity = _SEVERITY_MAP.get(severity_str)

        file_path = item.get("file", item.get("path", item.get("filename")))
        line_start = item.get("line", item.get("line_start", item.get("startLine")))
        line_end = item.get("line_end", item.get("endLine"))

        title = item.get("title", item.get("message", item.get("summary", "")))
        description = item.get("description", item.get("body", item.get("detail", "")))
        category = item.get("category", item.get("type", ""))

        return NormalizedFinding(
            tool="xai-review",
            file=file_path,
            line_start=int(line_start) if line_start else None,
            line_end=int(line_end) if line_end else None,
            severity=severity,
            category=category,
            title=str(title)[:120],
            description=str(description) if description else str(title),
            raw_text=json.dumps(item, indent=2),
        )

    def _parse_markdown(self, text: str) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []

        # Split on markdown headers or numbered items
        sections = re.split(r"\n(?=#{1,4} |\d+\.\s)", text)
        for section in sections:
            section = section.strip()
            if not section or len(section) < 15:
                continue

            file_match = re.search(r"`?([^\s`]+\.\w{1,5})`?(?::(\d+)(?:-(\d+))?)?", section)
            file_path = file_match.group(1) if file_match else None
            line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None
            line_end = int(file_match.group(3)) if file_match and file_match.group(3) else None

            severity = None
            for keyword, sev in _SEVERITY_MAP.items():
                if keyword in section.lower():
                    severity = sev
                    break

            first_line = section.split("\n")[0].lstrip("# 0123456789.")

            findings.append(
                NormalizedFinding(
                    tool="xai-review",
                    file=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    severity=severity,
                    title=first_line[:120],
                    description=section,
                    raw_text=section,
                )
            )

        return findings
