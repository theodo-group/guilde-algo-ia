import datetime as dt

import pytest

from project_index.metadata import ProjectMetadata, ProjectPath
from project_index.rules import (
    default_tag,
    file_problems,
    is_outside_projects,
    project_of_file,
    project_of_readme,
    project_problems,
    validate_metadata,
)

VALID = {
    "titre": "MLX vs PyTorch",
    "auteurs": ["Vlor999"],
    "description": "Compare MLX and PyTorch.",
}


def test_minimal_block_is_valid():
    assert validate_metadata(VALID) == ProjectMetadata(
        titre="MLX vs PyTorch", auteurs=("Vlor999",), description="Compare MLX and PyTorch.",
        date=None, session=None, stack=(),
    )


def test_full_block_is_valid():
    fields = VALID | {"date": dt.date(2026, 3, 11), "session": "https://notion.so/x", "stack": ["python", "mlx"]}
    outcome = validate_metadata(fields)
    assert isinstance(outcome, ProjectMetadata)
    assert (outcome.date, outcome.session, outcome.stack) == (dt.date(2026, 3, 11), "https://notion.so/x", ("python", "mlx"))


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"titre": None}, "'titre' must be a non-empty text"),
        ({"titre": "  "}, "'titre' must be a non-empty text"),
        ({"titre": ["x"]}, "'titre' must be a non-empty text"),
        ({"description": ""}, "'description' must be a non-empty text"),
        ({"auteurs": []}, "'auteurs' must be a non-empty list of texts"),
        ({"auteurs": "Vlor999"}, "'auteurs' must be a non-empty list of texts"),
        ({"auteurs": ["", "x"]}, "'auteurs' must be a non-empty list of texts"),
        ({"stack": "python"}, "'stack' must be a list of texts"),
        ({"stack": [1]}, "'stack' must be a list of texts"),
        ({"date": "2026-03-11"}, "'date' must be a date (YYYY-MM-DD)"),
        ({"date": dt.datetime(2026, 3, 11, 14)}, "'date' must be a date (YYYY-MM-DD)"),
        ({"session": "http://x"}, "'session' must be an https:// URL"),
        ({"session": "https://"}, "'session' must be an https:// URL"),
        ({"titre": "<Nom du projet>"}, "'titre' still holds a template placeholder: fill it or remove the metadata block"),
        ({"auteurs": ["<github-login>"]}, "'auteurs' still holds a template placeholder: fill it or remove the metadata block"),
        ({"session": "https://<lien>"}, "'session' still holds a template placeholder: fill it or remove the metadata block"),
        ({"foo": 1, "bar": 2}, "unknown keys: bar, foo"),
    ],
)
def test_each_rule_reports_its_problem(change, problem):
    fields = {key: value for key, value in (VALID | change).items() if value is not None}
    outcome = validate_metadata(fields)
    assert isinstance(outcome, list)
    assert problem in outcome


def test_all_problems_are_reported_together():
    outcome = validate_metadata({"session": "http://x", "foo": 1})
    assert len(outcome) == 5


@pytest.mark.parametrize(
    ("file", "project"),
    [
        ("ia/mlx/mlx-vs-pytorch/README.md", ProjectPath("ia", "mlx", "mlx-vs-pytorch")),
        ("ia/mlx/mlx-vs-pytorch/src/README.md", None),
        ("ia/mlx/README.md", None),
        ("README.md", None),
        ("ia/mlx/mlx-vs-pytorch/main.py", None),
        ("_template/a/b/README.md", None),
        (".github/a/b/README.md", None),
        (".claude/skills/x/README.md", None),
    ],
)
def test_project_of_readme(file, project):
    assert project_of_readme(file) == project


def test_default_tag():
    assert default_tag(ProjectPath("ia", "mlx", "mlx-vs-pytorch")) == "projet/ia/mlx/mlx-vs-pytorch"


@pytest.mark.parametrize(
    ("file", "project"),
    [
        ("ia/mlx/mlx-vs-pytorch/README.md", ProjectPath("ia", "mlx", "mlx-vs-pytorch")),
        ("ia/mlx/mlx-vs-pytorch/src/main.py", ProjectPath("ia", "mlx", "mlx-vs-pytorch")),
        ("ia/mlx/notes.md", None),
        ("README.md", None),
        ("_template/a/b/README.md", None),
        (".github/project-index/tests/fakes.py", None),
        (".claude/skills/x/README.md", None),
    ],
)
def test_project_of_file(file, project):
    assert project_of_file(file) == project


@pytest.mark.parametrize(
    ("file", "outside"),
    [
        ("ia/notes.md", True),
        ("ia/mlx/notes.md", True),
        ("README.md", False),
        ("ia/mlx/a/README.md", False),
        (".github/scripts/x.sh", False),
        ("_template/README.md", False),
        (".claude/skills/x", False),
    ],
)
def test_is_outside_projects(file, outside):
    assert is_outside_projects(file) is outside


MB = 1024 * 1024


@pytest.mark.parametrize(
    ("file", "size", "problems"),
    [
        ("ia/mlx/a/main.py", 10, []),
        ("ia/mlx/a/.env.example", 10, []),
        ("ia/mlx/a/.env", 10, ["secret file committed, keep it local and list its variables in .env.example"]),
        (".env.local", 10, ["secret file committed, keep it local and list its variables in .env.example"]),
        ("ia/mlx/a/data.bin", 10 * MB, []),
        ("ia/mlx/a/data.bin", 12 * MB, ["12 MB, over the 10 MB limit (put data in data/, which is not versioned)"]),
        ("ia/mlx/a/gone.txt", None, ["cannot read the file: commit its deletion or restore it"]),
    ],
)
def test_file_problems(file, size, problems):
    assert file_problems(file, size=size) == problems


@pytest.mark.parametrize(
    ("project", "files", "owner_paths", "problems"),
    [
        (ProjectPath("ia", "mlx", "a"), {"ia/mlx/a/README.md"}, {"ia/mlx/a"}, []),
        (ProjectPath("IA", "mlx_x", "a"), {"IA/mlx_x/a/README.md"}, {"IA/mlx_x/a"}, [
            "'IA' is not kebab-case (lowercase, digits, dashes)",
            "'mlx_x' is not kebab-case (lowercase, digits, dashes)",
        ]),
        (ProjectPath("ia", "mlx", "a-"), {"ia/mlx/a-/README.md"}, {"ia/mlx/a-"}, [
            "'a-' is not kebab-case (lowercase, digits, dashes)",
        ]),
        (ProjectPath("ia", "mlx", "a"), {"ia/mlx/a/src/README.md"}, {"ia/mlx/a"}, ["missing README.md"]),
        (ProjectPath("ia", "mlx", "a"), {"ia/mlx/a/README.md"}, {"ia/mlx/b"}, [
            "missing owner line in .github/CODEOWNERS",
        ]),
        (ProjectPath("ia", "mlx", "a"), {"ia/mlx/a/README.md"}, {"ia/mlx/a/**"}, []),
        (ProjectPath("ia", "mlx", "a"), {"ia/mlx/a/README.md"}, {"ia/mlx/a/src"}, []),
        (ProjectPath("ia", "mlx", "a"), {"ia/mlx/a/README.md"}, {"ia/mlx/ab"}, [
            "missing owner line in .github/CODEOWNERS",
        ]),
    ],
)
def test_project_problems(project, files, owner_paths, problems):
    assert project_problems(project, files=frozenset(files), owner_paths=frozenset(owner_paths)) == problems
