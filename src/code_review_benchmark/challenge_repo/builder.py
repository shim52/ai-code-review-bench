"""Build temporary git repos from before/after challenge fixtures."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from git import Repo

from code_review_benchmark.models.challenge import Challenge


class ChallengeRepo:
    """A temporary git repository built from a challenge's before/after dirs."""

    def __init__(self, repo_path: Path, repo: Repo, challenge: Challenge):
        self.path = repo_path
        self.repo = repo
        self.challenge = challenge
        self.main_branch = "main"
        self.pr_branch = "challenge"

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


def build_challenge_repo(challenge: Challenge, base_tmp: Path | None = None) -> ChallengeRepo:
    """Create a temp git repo: main branch has 'before', 'challenge' branch has 'after'.

    Returns a ChallengeRepo with paths and branch names.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"crb-{challenge.id}-", dir=base_tmp))
    repo = Repo.init(tmp_dir, initial_branch="main")
    repo.config_writer().set_value("user", "name", "CRB").release()
    repo.config_writer().set_value("user", "email", "crb@benchmark").release()

    # Copy 'before' files and commit on main
    _copy_tree(challenge.before_dir, tmp_dir)
    repo.git.add(A=True)
    repo.index.commit("Initial state (before)")

    # Create PR branch and apply 'after' files
    repo.git.checkout("-b", "challenge")

    # Remove all tracked files, then copy 'after'
    for item in tmp_dir.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    _copy_tree(challenge.after_dir, tmp_dir)
    repo.git.add(A=True)
    repo.index.commit(challenge.pr.title)

    return ChallengeRepo(repo_path=tmp_dir, repo=repo, challenge=challenge)


def _copy_tree(src: Path, dst: Path) -> None:
    """Copy contents of src into dst (without copying src dir itself)."""
    for item in src.iterdir():
        dest = dst / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
