"""Parse CodeRabbit review output into normalized findings."""

from __future__ import annotations

import re

from code_review_benchmark.models.challenge import Severity
from code_review_benchmark.models.finding import NormalizedFinding
from code_review_benchmark.parsers.base import AbstractOutputParser
from code_review_benchmark.runners.base import RunResult

_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
    "suggestion": Severity.LOW,
    "bug": Severity.HIGH,
    "security": Severity.CRITICAL,
    "performance": Severity.MEDIUM,
    "style": Severity.INFO,
    "warning": Severity.MEDIUM,
    "error": Severity.HIGH,
}


class CodeRabbitParser(AbstractOutputParser):
    @property
    def tool_name(self) -> str:
        return "coderabbit"

    def parse(self, result: RunResult) -> list[NormalizedFinding]:
        if not result.output_text:
            return []

        findings: list[NormalizedFinding] = []
        text = result.output_text

        # Parse Issues Found section
        issues_section = self._extract_section(text, "Issues Found")
        if issues_section:
            findings.extend(self._parse_issues_section(issues_section))

        # Parse Line-by-Line Review section
        line_review_section = self._extract_section(text, "Line-by-Line Review")
        if line_review_section:
            findings.extend(self._parse_line_review_section(line_review_section))

        # Parse Suggestions section
        suggestions_section = self._extract_section(text, "Suggestions")
        if suggestions_section:
            findings.extend(self._parse_suggestions_section(suggestions_section))

        # Fallback: parse any markdown list items that look like findings
        if not findings:
            findings = self._parse_markdown_lists(text)

        return findings

    def _extract_section(self, text: str, section_name: str) -> str | None:
        """Extract a markdown section by its header."""
        pattern = re.compile(
            rf"##\s*{re.escape(section_name)}\s*\n(.*?)(?=\n##\s|\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(text)
        return match.group(1).strip() if match else None

    def _parse_issues_section(self, section: str) -> list[NormalizedFinding]:
        """Parse the Issues Found section."""
        findings: list[NormalizedFinding] = []

        # Parse bullet points or numbered lists
        items = re.findall(r"^[\-\*\d+\.]?\s*(.+)$", section, re.MULTILINE)

        for item in items:
            item = item.strip()
            if not item or len(item) < 10:
                continue

            # Extract file path
            file_match = re.search(r"`?([^\s`]+\.\w{1,4})`?(?::(\d+)(?:-(\d+))?)?", item)
            file_path = file_match.group(1) if file_match else None
            line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None
            line_end = int(file_match.group(3)) if file_match and file_match.group(3) else None

            # Extract severity
            severity = None
            for sev_key, sev_value in _SEVERITY_MAP.items():
                if sev_key in item.lower():
                    severity = sev_value
                    break

            findings.append(
                NormalizedFinding(
                    tool="coderabbit",
                    file=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    severity=severity,
                    title=item[:120] if len(item) > 120 else item,
                    description=item,
                    raw_text=item,
                )
            )

        return findings

    def _parse_line_review_section(self, section: str) -> list[NormalizedFinding]:
        """Parse the Line-by-Line Review section."""
        findings: list[NormalizedFinding] = []

        # Split by file blocks (### File: path/to/file.ext)
        file_blocks = re.split(r"###\s*(?:File:|`)?\s*([^\n]+)", section)

        # Process pairs of (file_path, content)
        for i in range(1, len(file_blocks), 2):
            if i + 1 >= len(file_blocks):
                break

            file_path = file_blocks[i].strip().strip("`")
            content = file_blocks[i + 1]

            # Parse line-specific findings
            line_findings = re.findall(
                r"(?:Line|L)\s*(\d+)(?:-(\d+))?:?\s*(.+?)(?=(?:Line|L)\s*\d+|$)",
                content,
                re.DOTALL,
            )

            for line_match in line_findings:
                line_start = int(line_match[0]) if line_match[0] else None
                line_end = int(line_match[1]) if line_match[1] else line_start
                description = line_match[2].strip()

                # Extract severity from description
                severity = None
                for sev_key, sev_value in _SEVERITY_MAP.items():
                    if sev_key in description.lower():
                        severity = sev_value
                        break

                findings.append(
                    NormalizedFinding(
                        tool="coderabbit",
                        file=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        severity=severity,
                        title=description.split("\n")[0][:120],
                        description=description,
                        raw_text=f"Line {line_start}: {description}",
                    )
                )

        return findings

    def _parse_suggestions_section(self, section: str) -> list[NormalizedFinding]:
        """Parse the Suggestions section."""
        findings: list[NormalizedFinding] = []

        # Split suggestions by bullet points or numbers
        suggestions = re.split(r"\n(?=[\-\*\d+\.]?\s)", section)

        for suggestion in suggestions:
            suggestion = suggestion.strip()
            if not suggestion or len(suggestion) < 10:
                continue

            # Extract file reference
            file_match = re.search(r"`?([^\s`]+\.\w{1,4})`?(?::(\d+))?", suggestion)
            file_path = file_match.group(1) if file_match else None
            line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None

            findings.append(
                NormalizedFinding(
                    tool="coderabbit",
                    file=file_path,
                    line_start=line_start,
                    severity=Severity.LOW,  # Suggestions are typically low severity
                    title=suggestion.split("\n")[0][:120],
                    description=suggestion,
                    raw_text=suggestion,
                )
            )

        return findings

    def _parse_markdown_lists(self, text: str) -> list[NormalizedFinding]:
        """Fallback parser for markdown list items."""
        findings: list[NormalizedFinding] = []

        # Find all list items
        list_items = re.findall(r"^[\-\*]\s+(.+?)(?=\n[\-\*]|\n\n|\Z)", text, re.MULTILINE | re.DOTALL)

        for item in list_items:
            item = item.strip()
            if not item or len(item) < 20:
                continue

            # Check if it looks like a code review finding
            if any(keyword in item.lower() for keyword in ["issue", "bug", "error", "problem", "fix", "should", "consider"]):
                file_match = re.search(r"`?([^\s`]+\.\w{1,4})`?(?::(\d+))?", item)
                file_path = file_match.group(1) if file_match else None
                line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None

                findings.append(
                    NormalizedFinding(
                        tool="coderabbit",
                        file=file_path,
                        line_start=line_start,
                        title=item.split("\n")[0][:120],
                        description=item,
                        raw_text=item,
                    )
                )

        return findings