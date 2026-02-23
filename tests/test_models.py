"""Tests for Pydantic models."""

from pathlib import Path

from code_review_benchmark.models.challenge import Challenge, Difficulty, Severity


def test_challenge_from_yaml(tmp_path: Path):
    yaml_content = """\
id: test-challenge
name: Test Challenge
description: A test
language: python
difficulty: easy
categories: [bug]
pr:
  title: Fix bug
  description: Fixes a bug
issues:
  - id: test-issue
    severity: high
    category: bug
    file: src/main.py
    line_start: 10
    line_end: 15
    title: Test issue
    keywords: [test, bug]
"""
    yaml_path = tmp_path / "challenge.yaml"
    yaml_path.write_text(yaml_content)

    ch = Challenge.from_yaml(yaml_path)
    assert ch.id == "test-challenge"
    assert ch.difficulty == Difficulty.EASY
    assert len(ch.issues) == 1
    assert ch.issues[0].severity == Severity.HIGH
    assert ch.base_path == tmp_path


def test_challenge_before_after_dirs(tmp_path: Path):
    (tmp_path / "before").mkdir()
    (tmp_path / "after").mkdir()
    yaml_content = """\
id: test
name: Test
language: python
difficulty: medium
categories: []
pr:
  title: Test PR
issues: []
"""
    yaml_path = tmp_path / "challenge.yaml"
    yaml_path.write_text(yaml_content)

    ch = Challenge.from_yaml(yaml_path)
    assert ch.before_dir == tmp_path / "before"
    assert ch.after_dir == tmp_path / "after"
