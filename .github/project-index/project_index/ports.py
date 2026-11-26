"""Ports the project index domain needs."""

from typing import Protocol

from project_index.metadata import FrontMatter, IndexedProject, ProjectPath


class RepoUnavailable(Exception):
    """The files of the repo could not be listed."""


class RepoFiles(Protocol):
    """The files of the repo and the metadata block at the top of each README."""

    def tracked_files(self) -> list[str]:
        """Return the paths of every tracked file, relative to the repo root. Raises RepoUnavailable."""
        ...

    def front_matter(self, file: str) -> FrontMatter:
        """Return the metadata block at the top of a file; a file that cannot be read gives a MalformedBlock."""
        ...


class SiteUnwritable(Exception):
    """The index site could not be written where it was asked to go."""


class IndexSite(Protocol):
    """The published index of the projects."""

    def publish(self, projects: list[IndexedProject]) -> None:
        """Publish the given projects as the whole index. Raises SiteUnwritable."""
        ...


class TagsUnwritable(Exception):
    """A project tag could not be read, moved or shared."""


class ProjectTags(Protocol):
    """The default tags that mark the last change of each project."""

    def last_commit(self, project: ProjectPath) -> str:
        """Return the last commit that touches the project folder. Raises TagsUnwritable."""
        ...

    def tagged_commit(self, tag: str) -> str | None:
        """Return the commit a tag points to, or None when the tag does not exist. Raises TagsUnwritable."""
        ...

    def move_tag(self, tag: str, commit: str) -> None:
        """Point the tag at the commit and share it. Raises TagsUnwritable."""
        ...
