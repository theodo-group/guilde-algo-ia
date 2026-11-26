"""Fakes of the ports, for the domain and entry point tests."""

from project_index.metadata import FrontMatter, NoBlock
from project_index.ports import RepoUnavailable, SiteUnwritable, TagsUnwritable


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


class FakeSite:
    """A site that keeps what it was asked to publish."""

    def __init__(self) -> None:
        self.published = None

    def publish(self, projects) -> None:
        self.published = projects


class BrokenSite:
    """A site that cannot be written."""

    def publish(self, projects) -> None:
        raise SiteUnwritable("cannot write the site to out: denied")


class FakeTags:
    """Project tags kept in memory: last commit per project folder, and current tags."""

    def __init__(self, last_commits: dict[str, str], tags: dict[str, str] | None = None) -> None:
        self.last_commits = last_commits
        self.tags = dict(tags or {})
        self.moves: list[tuple[str, str]] = []

    def last_commit(self, project) -> str:
        return self.last_commits[str(project)]

    def tagged_commit(self, tag: str) -> str | None:
        return self.tags.get(tag)

    def move_tag(self, tag: str, commit: str) -> None:
        self.tags[tag] = commit
        self.moves.append((tag, commit))


class BrokenTags(FakeTags):
    """Project tags whose push fails for the given tags, once each."""

    def __init__(self, last_commits: dict[str, str], failing: set[str]) -> None:
        super().__init__(last_commits)
        self.failing = set(failing)

    def move_tag(self, tag: str, commit: str) -> None:
        if tag in self.failing:
            self.failing.discard(tag)
            raise TagsUnwritable("remote rejected")
        super().move_tag(tag, commit)
