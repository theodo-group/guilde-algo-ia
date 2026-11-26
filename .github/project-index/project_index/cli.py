"""Entry point: `python -m project_index check`."""

import argparse
import sys
from collections.abc import Callable

from project_index.adapters.git_repo import GitRepo
from project_index.constants import (
    ANNOTATION_PREFIX,
    CHECK_COMMAND,
    FORMAT_HINT,
    README_NAME,
)
from project_index.metadata import CheckReport
from project_index.ports import RepoFiles, RepoUnavailable
from project_index.steps import check_projects


def print_report(report: CheckReport) -> None:
    """Write the check outcome: one GitHub annotation per problem, then the counts."""
    for project in report.invalid:
        for problem in project.problems:
            print(f"{ANNOTATION_PREFIX}{project.path}/{README_NAME}: {problem}")
    print(f"{len(report.indexed)} project(s) with valid metadata")
    if report.without_metadata:
        names = ", ".join(str(path) for path in report.without_metadata)
        print(f"{len(report.without_metadata)} project(s) without metadata block, not indexed: {names}")
    if not report.passed:
        print(FORMAT_HINT)


def main(argv: list[str] | None = None, *, repo_factory: Callable[[], RepoFiles] = GitRepo.current) -> int:
    """Run the command and return its exit code: 0 when every block is valid, 1 otherwise."""
    parser = argparse.ArgumentParser(prog="project_index")
    parser.add_argument("command", choices=[CHECK_COMMAND], help="validate the metadata blocks")
    parser.parse_args(argv)
    try:
        report = check_projects(repo_factory())
    except RepoUnavailable as error:
        print(f"{ANNOTATION_PREFIX}cannot list the repo files: {error}", file=sys.stderr)
        return 1
    print_report(report)
    return 0 if report.passed else 1
