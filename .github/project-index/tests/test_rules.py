import datetime as dt
import re
from pathlib import Path

import pytest

from project_index.constants import NON_PROJECT_DIRS
from project_index.metadata import ProjectMetadata, ProjectPath
from project_index.rules import project_of_readme, validate_metadata

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


def test_non_project_dirs_match_check_structure_script():
    script = (Path(__file__).parents[2] / "scripts" / "check-structure.sh").read_text()
    pattern = re.search(r"grep -vE '\^\(([^)]*)\)/'", script).group(1)
    assert {name.replace("\\", "") for name in pattern.split("|")} == NON_PROJECT_DIRS
