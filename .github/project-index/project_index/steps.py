"""Domain steps of the project index."""

from project_index.metadata import (
    Block,
    Blocked,
    CheckReport,
    IndexedProject,
    InvalidProject,
    MalformedBlock,
    NoBlock,
    ProjectMetadata,
    Published,
    PublishOutcome,
    StructureProblem,
    StructureReport,
    TagFailure,
    TagMove,
    TagSync,
)
from project_index.ports import IndexSite, ProjectTags, RepoFiles, TagsUnwritable
from project_index.rules import (
    default_tag,
    file_problems,
    outside_project_problems,
    project_of_file,
    project_of_readme,
    project_problems,
    validate_metadata,
)


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


def check_structure(repo: RepoFiles) -> StructureReport:
    """Check the repo standard on every tracked file and every project folder.

    Problems come files first (secrets, size), then projects (names, README, owner), then
    files that sit outside any project, so the author can fix them all in one go.
    """
    files = sorted(repo.tracked_files())
    report = StructureReport()
    for file in files:
        report.problems += [StructureProblem(file, problem) for problem in file_problems(file, size=repo.file_size(file))]
    projects = sorted(set(filter(None, map(project_of_file, files))), key=str)
    tracked, owner_paths = frozenset(files), repo.owner_paths()
    for project in projects:
        report.problems += [
            StructureProblem(str(project), problem)
            for problem in project_problems(project, files=tracked, owner_paths=owner_paths)
        ]
    report.problems += [StructureProblem(file, problem) for file in files for problem in outside_project_problems(file)]
    return report


def publish_index(repo: RepoFiles, site: IndexSite) -> PublishOutcome:
    """Check every project, then publish the valid ones as the whole index.

    Nothing is published when a metadata block is invalid: the site keeps its last good
    version, and the outcome says so.
    """
    report = check_projects(repo)
    if not report.passed:
        return Blocked(report)
    site.publish(report.indexed)
    return Published(report)


def sync_project_tags(repo: RepoFiles, tags: ProjectTags) -> TagSync:
    """Point each project's default tag at the last commit that touches its folder.

    A tag already on that commit is left alone, so a rerun changes nothing. A tag that
    cannot be moved is recorded with its reason and the other projects still go through,
    so the outcome names a partial sync.
    """
    sync = TagSync()
    projects = sorted(filter(None, map(project_of_readme, repo.tracked_files())), key=str)
    for project in projects:
        tag = default_tag(project)
        try:
            commit = tags.last_commit(project)
            if tags.tagged_commit(tag) == commit:
                sync.up_to_date.append(tag)
                continue
            tags.move_tag(tag, commit)
        except TagsUnwritable as error:
            sync.failed.append(TagFailure(tag, str(error)))
            continue
        sync.moved.append(TagMove(tag, commit))
    return sync
