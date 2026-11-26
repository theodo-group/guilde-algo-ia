import subprocess

import pytest

from project_index.adapters.git_repo import GitRepo
from project_index.metadata import Block, MalformedBlock, NoBlock
from project_index.ports import RepoUnavailable


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def track(root, files):
    for name, content in files.items():
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content.encode() if isinstance(content, str) else content)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


def test_lists_tracked_files_only(repo):
    track(repo, {"ia/mlx/a/README.md": "# A\n", "README.md": "# root\n"})
    (repo / "untracked.md").write_text("x")
    assert sorted(GitRepo(repo).tracked_files()) == ["README.md", "ia/mlx/a/README.md"]


def test_reads_the_metadata_block(repo):
    track(repo, {"a/README.md": "---\ntitre: x\n---\n", "b/README.md": "# no block\n"})
    assert GitRepo(repo).front_matter("a/README.md") == Block({"titre": "x"})
    assert GitRepo(repo).front_matter("b/README.md") == NoBlock()


@pytest.mark.parametrize("content", [b"---\ntitre: caf\xe9\n---\n", None])
def test_unreadable_readme_is_a_malformed_block(repo, content):
    if content is not None:
        track(repo, {"a/README.md": content})
    outcome = GitRepo(repo).front_matter("a/README.md")
    assert isinstance(outcome, MalformedBlock)
    assert outcome.reason.startswith("cannot read the README: ")


def test_outside_a_git_repo_gives_git_message(tmp_path):
    with pytest.raises(RepoUnavailable, match="not a git repository"):
        GitRepo(tmp_path).tracked_files()


def test_current_repo_is_found(repo, monkeypatch):
    monkeypatch.chdir(repo)
    assert GitRepo.current().root.resolve() == repo.resolve()
