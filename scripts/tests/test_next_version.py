"""Tests for scripts/next-version.sh.

Each test builds a throwaway git repository so the bump rules are exercised
against real `git log` output rather than a stubbed string.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "next-version.sh"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    return tmp_path


def commit(repo: Path, message: str) -> None:
    (repo / "file.txt").write_text(message)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def next_version(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args], cwd=repo, capture_output=True, text=True
    )


def test_feat_bumps_the_minor_and_resets_the_patch(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")
    commit(repo, "feat(agent): add a subject picker")

    assert next_version(repo).stdout.strip() == "1.3.0"


def test_fix_bumps_only_the_patch(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")
    commit(repo, "fix(backend): stop swallowing Redis errors")

    assert next_version(repo).stdout.strip() == "1.2.4"


@pytest.mark.parametrize(
    "message",
    [
        "feat(agent)!: drop the dispatch toggle",
        "refactor!: move the repository",
        "feat: rework config\n\nBREAKING CHANGE: VOICE_PIPELINE_MODE is gone",
    ],
)
def test_breaking_change_bumps_the_major(repo, message):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")
    commit(repo, message)

    assert next_version(repo).stdout.strip() == "2.0.0"


def test_a_breaking_commit_wins_over_a_feat(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")
    commit(repo, "feat: something additive")
    commit(repo, "fix!: and something breaking")

    assert next_version(repo).stdout.strip() == "2.0.0"


def test_non_releasable_types_still_produce_a_patch(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")
    commit(repo, "docs: rewrite the README")

    assert next_version(repo).stdout.strip() == "1.2.4"


def test_two_component_tag_is_normalised(repo):
    """The repo's existing tag is `v1.0`, not `v1.0.0`."""
    commit(repo, "chore: init")
    git(repo, "tag", "v1.0")
    commit(repo, "fix: something")

    assert next_version(repo).stdout.strip() == "1.0.1"


def test_first_release_with_no_tags_starts_from_zero(repo):
    commit(repo, "feat: the whole thing")

    assert next_version(repo).stdout.strip() == "0.1.0"


def test_highest_tag_wins_regardless_of_creation_order(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.9.0")
    commit(repo, "chore: more")
    git(repo, "tag", "v1.10.0")
    commit(repo, "chore: even more")
    git(repo, "tag", "v1.2.0")
    commit(repo, "fix: something")

    assert next_version(repo).stdout.strip() == "1.10.1"


def test_explicit_bump_overrides_the_commit_messages(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")
    commit(repo, "docs: only docs")

    assert next_version(repo, "major").stdout.strip() == "2.0.0"
    assert next_version(repo, "minor").stdout.strip() == "1.3.0"


def test_nothing_to_release_exits_nonzero(repo):
    commit(repo, "chore: init")
    git(repo, "tag", "v1.2.3")

    result = next_version(repo)
    assert result.returncode == 1
    assert "nothing to release" in result.stderr


def test_an_unknown_bump_argument_is_rejected(repo):
    commit(repo, "feat: init")

    result = next_version(repo, "sideways")
    assert result.returncode == 2
    assert "usage:" in result.stderr
