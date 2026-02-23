"""Parse PR-Agent review output into normalized findings."""

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
    "security": Severity.HIGH,
    "performance": Severity.MEDIUM,
}


class PRAgentParser(AbstractOutputParser):
    @property
    def tool_name(self) -> str:
        return "pr-agent"

    def parse(self, result: RunResult) -> list[NormalizedFinding]:
        if not result.output_text:
            return []

        findings: list[NormalizedFinding] = []
        text = result.output_text

        # PR-Agent outputs markdown with tables and code suggestions.
        # Parse table rows: | severity | file:line | description |
        table_pattern = re.compile(r"\|[^|]*\|[^|]*\|[^|]*\|", re.MULTILINE)
        rows = table_pattern.findall(text)
        for row in rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if len(cells) < 3:
                continue
            # Skip header rows
            if cells[0].startswith("---") or cells[0].lower() in ("severity", "type", "category"):
                continue
            finding = self._parse_table_row(cells)
            if finding:
                findings.append(finding)

        # Also parse code suggestion blocks
        suggestion_pattern = re.compile(r"### Suggestion\s*\n(.*?)(?=### |$)", re.DOTALL)
        for match in suggestion_pattern.finditer(text):
            finding = self._parse_suggestion_block(match.group(1))
            if finding:
                findings.append(finding)

        # Fallback: if no structured output found, parse free-text sections
        if not findings:
            findings = self._parse_freetext(text)

        return findings

    def _parse_table_row(self, cells: list[str]) -> NormalizedFinding | None:
        severity_text = cells[0].lower().strip()
        severity = _SEVERITY_MAP.get(severity_text)

        file_ref = cells[1] if len(cells) > 1 else ""
        description = cells[2] if len(cells) > 2 else ""

        file_path, line_start, line_end = _parse_file_ref(file_ref)

        return NormalizedFinding(
            tool="pr-agent",
            file=file_path,
            line_start=line_start,
            line_end=line_end,
            severity=severity,
            title=description[:120],
            description=description,
            raw_text=" | ".join(cells),
        )

    def _parse_suggestion_block(self, block: str) -> NormalizedFinding | None:
        lines = block.strip().split("\n")
        if not lines:
            return None

        file_path = None
        line_start = None
        description_parts: list[str] = []

        for line in lines:
            file_match = re.search(r"`([^`]+\.\w+)`", line)
            if file_match and not file_path:
                file_path = file_match.group(1)
            line_match = re.search(r"[Ll]ines?\s*(\d+)", line)
            if line_match and line_start is None:
                line_start = int(line_match.group(1))
            description_parts.append(line)

        description = "\n".join(description_parts)
        return NormalizedFinding(
            tool="pr-agent",
            file=file_path,
            line_start=line_start,
            title=description.split("\n")[0][:120],
            description=description,
            raw_text=block,
        )

    def _parse_freetext(self, text: str) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []
        # Split on markdown headers or bullet points
        sections = re.split(r"\n(?=[-*] |#{1,4} )", text)
        for section in sections:
            section = section.strip()
            if not section or len(section) < 20:
                continue
            file_match = re.search(r"`?([^\s`]+\.\w{1,4})`?(?::(\d+))?", section)
            file_path = file_match.group(1) if file_match else None
            line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None

            findings.append(
                NormalizedFinding(
                    tool="pr-agent",
                    file=file_path,
                    line_start=line_start,
                    title=section.split("\n")[0][:120],
                    description=section,
                    raw_text=section,
                )
            )
        return findings


def _parse_file_ref(ref: str) -> tuple[str | None, int | None, int | None]:
    """Parse 'path/to/file.ts:12-15' or 'path/to/file.ts [12]' style refs."""
    ref = ref.strip().strip("`")
    match = re.match(r"(.+?)(?::(\d+)(?:-(\d+))?|\s*\[(\d+)(?:-(\d+))?\])?$", ref)
    if not match:
        return None, None, None

    file_path = match.group(1).strip()
    line_start = int(match.group(2) or match.group(4) or 0) or None
    line_end = int(match.group(3) or match.group(5) or 0) or None
    return file_path, line_start, line_end
