"""Parse Claude Reviewer output into normalized findings."""

from __future__ import annotations

from code_review_benchmark.parsers.llm_reviewer import LLMReviewerParser


class ClaudeReviewerParser(LLMReviewerParser):
    def __init__(self) -> None:
        super().__init__(tool_name="claude-reviewer")
