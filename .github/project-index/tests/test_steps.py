from project_index.metadata import (
    Block,
    Blocked,
    MalformedBlock,
    NoBlock,
    ProjectPath,
    Published,
)
from project_index.steps import check_projects, publish_index
from tests.fakes import FakeRepo, FakeSite

VALID = Block({"titre": "T", "auteurs": ["a"], "description": "D"})


def path(name):
    return ProjectPath("ia", "mlx", name)


def test_sorts_project_readmes_by_outcome():
    report = check_projects(FakeRepo({
        "ia/mlx/ok/README.md": VALID,
        "ia/mlx/bare/README.md": NoBlock(),
        "ia/mlx/broken/README.md": MalformedBlock("never closed"),
        "ia/mlx/empty/README.md": Block({}),
    }))
    assert [p.path for p in report.indexed] == [path("ok")]
    assert report.without_metadata == [path("bare")]
    assert [(p.path, len(p.problems)) for p in report.invalid] == [(path("broken"), 1), (path("empty"), 3)]
    assert not report.passed


def test_other_files_are_not_read():
    repo = FakeRepo({"ia/mlx/ok/README.md": VALID, "ia/mlx/ok/src/README.md": MalformedBlock("x"), "README.md": MalformedBlock("x")})
    report = check_projects(repo)
    assert report.passed
    assert [p.path for p in report.indexed] == [path("ok")]


def test_projects_are_sorted_by_path():
    report = check_projects(FakeRepo({"ia/mlx/b/README.md": VALID, "algo/knn/a/README.md": VALID}))
    assert [str(p.path) for p in report.indexed] == ["algo/knn/a", "ia/mlx/b"]


def test_publish_index_publishes_the_valid_projects():
    site = FakeSite()
    outcome = publish_index(FakeRepo({"ia/mlx/ok/README.md": VALID, "ia/mlx/bare/README.md": NoBlock()}), site)
    assert isinstance(outcome, Published)
    assert [p.path for p in site.published] == [path("ok")]


def test_publish_index_is_blocked_by_an_invalid_block():
    site = FakeSite()
    outcome = publish_index(FakeRepo({"ia/mlx/ok/README.md": VALID, "ia/mlx/bad/README.md": Block({})}), site)
    assert isinstance(outcome, Blocked)
    assert site.published is None
