"""Domain types of the project index: projects, metadata blocks and the check report."""

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectPath:
    """Where a project lives: `<theme>/<sujet>/<projet>`."""

    theme: str
    sujet: str
    projet: str

    def __str__(self) -> str:
        return f"{self.theme}/{self.sujet}/{self.projet}"


@dataclass(frozen=True)
class NoBlock:
    """The README does not start with a metadata block: the project is not indexed."""


@dataclass(frozen=True)
class MalformedBlock:
    """The README starts a metadata block that cannot be read, for the given reason."""

    reason: str


@dataclass(frozen=True)
class Block:
    """The fields of a metadata block, as read from the README and not yet validated."""

    fields: Mapping[str, object]


FrontMatter = NoBlock | MalformedBlock | Block


@dataclass(frozen=True)
class ProjectMetadata:
    """The validated metadata of a project."""

    titre: str
    auteurs: tuple[str, ...]
    description: str
    date: dt.date | None
    session: str | None
    stack: tuple[str, ...]


@dataclass(frozen=True)
class InvalidProject:
    """A project whose metadata block breaks the format, with every problem found."""

    path: ProjectPath
    problems: tuple[str, ...]


@dataclass(frozen=True)
class IndexedProject:
    """A project whose metadata block is valid."""

    path: ProjectPath
    metadata: ProjectMetadata


@dataclass
class CheckReport:
    """What the check found, project by project: valid, without a block, or invalid."""

    indexed: list[IndexedProject] = field(default_factory=list)
    without_metadata: list[ProjectPath] = field(default_factory=list)
    invalid: list[InvalidProject] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Tell whether every metadata block present is valid."""
        return not self.invalid


@dataclass(frozen=True)
class Published:
    """The index was published with the valid projects of the report."""

    report: CheckReport


@dataclass(frozen=True)
class Blocked:
    """Nothing was published, because some metadata blocks are invalid."""

    report: CheckReport


PublishOutcome = Published | Blocked


@dataclass(frozen=True)
class TagMove:
    """A project's default tag, moved to the given commit."""

    tag: str
    commit: str


@dataclass(frozen=True)
class TagFailure:
    """A default tag that could not be moved, and why."""

    tag: str
    reason: str


@dataclass
class TagSync:
    """What the tag sync did: the tags it moved, the tags already in place, the tags it could not move."""

    moved: list[TagMove] = field(default_factory=list)
    up_to_date: list[str] = field(default_factory=list)
    failed: list[TagFailure] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        """Tell whether every default tag is now on its project's last commit."""
        return not self.failed
