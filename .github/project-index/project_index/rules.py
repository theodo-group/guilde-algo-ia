"""Domain rules of the project index: what a project is, the repo standard, and what a valid block holds."""

import datetime as dt
import re
from collections.abc import Mapping
from pathlib import PurePosixPath

from project_index.constants import (
    AUTHORS_KEY,
    BYTES_PER_MB,
    CODEOWNERS_FILE,
    DATE_KEY,
    DESCRIPTION_KEY,
    KNOWN_KEYS,
    MAX_FILE_MB,
    NON_PROJECT_DIRS,
    OPTIONAL_LIST_KEYS,
    OUTSIDE_PROJECT_PROBLEM,
    PLACEHOLDER_PATTERN,
    PROJECT_DEPTH,
    PROJECT_NAME_PATTERN,
    README_NAME,
    REQUIRED_LIST_KEYS,
    REQUIRED_TEXT_KEYS,
    SECRET_EXAMPLE_NAME,
    SECRET_FILE_NAME,
    SESSION_KEY,
    SESSION_PREFIX,
    STACK_KEY,
    TAG_PREFIX,
    TITLE_KEY,
    UNREADABLE_FILE_PROBLEM,
)
from project_index.metadata import ProjectMetadata, ProjectPath


def is_tooling_file(file: str) -> bool:
    """Tell whether a repo file sits in a tooling folder (`.claude`, `.github`, `_template`), which holds no project."""
    return PurePosixPath(file).parts[0] in NON_PROJECT_DIRS


def project_of_file(file: str) -> ProjectPath | None:
    """Return the project that holds the given repo file, or None for a file outside any project.

    A project is a folder at `<theme>/<sujet>/<projet>/`, outside the tooling folders.
    """
    parts = PurePosixPath(file).parts
    if len(parts) <= PROJECT_DEPTH or is_tooling_file(file):
        return None
    return ProjectPath(*parts[:PROJECT_DEPTH])


def project_of_readme(file: str) -> ProjectPath | None:
    """Return the project whose README the given repo file is, or None for any other file.

    A project README sits at `<theme>/<sujet>/<projet>/README.md`.
    """
    project = project_of_file(file)
    if project is None or file != f"{project}/{README_NAME}":
        return None
    return project


def is_outside_projects(file: str) -> bool:
    """Tell whether a file sits directly in a theme or subject folder, where only project folders belong."""
    return 1 < len(PurePosixPath(file).parts) <= PROJECT_DEPTH and not is_tooling_file(file)


def outside_project_problems(file: str) -> list[str]:
    """Return the problem of a file that sits in a theme or subject folder instead of a project folder."""
    return [OUTSIDE_PROJECT_PROBLEM] if is_outside_projects(file) else []


def is_secret_file(file: str) -> bool:
    """Tell whether a file holds local secrets: `.env` or `.env.<name>`, except the `.env.example` template."""
    name = PurePosixPath(file).name
    return name == SECRET_FILE_NAME or (name.startswith(f"{SECRET_FILE_NAME}.") and name != SECRET_EXAMPLE_NAME)


def file_problems(file: str, *, size: int | None) -> list[str]:
    """Return the problems of a tracked file: a committed secret, over the size limit, or unreadable.

    `size` is in bytes, or None when the file cannot be read (for example deleted but not committed).
    """
    problems = []
    if is_secret_file(file):
        problems.append(f"secret file committed, keep it local and list its variables in {SECRET_EXAMPLE_NAME}")
    if size is None:
        problems.append(UNREADABLE_FILE_PROBLEM)
    elif size > MAX_FILE_MB * BYTES_PER_MB:
        problems.append(
            f"{size // BYTES_PER_MB} MB, over the {MAX_FILE_MB} MB limit (put data in data/, which is not versioned)"
        )
    return problems


def project_problems(project: ProjectPath, *, files: frozenset[str], owner_paths: frozenset[str]) -> list[str]:
    """Return the problems of a project folder.

    Each part of its path must be kebab-case, its README must be among the tracked `files`,
    and one of the CODEOWNERS `owner_paths` must be its folder or a path below it.
    """
    problems = [
        f"'{part}' is not kebab-case (lowercase, digits, dashes)"
        for part in (project.theme, project.sujet, project.projet)
        if not re.fullmatch(PROJECT_NAME_PATTERN, part)
    ]
    if f"{project}/{README_NAME}" not in files:
        problems.append(f"missing {README_NAME}")
    if not any(path == str(project) or path.startswith(f"{project}/") for path in owner_paths):
        problems.append(f"missing owner line in {CODEOWNERS_FILE}")
    return problems


def default_tag(project: ProjectPath) -> str:
    """Return the tag that follows the last commit of a project folder: `projet/<theme>/<sujet>/<projet>`."""
    return f"{TAG_PREFIX}{project}"


def is_filled_text(value: object) -> bool:
    """Tell whether a value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def is_filled_text_list(value: object) -> bool:
    """Tell whether a value is a list of non-empty strings (the list itself may be empty)."""
    return isinstance(value, list) and all(is_filled_text(item) for item in value)


def required_key_problems(fields: Mapping[str, object]) -> list[str]:
    """Return one problem per required key that is missing or empty."""
    problems = [f"'{key}' must be a non-empty text" for key in REQUIRED_TEXT_KEYS if not is_filled_text(fields.get(key))]
    for key in REQUIRED_LIST_KEYS:
        value = fields.get(key)
        if not (is_filled_text_list(value) and value):
            problems.append(f"'{key}' must be a non-empty list of texts")
    return problems


def is_session_date(value: object) -> bool:
    """Tell whether a value is a calendar date without a time."""
    return isinstance(value, dt.date) and not isinstance(value, dt.datetime)


def is_session_link(value: object) -> bool:
    """Tell whether a value is an https URL with something after the scheme."""
    return isinstance(value, str) and value.startswith(SESSION_PREFIX) and len(value) > len(SESSION_PREFIX)


def optional_key_problems(fields: Mapping[str, object]) -> list[str]:
    """Return one problem per optional key that is present with the wrong shape."""
    problems = [f"'{key}' must be a list of texts" for key in OPTIONAL_LIST_KEYS if key in fields and not is_filled_text_list(fields[key])]
    if DATE_KEY in fields and not is_session_date(fields[DATE_KEY]):
        problems.append(f"'{DATE_KEY}' must be a date (YYYY-MM-DD)")
    if SESSION_KEY in fields and not is_session_link(fields[SESSION_KEY]):
        problems.append(f"'{SESSION_KEY}' must be an {SESSION_PREFIX} URL")
    return problems


def placeholder_problems(fields: Mapping[str, object]) -> list[str]:
    """Return one problem per key that still holds a `<...>` placeholder from the template."""
    def holds_placeholder(value: object) -> bool:
        values = value if isinstance(value, list) else [value]
        return any(isinstance(item, str) and re.search(PLACEHOLDER_PATTERN, item) for item in values)

    return [
        f"'{key}' still holds a template placeholder: fill it or remove the metadata block"
        for key, value in fields.items()
        if holds_placeholder(value)
    ]


def unknown_key_problems(fields: Mapping[str, object]) -> list[str]:
    """Return a problem naming the keys the metadata format does not define."""
    unknown = sorted(set(fields) - KNOWN_KEYS)
    return [f"unknown keys: {', '.join(unknown)}"] if unknown else []


def validate_metadata(fields: Mapping[str, object]) -> ProjectMetadata | list[str]:
    """Validate the fields of a metadata block.

    Returns the metadata when every rule holds, otherwise the list of problems found,
    each one naming its key, so the author can fix them all in one go.
    """
    problems = (
        required_key_problems(fields)
        + optional_key_problems(fields)
        + placeholder_problems(fields)
        + unknown_key_problems(fields)
    )
    if problems:
        return problems
    return ProjectMetadata(
        titre=fields[TITLE_KEY],
        auteurs=tuple(fields[AUTHORS_KEY]),
        description=fields[DESCRIPTION_KEY],
        date=fields.get(DATE_KEY),
        session=fields.get(SESSION_KEY),
        stack=tuple(fields.get(STACK_KEY, [])),
    )
