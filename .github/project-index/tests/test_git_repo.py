import subprocess

import pytest

from project_index.adapters.git_repo import GitRepo
from project_index.metadata import Block, MalformedBlock, NoBlock, ProjectPath
from project_index.ports import RepoUnavailable, TagsUnwritable


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
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


def commit_all(root, message):
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message], cwd=root, check=True
    )
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo_with_remote(repo, tmp_path_factory):
    remote = tmp_path_factory.mktemp("remote")
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main"], cwd=remote, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=repo, check=True)
    return repo, remote


def push_main(repo):
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=repo, check=True)


def remote_tag(remote, tag):
    found = subprocess.run(["git", "rev-parse", f"refs/tags/{tag}"], cwd=remote, capture_output=True, text=True)
    return found.stdout.strip()


def test_last_commit_reads_origin_main_not_head(repo_with_remote):
    repo, _ = repo_with_remote
    track(repo, {"ia/mlx/a/README.md": "# A\n"})
    pushed = commit_all(repo, "a")
    push_main(repo)
    track(repo, {"ia/mlx/a/README.md": "# A local\n"})
    commit_all(repo, "a, not pushed")
    assert GitRepo(repo).last_commit(ProjectPath("ia", "mlx", "a")) == pushed


def test_shallow_clone_is_refused(repo_with_remote, tmp_path_factory):
    repo, remote = repo_with_remote
    track(repo, {"ia/mlx/a/README.md": "# A\n"})
    commit_all(repo, "a")
    track(repo, {"ia/mlx/b/README.md": "# B\n"})
    commit_all(repo, "b")
    push_main(repo)
    clone = tmp_path_factory.mktemp("clone") / "repo"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{remote}", str(clone)], check=True)
    with pytest.raises(TagsUnwritable, match="shallow"):
        GitRepo(clone).last_commit(ProjectPath("ia", "mlx", "a"))


def test_tagged_commit_reads_the_remote_tag(repo_with_remote):
    repo, _ = repo_with_remote
    track(repo, {"ia/mlx/a/README.md": "# A\n"})
    first = commit_all(repo, "a")
    push_main(repo)
    subprocess.run(["git", "tag", "projet/ia/mlx/a", first], cwd=repo, check=True)
    assert GitRepo(repo).tagged_commit("projet/ia/mlx/a") is None


def test_move_tag_points_and_pushes(repo_with_remote):
    repo, remote = repo_with_remote
    track(repo, {"ia/mlx/a/README.md": "# A\n"})
    first = commit_all(repo, "a")
    push_main(repo)
    git = GitRepo(repo)
    git.move_tag("projet/ia/mlx/a", first)
    track(repo, {"ia/mlx/a/README.md": "# A2\n"})
    second = commit_all(repo, "a2")
    push_main(repo)
    git.move_tag("projet/ia/mlx/a", second)
    assert git.tagged_commit("projet/ia/mlx/a") == second
    assert remote_tag(remote, "projet/ia/mlx/a") == second


def test_move_tag_without_remote_is_unwritable(repo):
    track(repo, {"ia/mlx/a/README.md": "# A\n"})
    first = commit_all(repo, "a")
    with pytest.raises(TagsUnwritable):
        GitRepo(repo).move_tag("projet/ia/mlx/a", first)


def test_project_without_commit_on_main_is_unwritable(repo_with_remote):
    repo, _ = repo_with_remote
    track(repo, {"README.md": "# root\n"})
    commit_all(repo, "root")
    push_main(repo)
    with pytest.raises(TagsUnwritable, match="no commit of origin/main touches"):
        GitRepo(repo).last_commit(ProjectPath("ia", "mlx", "a"))


def test_tagged_commit_peels_an_annotated_tag(repo_with_remote):
    repo, _ = repo_with_remote
    track(repo, {"ia/mlx/a/README.md": "# A\n"})
    first = commit_all(repo, "a")
    push_main(repo)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "tag", "-a", "-m", "note", "projet/ia/mlx/a", first],
        cwd=repo, check=True,
    )
    subprocess.run(["git", "push", "-q", "origin", "refs/tags/projet/ia/mlx/a"], cwd=repo, check=True)
    assert GitRepo(repo).tagged_commit("projet/ia/mlx/a") == first


def test_file_size_is_the_size_of_the_tracked_file(repo):
    track(repo, {"ia/mlx/a/data.bin": b"x" * 42})
    assert GitRepo(repo).file_size("ia/mlx/a/data.bin") == 42


def test_file_size_of_a_missing_file_is_none(repo):
    assert GitRepo(repo).file_size("missing.bin") is None


def test_owner_paths_are_the_paths_of_the_codeowners_lines(repo):
    track(repo, {".github/CODEOWNERS": "# /ia/mlx/commented/ @x\n\n*  @lead\n/ia/mlx/a/   @x\n/ia/mlx/b @y\nia/mlx/c/ @z\n"})
    assert GitRepo(repo).owner_paths() == frozenset({"*", "ia/mlx/a", "ia/mlx/b", "ia/mlx/c"})


def test_unreadable_codeowners_is_unavailable(repo):
    track(repo, {".github/CODEOWNERS": b"/ia/mlx/caf\xe9/ @x\n"})
    with pytest.raises(RepoUnavailable, match="cannot read .github/CODEOWNERS"):
        GitRepo(repo).owner_paths()


def test_no_codeowners_means_no_owner_path(repo):
    assert GitRepo(repo).owner_paths() == frozenset()
