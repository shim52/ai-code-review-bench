"""Tests for challenge repo builder."""

from pathlib import Path

from git import Repo

from code_review_benchmark.challenge_repo.builder import build_challenge_repo
from code_review_benchmark.models.challenge import Challenge


def test_build_challenge_repo(tmp_path: Path):
    # Create a minimal challenge
    before_dir = tmp_path / "before"
    before_dir.mkdir()
    (before_dir / "hello.txt").write_text("hello before")

    after_dir = tmp_path / "after"
    after_dir.mkdir()
    (after_dir / "hello.txt").write_text("hello after")

    yaml_content = """\
id: test
name: Test
language: python
difficulty: easy
categories: []
pr:
  title: Test PR
issues: []
"""
    (tmp_path / "challenge.yaml").write_text(yaml_content)
    challenge = Challenge.from_yaml(tmp_path / "challenge.yaml")

    repo = build_challenge_repo(challenge)
    try:
        assert repo.path.exists()
        assert (repo.path / ".git").exists()

        git_repo = Repo(repo.path)

        # Check branches exist
        branches = [b.name for b in git_repo.branches]
        assert "main" in branches
        assert "challenge" in branches

        # Check challenge branch has the "after" content
        git_repo.git.checkout("challenge")
        content = (repo.path / "hello.txt").read_text()
        assert content == "hello after"

        # Check main has the "before" content
        git_repo.git.checkout("main")
        content = (repo.path / "hello.txt").read_text()
        assert content == "hello before"
    finally:
        repo.cleanup()
