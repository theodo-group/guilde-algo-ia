from project_index.metadata import (
    Block,
    Blocked,
    MalformedBlock,
    NoBlock,
    ProjectPath,
    Published,
    StructureProblem,
)
from project_index.steps import (
    check_projects,
    check_structure,
    publish_index,
    sync_project_tags,
)
from tests.fakes import BrokenTags, FakeRepo, FakeSite, FakeTags

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


PROJECTS = FakeRepo({"ia/mlx/a/README.md": NoBlock(), "ia/mlx/b/README.md": VALID, "ia/mlx/b/src/x.py": NoBlock()})


def test_sync_moves_missing_and_stale_tags_only():
    tags = FakeTags({"ia/mlx/a": "c1", "ia/mlx/b": "c2"}, {"projet/ia/mlx/a": "c1", "projet/ia/mlx/b": "old"})
    sync = sync_project_tags(PROJECTS, tags)
    assert tags.moves == [("projet/ia/mlx/b", "c2")]
    assert sync.up_to_date == ["projet/ia/mlx/a"]


def test_sync_is_a_no_op_when_run_twice():
    tags = FakeTags({"ia/mlx/a": "c1", "ia/mlx/b": "c2"})
    sync_project_tags(PROJECTS, tags)
    second = sync_project_tags(PROJECTS, tags)
    assert second.moved == []
    assert len(tags.moves) == 2


def test_sync_records_a_failed_tag_and_moves_the_others():
    tags = BrokenTags({"ia/mlx/a": "c1", "ia/mlx/b": "c2"}, failing={"projet/ia/mlx/a"})
    sync = sync_project_tags(PROJECTS, tags)
    assert [(f.tag, f.reason) for f in sync.failed] == [("projet/ia/mlx/a", "remote rejected")]
    assert [m.tag for m in sync.moved] == ["projet/ia/mlx/b"]
    assert not sync.complete


def test_rerun_after_a_failed_push_moves_the_stale_tag():
    tags = BrokenTags({"ia/mlx/a": "c1", "ia/mlx/b": "c2"}, failing={"projet/ia/mlx/a"})
    sync_project_tags(PROJECTS, tags)
    rerun = sync_project_tags(PROJECTS, tags)
    assert [m.tag for m in rerun.moved] == ["projet/ia/mlx/a"]
    assert rerun.complete


def test_structure_reports_files_then_projects_then_stray_files():
    repo = FakeRepo(
        {
            "README.md": NoBlock(),
            ".github/CODEOWNERS": NoBlock(),
            "ia/mlx/ok/README.md": NoBlock(),
            "ia/mlx/ok/.env": NoBlock(),
            "ia/mlx/Bad/main.py": NoBlock(),
            "ia/notes.md": NoBlock(),
        },
        sizes={"ia/mlx/ok/README.md": 11 * 1024 * 1024},
        owner_paths=frozenset({"ia/mlx/ok"}),
    )
    report = check_structure(repo)
    assert report.problems == [
        StructureProblem("ia/mlx/ok/.env", "secret file committed, keep it local and list its variables in .env.example"),
        StructureProblem("ia/mlx/ok/README.md", "11 MB, over the 10 MB limit (put data in data/, which is not versioned)"),
        StructureProblem("ia/mlx/Bad", "'Bad' is not kebab-case (lowercase, digits, dashes)"),
        StructureProblem("ia/mlx/Bad", "missing README.md"),
        StructureProblem("ia/mlx/Bad", "missing owner line in .github/CODEOWNERS"),
        StructureProblem("ia/notes.md", "file outside a project, expected <theme>/<sujet>/<projet>/..."),
    ]
    assert not report.passed


def test_structure_passes_on_a_clean_repo():
    repo = FakeRepo({"README.md": NoBlock(), "ia/mlx/ok/README.md": NoBlock()}, owner_paths=frozenset({"ia/mlx/ok"}))
    assert check_structure(repo).passed


def test_structure_reports_an_unreadable_file_and_checks_the_rest():
    repo = FakeRepo(
        {"ia/mlx/a/README.md": NoBlock(), "ia/mlx/a/gone.txt": NoBlock(), "ia/stray.txt": NoBlock()},
        sizes={"ia/mlx/a/gone.txt": None},
        owner_paths=frozenset({"ia/mlx/a"}),
    )
    problems = [(p.path, p.problem) for p in check_structure(repo).problems]
    assert problems == [
        ("ia/mlx/a/gone.txt", "cannot read the file: commit its deletion or restore it"),
        ("ia/stray.txt", "file outside a project, expected <theme>/<sujet>/<projet>/..."),
    ]
