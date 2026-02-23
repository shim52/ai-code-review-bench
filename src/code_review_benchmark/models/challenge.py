"""Challenge and ground truth models."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GroundTruthIssue(BaseModel):
    id: str
    severity: Severity
    category: str
    file: str
    line_start: int | None = None
    line_end: int | None = None
    title: str
    description: str = ""
    keywords: list[str] = Field(default_factory=list)


class PRInfo(BaseModel):
    title: str
    description: str = ""


class Challenge(BaseModel):
    id: str
    name: str
    description: str = ""
    language: str
    difficulty: Difficulty
    categories: list[str] = Field(default_factory=list)
    pr: PRInfo
    issues: list[GroundTruthIssue]

    # Set after loading — not in YAML
    base_path: Path | None = None

    @property
    def before_dir(self) -> Path:
        assert self.base_path is not None
        return self.base_path / "before"

    @property
    def after_dir(self) -> Path:
        assert self.base_path is not None
        return self.base_path / "after"

    @classmethod
    def from_yaml(cls, path: Path) -> Challenge:
        with open(path) as f:
            data = yaml.safe_load(f)
        challenge = cls.model_validate(data)
        challenge.base_path = path.parent
        return challenge


def load_challenges(challenges_dir: Path, ids: list[str] | None = None) -> list[Challenge]:
    """Load challenges from a directory. Optionally filter by id list."""
    challenges: list[Challenge] = []
    for child in sorted(challenges_dir.iterdir()):
        if child.name.startswith("_") or not child.is_dir():
            continue
        yaml_path = child / "challenge.yaml"
        if not yaml_path.exists():
            continue
        if ids and child.name not in ids:
            continue
        challenges.append(Challenge.from_yaml(yaml_path))
    return challenges
