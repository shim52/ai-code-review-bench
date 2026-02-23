"""Parse Shippie review output into normalized findings."""

from __future__ import annotations

import re

from code_review_benchmark.models.challenge import Severity
from code_review_benchmark.models.finding import NormalizedFinding
from code_review_benchmark.parsers.base import AbstractOutputParser
from code_review_benchmark.runners.base import RunResult

_SEVERITY_KEYWORDS: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "security": Severity.HIGH,
    "bug": Severity.HIGH,
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "performance": Severity.MEDIUM,
    "suggestion": Severity.LOW,
    "style": Severity.INFO,
    "nitpick": Severity.INFO,
    "nit": Severity.INFO,
}


class ShippieParser(AbstractOutputParser):
    @property
    def tool_name(self) -> str:
        return "shippie"

    def parse(self, result: RunResult) -> list[NormalizedFinding]:
        if not result.output_text:
            return []

        findings: list[NormalizedFinding] = []
        text = result.output_text

        # Shippie outputs markdown with file-level sections and inline comments.
        # Pattern: ### `file.ts` or ## file.ts
        file_sections = re.split(r"\n#{2,3}\s+`?([^`\n]+\.\w{1,5})`?", text)

        # file_sections alternates: [preamble, filename, content, filename, content, ...]
        i = 1
        while i < len(file_sections) - 1:
            file_path = file_sections[i].strip()
            section_text = file_sections[i + 1]
            findings.extend(self._parse_file_section(file_path, section_text))
            i += 2

        # Also parse any top-level bullet points (general findings)
        if file_sections:
            preamble = file_sections[0]
            findings.extend(self._parse_bullets(preamble))

        return findings

    def _parse_file_section(
        self, file_path: str, section: str
    ) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []

        # Parse line references: "Line 12:", "Lines 12-15:", or "[L12]"
        comments = re.split(r"\n(?=[-*] |\d+\. )", section)
        for comment in comments:
            comment = comment.strip()
            if not comment or len(comment) < 10:
                continue

            line_match = re.search(
                r"[Ll]ines?\s*(\d+)(?:\s*-\s*(\d+))?", comment
            )
            line_start = int(line_match.group(1)) if line_match else None
            line_end = int(line_match.group(2)) if line_match and line_match.group(2) else None

            severity = _infer_severity(comment)

            findings.append(
                NormalizedFinding(
                    tool="shippie",
                    file=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    severity=severity,
                    title=comment.split("\n")[0][:120].lstrip("- *"),
                    description=comment,
                    raw_text=comment,
                )
            )

        return findings

    def _parse_bullets(self, text: str) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []
        for match in re.finditer(r"[-*]\s+(.+?)(?=\n[-*]|\n\n|$)", text, re.DOTALL):
            bullet = match.group(1).strip()
            if len(bullet) < 15:
                continue

            file_match = re.search(r"`([^`]+\.\w{1,5})`(?::(\d+))?", bullet)
            file_path = file_match.group(1) if file_match else None
            line_start = int(file_match.group(2)) if file_match and file_match.group(2) else None

            findings.append(
                NormalizedFinding(
                    tool="shippie",
                    file=file_path,
                    line_start=line_start,
                    severity=_infer_severity(bullet),
                    title=bullet.split("\n")[0][:120],
                    description=bullet,
                    raw_text=bullet,
                )
            )
        return findings


def _infer_severity(text: str) -> Severity | None:
    text_lower = text.lower()
    for keyword, severity in _SEVERITY_KEYWORDS.items():
        if keyword in text_lower:
            return severity
    return None
