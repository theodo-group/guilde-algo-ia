"""Git adapter: reads the tracked paths and README metadata blocks, and moves the project tags on origin."""

import subprocess
from functools import cached_property
from pathlib import Path

from project_index.adapters.front_matter import read_front_matter
from project_index.constants import TAGS_BRANCH, TAGS_REMOTE
from project_index.metadata import FrontMatter, MalformedBlock, ProjectPath
from project_index.ports import RepoUnavailable, TagsUnwritable


def run_git(args: list[str], *, cwd: Path | None = None) -> str:
    """Run a git command and return its output. Raises RepoUnavailable with git's own message."""
    try:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as error:
        raise RepoUnavailable(error.stderr.strip() or f"git exited with status {error.returncode}") from error
    except OSError as error:
        raise RepoUnavailable(f"cannot run git: {error}") from error


class GitRepo:
    """A git repo: its tracked files (RepoFiles) and its project tags (ProjectTags).

    As ProjectTags it reads origin/main and the tags on origin, and moves and force-pushes
    the default tags to origin.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def current(cls) -> "GitRepo":
        """Return the repo that holds the current folder. Raises RepoUnavailable."""
        return cls(Path(run_git(["rev-parse", "--show-toplevel"]).strip()))

    def tracked_files(self) -> list[str]:
        """Return the paths of every tracked file, relative to the repo root. Raises RepoUnavailable."""
        return [name for name in run_git(["ls-files", "-z"], cwd=self.root).split("\0") if name]

    def front_matter(self, file: str) -> FrontMatter:
        """Return the metadata block at the top of a file; a file that cannot be read gives a MalformedBlock."""
        try:
            text = (self.root / file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            return MalformedBlock(f"cannot read the README: {error}")
        return read_front_matter(text)

    def last_commit(self, project: ProjectPath) -> str:
        """Return the last commit of origin/main that touches the project folder. Raises TagsUnwritable.

        Reading origin/main, not HEAD, keeps a run from a branch or an older checkout from
        moving the tags; a shallow clone is refused because its history is cut.
        """
        if self._is_shallow:
            raise TagsUnwritable("the clone is shallow: fetch the full history (fetch-depth: 0)")
        branch = f"{TAGS_REMOTE}/{TAGS_BRANCH}"
        commit = self._git_for_tags(["log", "-1", "--format=%H", branch, "--", str(project)]).strip()
        if not commit:
            raise TagsUnwritable(f"no commit of {branch} touches {project}")
        return commit

    def tagged_commit(self, tag: str) -> str | None:
        """Return the commit the tag points to on origin, or None when origin has no such tag.

        The remote is read, not the local tag, so a rerun after a failed push sees the stale
        tag again. Raises TagsUnwritable when origin cannot be read.
        """
        ref = f"refs/tags/{tag}"
        lines = self._git_for_tags(["ls-remote", "--tags", TAGS_REMOTE, ref, f"{ref}^{{}}"]).splitlines()
        commits = dict(reversed(line.split("\t")) for line in lines if "\t" in line)
        return commits.get(f"{ref}^{{}}", commits.get(ref))

    def move_tag(self, tag: str, commit: str) -> None:
        """Point the tag at the commit, then force-push it. Raises TagsUnwritable."""
        self._git_for_tags(["tag", "--force", tag, commit])
        self._git_for_tags(["push", "--force", TAGS_REMOTE, f"refs/tags/{tag}"])

    @cached_property
    def _is_shallow(self) -> bool:
        return self._git_for_tags(["rev-parse", "--is-shallow-repository"]).strip() == "true"

    def _git_for_tags(self, args: list[str]) -> str:
        try:
            return run_git(args, cwd=self.root)
        except RepoUnavailable as error:
            raise TagsUnwritable(str(error)) from error
