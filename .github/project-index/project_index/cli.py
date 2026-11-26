"""Entry point: `python -m project_index check`, `build --out <folder>` or `tags`."""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from project_index.adapters.git_repo import GitRepo
from project_index.adapters.static_site import StaticSite
from project_index.constants import (
    ANNOTATION_PREFIX,
    BUILD_COMMAND,
    CHECK_COMMAND,
    FORMAT_HINT,
    README_NAME,
    SITE_TEMPLATE_DIR,
    TAGS_COMMAND,
)
from project_index.metadata import Blocked, CheckReport, Published
from project_index.ports import (
    IndexSite,
    ProjectTags,
    RepoFiles,
    RepoUnavailable,
    SiteUnwritable,
)
from project_index.steps import check_projects, publish_index, sync_project_tags


def static_site(out_dir: Path) -> IndexSite:
    """Build the site adapter that writes the page template and the JSON into a folder."""
    return StaticSite(SITE_TEMPLATE_DIR, out_dir)


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


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line: `check`, or `build` with its required `--out` folder."""
    parser = argparse.ArgumentParser(prog="project_index")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(CHECK_COMMAND, help="validate the metadata blocks")
    build = commands.add_parser(BUILD_COMMAND, help="validate, then write the index site")
    build.add_argument("--out", type=Path, required=True, help="folder to write the site into")
    commands.add_parser(TAGS_COMMAND, help="move each project's default tag to its last commit")
    return parser.parse_args(argv)


def run_build(repo: RepoFiles, site: IndexSite, *, out: Path) -> int:
    """Publish the index and report the outcome; return the exit code."""
    match publish_index(repo, site):
        case Published(report=report):
            print_report(report)
            print(f"Site written to {out}")
            return 0
        case Blocked(report=report):
            print_report(report)
            print("Nothing published: the site keeps its last version until the metadata is fixed.")
            return 1


def run_tags(repo: RepoFiles, tags: ProjectTags) -> int:
    """Sync the default project tags and report each move and failure; return 0 when all are in place."""
    sync = sync_project_tags(repo, tags)
    for move in sync.moved:
        print(f"{move.tag} -> {move.commit[:7]}")
    for failure in sync.failed:
        print(f"{ANNOTATION_PREFIX}{failure.tag}: {failure.reason}")
    print(f"{len(sync.moved)} tag(s) moved, {len(sync.up_to_date)} already up to date, {len(sync.failed)} failed")
    return 0 if sync.complete else 1


def run_check(repo: RepoFiles) -> int:
    """Check the metadata blocks and report them; return the exit code."""
    report = check_projects(repo)
    print_report(report)
    return 0 if report.passed else 1


def main(
    argv: list[str] | None = None,
    *,
    repo_factory: Callable[[], RepoFiles] = GitRepo.current,
    site_factory: Callable[[Path], IndexSite] = static_site,
    tags_factory: Callable[[], ProjectTags] = GitRepo.current,
) -> int:
    """Run the command and return its exit code: 0 when every block is valid, the site (build) is written, or every tag (tags) is in place."""
    args = parse_args(argv)
    try:
        if args.command == TAGS_COMMAND:
            return run_tags(repo_factory(), tags_factory())
        if args.command == BUILD_COMMAND:
            return run_build(repo_factory(), site_factory(args.out), out=args.out)
        return run_check(repo_factory())
    except RepoUnavailable as error:
        print(f"{ANNOTATION_PREFIX}cannot list the repo files: {error}", file=sys.stderr)
    except SiteUnwritable as error:
        print(f"{ANNOTATION_PREFIX}{error}", file=sys.stderr)
    return 1
