"""Domain steps of the project index."""

from project_index.metadata import (
    Block,
    CheckReport,
    IndexedProject,
    InvalidProject,
    MalformedBlock,
    NoBlock,
    ProjectMetadata,
)
from project_index.ports import RepoFiles
from project_index.rules import project_of_readme, validate_metadata


def check_projects(repo: RepoFiles) -> CheckReport:
    """Sort every project README into indexed, without metadata, or invalid.

    A README without a block is not an error (the block is optional) but it is listed,
    so the author can see why the project is not indexed.
    """
    report = CheckReport()
    for file in sorted(repo.tracked_files()):
        project = project_of_readme(file)
        if project is None:
            continue
        match repo.front_matter(file):
            case NoBlock():
                report.without_metadata.append(project)
            case MalformedBlock(reason=reason):
                report.invalid.append(InvalidProject(project, (reason,)))
            case Block(fields=fields):
                outcome = validate_metadata(fields)
                if isinstance(outcome, ProjectMetadata):
                    report.indexed.append(IndexedProject(project, outcome))
                else:
                    report.invalid.append(InvalidProject(project, tuple(outcome)))
    return report
