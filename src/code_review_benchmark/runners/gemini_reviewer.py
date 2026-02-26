"""Gemini code reviewer — uses Google Gemini models via the google-genai SDK."""

from __future__ import annotations

import os

from code_review_benchmark.runners.llm_reviewer_base import AbstractLLMReviewer
from code_review_benchmark.runners.registry import register_tool

DEFAULT_MODEL = "gemini-2.5-pro"


@register_tool
class GeminiReviewerRunner(AbstractLLMReviewer):
    @property
    def name(self) -> str:
        return "gemini-reviewer"

    @property
    def version_command(self) -> list[str]:
        return ["python3", "-c", "import google.genai; print(google.genai.__version__)"]

    def is_available(self) -> bool:
        try:
            import google.genai  # noqa: F401
        except ImportError:
            return False
        return bool(os.environ.get("GOOGLE_API_KEY", ""))

    def _resolve_model(self, model: str | None) -> str:
        """Determine which Gemini model to use."""
        env_model = os.environ.get("CRB_GEMINI_MODEL")
        if env_model:
            return env_model
        if model and ("gemini" in model.lower() or "google" in model.lower()):
            return model
        return DEFAULT_MODEL

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        timeout: int,
    ) -> str:
        from google import genai

        client = genai.Client()
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text or ""
