"""Fakes of the ports, for the domain and entry point tests."""

from project_index.metadata import FrontMatter, NoBlock
from project_index.ports import RepoUnavailable


class FakeRepo:
    """A repo whose files and metadata blocks are given in memory."""

    def __init__(self, blocks: dict[str, FrontMatter]) -> None:
        self.blocks = blocks

    def tracked_files(self) -> list[str]:
        return list(self.blocks)

    def front_matter(self, file: str) -> FrontMatter:
        return self.blocks.get(file, NoBlock())


class BrokenRepo:
    """A repo whose files cannot be listed."""

    def tracked_files(self) -> list[str]:
        raise RepoUnavailable("fatal: not a git repository")

    def front_matter(self, file: str) -> FrontMatter:
        raise AssertionError("never read")
