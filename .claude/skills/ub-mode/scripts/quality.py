#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the ub-mode quality gates on the source files a branch changed.

crapper (CRAP score), dryer (duplication) and mutator (mutation testing) are
cloned at a pinned commit into a cache, then run on the files changed against
the base ref. Code the branch does not touch never fails a gate.

Run it from the root of the project to check (the folder that holds
pyproject.toml or package.json):

    uv run --script <plugin root>/skills/ub-mode/scripts/quality.py \
        [--base origin/main] [--gate crap|dry|mutate ...] [--tests <pytest path>]

The default gates are crap and dry. mutate runs only when asked with
--gate mutate, and its result is not yet reliable on uv projects.

Exit 0 when every gate passes, 1 when one fails, 2 when a tool cannot run.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from constants import (
    CACHE_ENV,
    CRAP_THRESHOLD,
    DEFAULT_BASE,
    DEFAULT_CACHE,
    DEFAULT_GATES,
    DRY_THRESHOLD,
    GATES,
    MUTATOR_MAX_WORKERS,
    MUTATOR_TIMEOUT_FACTOR,
    OUTPUT_DIRS,
    PYTHON_SUFFIXES,
    SCRIPT_SUFFIXES,
    TEST_DIRS,
    TEST_MARKERS,
    TOOLS,
    UV_COVERAGE,
    UV_TESTS,
)

SPAN = re.compile(r"^\s+(?P<file>.+):(?P<start>\d+)-(?P<end>\d+)$")


@dataclass(frozen=True)
class Changed:
    """The changed source files, split by the coverage tooling they need."""

    python: tuple[str, ...]
    scripts: tuple[str, ...]

    @property
    def all(self) -> tuple[str, ...]:
        return self.python + self.scripts


@dataclass(frozen=True)
class Verdict:
    gate: str
    passed: bool
    detail: str


# Pure logic


def is_source(path: str) -> bool:
    """A file a gate judges: application code, never a test."""
    parts = Path(path).parts
    name = parts[-1]
    if Path(name).suffix not in PYTHON_SUFFIXES | SCRIPT_SUFFIXES:
        return False
    if TEST_DIRS.intersection(parts[:-1]):
        return False
    if name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py"):
        return False
    return not any(marker in name for marker in TEST_MARKERS)


def select_changed(paths: Iterable[str], exists: set[str]) -> Changed:
    """Keep the changed sources still on disk, Python apart from TS/JS."""
    sources = sorted({p for p in paths if p in exists and is_source(p)})
    python = tuple(p for p in sources if Path(p).suffix in PYTHON_SUFFIXES)
    scripts = tuple(p for p in sources if Path(p).suffix in SCRIPT_SUFFIXES)
    return Changed(python, scripts)


def duplicates_touching(report: str, changed: set[str]) -> list[str]:
    """dryer's blocks where at least one side is a changed file."""
    kept = []
    for block in report.strip().split("\n\n"):
        files = {m["file"] for line in block.splitlines() if (m := SPAN.match(line))}
        if files & changed:
            kept.append(block)
    return kept


def missing_excludes(current: str) -> list[str]:
    lines = set(current.splitlines())
    return [entry for entry in OUTPUT_DIRS if entry not in lines]


# Adapters: git, the tool cache, the tools


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def changed_paths(base: str) -> list[str]:
    """Committed, staged, unstaged and untracked changes, relative to cwd."""
    outputs = [
        git("diff", "--name-only", "--relative", "--diff-filter=AMR", f"{base}...HEAD"),
        git("diff", "--name-only", "--relative", "--diff-filter=AMR", "HEAD"),
        git("ls-files", "--others", "--exclude-standard"),
    ]
    return [line for out in outputs for line in out.splitlines() if line]


def files_on_disk(paths: Iterable[str]) -> set[str]:
    return {p for p in paths if Path(p).is_file()}


def exclude_outputs() -> None:
    """Keep the tools' reports out of git without touching a tracked file."""
    exclude = Path(git("rev-parse", "--git-path", "info/exclude").strip())
    current = exclude.read_text() if exclude.exists() else ""
    missing = missing_excludes(current)
    if missing:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        tail = "" if not current or current.endswith("\n") else "\n"
        exclude.write_text(current + tail + "\n".join(missing) + "\n")


def tool(name: str) -> Path:
    """The tool's launcher, cloned or moved to its pinned commit first."""
    url, sha = TOOLS[name]
    folder = Path(os.environ.get(CACHE_ENV, DEFAULT_CACHE)).expanduser() / name
    if not folder.exists():
        folder.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", url, str(folder)], check=True)
    head = subprocess.run(
        ["git", "-C", str(folder), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != sha:
        subprocess.run(["git", "-C", str(folder), "fetch", "-q", "origin"], check=True)
        subprocess.run(
            ["git", "-C", str(folder), "checkout", "-q", "--detach", sha], check=True
        )
    return folder / name


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(command), flush=True)
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result


def uses_uv() -> bool:
    return Path("uv.lock").exists()


def python_options(tests: str, test_option: bool) -> list[str]:
    """Coverage, and tests for mutator, through uv when the project uses it."""
    if not uses_uv():
        return []
    options = ["--coverage-command", UV_COVERAGE.format(tests=tests)]
    if test_option:
        options += ["--test-command", UV_TESTS.format(tests=tests)]
    return options


# Gates


def crap_gate(changed: Changed, tests: str) -> Verdict:
    groups = [(changed.python, python_options(tests, False)), (changed.scripts, [])]
    failed = []
    for files, options in groups:
        if not files:
            continue
        result = run(
            [str(tool("crapper")), "--threshold", CRAP_THRESHOLD, *options, *files]
        )
        if result.returncode != 0:
            failed.append(result.returncode)
    detail = f"crapper exit codes {failed}" if failed else f"CRAP <= {CRAP_THRESHOLD}"
    return Verdict("crap", not failed, detail)


def dry_gate(changed: Changed, tests: str) -> Verdict:
    result = run([str(tool("dryer")), "--threshold", DRY_THRESHOLD])
    if result.returncode != 0:
        return Verdict("dry", False, f"dryer exit code {result.returncode}")
    found = duplicates_touching(result.stdout, set(changed.all))
    detail = "\n\n".join(found) if found else f"no pair >= {DRY_THRESHOLD}"
    return Verdict("dry", not found, detail)


def mutate_gate(changed: Changed, tests: str) -> Verdict:
    tool("crapper")  # mutator reads function names from ../crapper
    groups = [(changed.python, python_options(tests, True)), (changed.scripts, [])]
    failed = []
    for files, options in groups:
        if not files:
            continue
        result = run(
            [
                str(tool("mutator")),
                "--timeout-factor",
                MUTATOR_TIMEOUT_FACTOR,
                "--max-workers",
                MUTATOR_MAX_WORKERS,
                *options,
                *files,
            ]
        )
        if result.returncode != 0:
            failed.append(result.returncode)
    detail = (
        f"mutator exit codes {failed} (2 baseline tests fail, 3 a mutant survives)"
        if failed
        else "every mutant killed"
    )
    return Verdict("mutate", not failed, detail)


RUNNERS = {"crap": crap_gate, "dry": dry_gate, "mutate": mutate_gate}


def main() -> int:
    parser = argparse.ArgumentParser(description="ub-mode quality gates")
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--gate", action="append", choices=GATES)
    parser.add_argument(
        "--tests",
        default="",
        help="pytest target for coverage and mutants, e.g. tests/theodore_defect",
    )
    args = parser.parse_args()
    try:
        paths = changed_paths(args.base)
        changed = select_changed(paths, files_on_disk(paths))
        if not changed.all:
            print(f"No changed source file against {args.base}.")
            return 0
        exclude_outputs()
        print("Changed sources:", *changed.all, sep="\n  ")
        gates = args.gate or DEFAULT_GATES
        verdicts = [RUNNERS[gate](changed, args.tests) for gate in gates]
    except (subprocess.CalledProcessError, OSError) as error:
        print(f"ub-mode quality: cannot run, {error}", file=sys.stderr)
        return 2
    print("\nub-mode quality gates")
    for verdict in verdicts:
        status = "PASS" if verdict.passed else "FAIL"
        print(f"  {status} {verdict.gate}: {verdict.detail}")
    return 0 if all(v.passed for v in verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
