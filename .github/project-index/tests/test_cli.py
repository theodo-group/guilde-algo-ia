import pytest

from project_index.cli import main
from project_index.metadata import Block, MalformedBlock, NoBlock
from tests.fakes import BrokenRepo, BrokenSite, BrokenTags, FakeRepo, FakeSite, FakeTags

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
    assert out.err.strip() == "::error::cannot read the repo: fatal: not a git repository"


def test_unknown_command_is_refused():
    with pytest.raises(SystemExit):
        main(["publish"], repo_factory=BrokenRepo)


def test_build_requires_out():
    with pytest.raises(SystemExit):
        main(["build"], repo_factory=BrokenRepo)


def build(capsys, repo, site):
    code = main(["build", "--out", "out"], repo_factory=lambda: repo, site_factory=lambda out: site)
    return code, capsys.readouterr()


def test_build_publishes_and_says_where(capsys):
    site = FakeSite()
    code, out = build(capsys, FakeRepo({"ia/mlx/ok/README.md": VALID}), site)
    assert code == 0
    assert [str(p.path) for p in site.published] == ["ia/mlx/ok"]
    assert out.out.splitlines()[-1] == "Site written to out"


def test_blocked_build_says_nothing_was_published(capsys):
    site = FakeSite()
    code, out = build(capsys, FakeRepo({"ia/mlx/bad/README.md": MalformedBlock("never closed")}), site)
    assert code == 1
    assert site.published is None
    assert out.out.splitlines()[-1] == "Nothing published: the site keeps its last version until the metadata is fixed."


def test_unwritable_site_fails(capsys):
    code, out = build(capsys, FakeRepo({"ia/mlx/ok/README.md": VALID}), BrokenSite())
    assert code == 1
    assert out.err.strip() == "::error::cannot write the site to out: denied"


def test_tags_reports_each_move(capsys):
    repo = FakeRepo({"ia/mlx/a/README.md": NoBlock(), "ia/mlx/b/README.md": NoBlock()})
    tags = FakeTags({"ia/mlx/a": "1111111aaa", "ia/mlx/b": "2222222bbb"}, {"projet/ia/mlx/a": "1111111aaa"})
    code = main(["tags"], repo_factory=lambda: repo, tags_factory=lambda: tags)
    assert code == 0
    assert capsys.readouterr().out.splitlines() == ["projet/ia/mlx/b -> 2222222", "1 tag(s) moved, 1 already up to date, 0 failed"]


def test_tags_fails_when_a_tag_cannot_be_pushed(capsys):
    repo = FakeRepo({"ia/mlx/a/README.md": NoBlock()})
    code = main(["tags"], repo_factory=lambda: repo, tags_factory=lambda: BrokenTags({"ia/mlx/a": "c1"}, {"projet/ia/mlx/a"}))
    assert code == 1
    assert capsys.readouterr().out.splitlines() == [
        "::error::projet/ia/mlx/a: remote rejected",
        "0 tag(s) moved, 0 already up to date, 1 failed",
    ]


def test_structure_ok(capsys):
    repo = FakeRepo({"ia/mlx/ok/README.md": NoBlock()}, owner_paths=frozenset({"ia/mlx/ok"}))
    assert main(["structure"], repo_factory=lambda: repo) == 0
    assert capsys.readouterr().out.splitlines() == ["Structure OK"]


def test_structure_prints_one_annotation_per_problem(capsys):
    repo = FakeRepo({"ia/mlx/ok/README.md": NoBlock(), "ia/notes.md": NoBlock()})
    assert main(["structure"], repo_factory=lambda: repo) == 1
    assert capsys.readouterr().out.splitlines() == [
        "::error::ia/mlx/ok: missing owner line in .github/CODEOWNERS",
        "::error::ia/notes.md: file outside a project, expected <theme>/<sujet>/<projet>/...",
        "2 problem(s) found. Rules: README.md, section Conventions.",
    ]


def test_structure_on_unlistable_repo_fails(capsys):
    assert main(["structure"], repo_factory=BrokenRepo) == 1
    assert capsys.readouterr().err.strip() == "::error::cannot read the repo: fatal: not a git repository"
