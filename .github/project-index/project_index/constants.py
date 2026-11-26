"""Literals shared by the project index: metadata keys, folder layout, messages."""

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

FORMAT_HINT = "Metadata format: README.md, section Métadonnées."
