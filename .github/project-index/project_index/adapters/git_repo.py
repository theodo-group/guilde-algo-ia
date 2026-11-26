"""Reads the files of a git repo: the tracked paths and the README metadata blocks."""

import subprocess
from pathlib import Path

from project_index.adapters.front_matter import read_front_matter
from project_index.metadata import FrontMatter, MalformedBlock
from project_index.ports import RepoUnavailable


def run_git(args: list[str], *, cwd: Path | None = None) -> str:
    """Run a git command and return its output. Raises RepoUnavailable with git's own message."""
    try:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as error:
        raise RepoUnavailable(error.stderr.strip() or f"git exited with status {error.returncode}") from error
    except OSError as error:
        raise RepoUnavailable(f"cannot run git: {error}") from error


class GitRepo:
    """The files git tracks under a repo root."""

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
