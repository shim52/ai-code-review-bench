"""Parse Claude Reviewer output into normalized findings."""

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
}


class ClaudeReviewerParser(AbstractOutputParser):
    @property
    def tool_name(self) -> str:
        return "claude-reviewer"

    def parse(self, result: RunResult) -> list[NormalizedFinding]:
        if not result.output_text:
            return []

        findings: list[NormalizedFinding] = []
        text = result.output_text

        # Split on "### Finding N" headers.
        finding_blocks = re.split(r"###\s+Finding\s+\d+", text)

        for block in finding_blocks[1:]:  # skip text before first finding
            finding = self._parse_finding_block(block)
            if finding:
                findings.append(finding)

        # Fallback: if structured parsing found nothing, try freetext.
        if not findings:
            findings = self._parse_freetext(text)

        return findings

    def _parse_finding_block(self, block: str) -> NormalizedFinding | None:
        file_match = re.search(r"\*\*File\*\*:\s*`?([^`\n]+?)`?\s*$", block, re.MULTILINE)
        lines_match = re.search(r"\*\*Lines?\*\*:\s*(\d+)(?:\s*-\s*(\d+))?", block)
        severity_match = re.search(r"\*\*Severity\*\*:\s*(\w+)", block)
        category_match = re.search(r"\*\*Category\*\*:\s*([^\n]+)", block)
        title_match = re.search(r"\*\*Title\*\*:\s*([^\n]+)", block)
        desc_match = re.search(r"\*\*Description\*\*:\s*(.+)", block, re.DOTALL)

        file_path = file_match.group(1).strip() if file_match else None
        line_start = int(lines_match.group(1)) if lines_match else None
        line_end = int(lines_match.group(2)) if lines_match and lines_match.group(2) else None
        severity_text = severity_match.group(1).lower().strip() if severity_match else None
        severity = _SEVERITY_MAP.get(severity_text) if severity_text else None
        category = category_match.group(1).strip() if category_match else None
        title = title_match.group(1).strip() if title_match else block.strip()[:120]
        description = desc_match.group(1).strip() if desc_match else block.strip()

        if not title and not description:
            return None

        return NormalizedFinding(
            tool="claude-reviewer",
            file=file_path,
            line_start=line_start,
            line_end=line_end,
            severity=severity,
            category=category,
            title=title[:120],
            description=description,
            raw_text=block.strip(),
        )

    def _parse_freetext(self, text: str) -> list[NormalizedFinding]:
        """Fallback parser for unstructured Claude output."""
        findings: list[NormalizedFinding] = []
        sections = re.split(r"\n(?=[-*] |#{1,4} )", text)
        for section in sections:
            section = section.strip()
            if not section or len(section) < 20:
                continue
            if "no issues found" in section.lower():
                continue

            file_match = re.search(r"`?([^\s`]+\.\w{1,5})`?(?::(\d+))?", section)
            file_path = file_match.group(1) if file_match else None
            line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None

            findings.append(
                NormalizedFinding(
                    tool="claude-reviewer",
                    file=file_path,
                    line_start=line_start,
                    severity=_infer_severity(section),
                    title=section.split("\n")[0][:120].lstrip("- *#"),
                    description=section,
                    raw_text=section,
                )
            )
        return findings


def _infer_severity(text: str) -> Severity | None:
    text_lower = text.lower()
    for keyword in ("critical", "injection", "vulnerability", "exploit"):
        if keyword in text_lower:
            return Severity.CRITICAL
    for keyword in ("security", "bug", "error", "race condition"):
        if keyword in text_lower:
            return Severity.HIGH
    for keyword in ("performance", "memory", "leak"):
        if keyword in text_lower:
            return Severity.MEDIUM
    for keyword in ("suggestion", "style", "nitpick"):
        if keyword in text_lower:
            return Severity.LOW
    return None
