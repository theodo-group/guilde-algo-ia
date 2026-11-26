import pytest

from project_index.cli import main
from project_index.metadata import Block, MalformedBlock, NoBlock
from tests.fakes import BrokenRepo, FakeRepo

VALID = Block({"titre": "T", "auteurs": ["a"], "description": "D"})


def run(capsys, repo):
    code = main(["check"], repo_factory=lambda: repo)
    return code, capsys.readouterr()


def test_passing_check_prints_counts(capsys):
    code, out = run(capsys, FakeRepo({"ia/mlx/ok/README.md": VALID, "ia/mlx/bare/README.md": NoBlock()}))
    assert code == 0
    assert out.out.splitlines() == [
        "1 project(s) with valid metadata",
        "1 project(s) without metadata block, not indexed: ia/mlx/bare",
    ]


def test_failing_check_prints_one_annotation_per_problem(capsys):
    code, out = run(capsys, FakeRepo({"ia/mlx/broken/README.md": MalformedBlock("never closed")}))
    assert code == 1
    assert out.out.splitlines() == [
        "::error::ia/mlx/broken/README.md: never closed",
        "0 project(s) with valid metadata",
        "Metadata format: README.md, section Métadonnées.",
    ]


def test_unlistable_repo_fails_with_git_message(capsys):
    code, out = run(capsys, BrokenRepo())
    assert code == 1
    assert out.err.strip() == "::error::cannot list the repo files: fatal: not a git repository"


def test_unknown_command_is_refused():
    with pytest.raises(SystemExit):
        main(["publish"], repo_factory=BrokenRepo)
