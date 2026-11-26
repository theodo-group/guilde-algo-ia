"""Ports the project index domain needs."""

from typing import Protocol

from project_index.metadata import FrontMatter


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
