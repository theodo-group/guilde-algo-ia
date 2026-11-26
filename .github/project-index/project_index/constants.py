"""Literals shared by the project index: metadata keys, folder layout, messages."""

from pathlib import Path

TITLE_KEY = "titre"
AUTHORS_KEY = "auteurs"
DESCRIPTION_KEY = "description"
DATE_KEY = "date"
SESSION_KEY = "session"
STACK_KEY = "stack"
REQUIRED_TEXT_KEYS = (TITLE_KEY, DESCRIPTION_KEY)
REQUIRED_LIST_KEYS = (AUTHORS_KEY,)
OPTIONAL_LIST_KEYS = (STACK_KEY,)
KNOWN_KEYS = frozenset(
    REQUIRED_TEXT_KEYS + REQUIRED_LIST_KEYS + OPTIONAL_LIST_KEYS + (DATE_KEY, SESSION_KEY)
)

SESSION_PREFIX = "https://"
PLACEHOLDER_PATTERN = r"<[^<>]*>"

# Top-level folders that hold the repo tooling, not projects. check-structure.sh, a shell
# script the CI runs first, keeps its own copy of this list; tests/test_rules.py checks they agree.
NON_PROJECT_DIRS = frozenset({".claude", ".github", "_template"})
README_NAME = "README.md"
PROJECT_DEPTH = 3  # <theme>/<sujet>/<projet>
FRONT_MATTER_FENCE = "---"
BYTE_ORDER_MARK = "\ufeff"

CHECK_COMMAND = "check"
ANNOTATION_PREFIX = "::error::"  # GitHub Actions error annotation

SITE_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "site"  # .github/project-index/site/
SITE_DATA_FILE = "projects.json"
# Written first in every built site, so a rebuild, even after a crash halfway, only ever
# deletes a folder an earlier build made.
SITE_MARKER_FILE = ".project-index-site"
BUILD_COMMAND = "build"

# Default tag of a project, moved to the last commit that touches its folder. Extra tags set
# by hand add "@<label>": git cannot hold both refs a/b and a/b/c (README.md, section Tags).
TAG_PREFIX = "projet/"
TAGS_REMOTE = "origin"
TAGS_BRANCH = "main"  # tags follow the history of origin/main, whatever is checked out
TAGS_COMMAND = "tags"

FORMAT_HINT = "Metadata format: README.md, section Métadonnées."
