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

# Top-level folders that hold the repo tooling, not projects: the only definition of this list.
NON_PROJECT_DIRS = frozenset({".claude", ".github", "_template"})
README_NAME = "README.md"
PROJECT_DEPTH = 3  # <theme>/<sujet>/<projet>
FRONT_MATTER_FENCE = "---"
BYTE_ORDER_MARK = "\ufeff"

# Repo standard checked by the `structure` command (README.md, section Conventions).
PROJECT_NAME_PATTERN = r"[a-z0-9]+(-[a-z0-9]+)*"  # kebab-case
SECRET_FILE_NAME = ".env"  # also .env.<anything>, except the example below
SECRET_EXAMPLE_NAME = ".env.example"
BYTES_PER_MB = 1024 * 1024
MAX_FILE_MB = 10
CODEOWNERS_FILE = ".github/CODEOWNERS"
STRUCTURE_HINT = "Rules: README.md, section Conventions."

CHECK_COMMAND = "check"
STRUCTURE_COMMAND = "structure"
ANNOTATION_PREFIX = "::error::"  # GitHub Actions error annotation

SITE_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "site"  # .github/project-index/site/
SITE_DATA_FILE = "projects.json"
# npm libraries the page imports, installed by `npm ci` from package-lock.json and updated
# by Dependabot: site path -> installed file. site/search.js imports ./vendor/fzf/fzf.es.js.
NODE_MODULES_DIR = SITE_TEMPLATE_DIR.parent / "node_modules"  # .github/project-index/node_modules/
SITE_LIBRARIES = {
    "vendor/fzf/fzf.es.js": NODE_MODULES_DIR / "fzf" / "dist" / "fzf.es.js",
    "vendor/fzf/LICENSE": NODE_MODULES_DIR / "fzf" / "license.txt",
}
LIBRARY_INSTALL_HINT = (
    "run `npm ci` in .github/project-index; if they are installed, the package layout changed: update SITE_LIBRARIES"
)
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

UNREADABLE_FILE_PROBLEM = "cannot read the file: commit its deletion or restore it"
OUTSIDE_PROJECT_PROBLEM = "file outside a project, expected <theme>/<sujet>/<projet>/..."
