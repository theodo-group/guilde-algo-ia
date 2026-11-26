"""Pinned tools and thresholds of the ub-mode quality gates."""

TOOLS = {
    "crapper": (
        "https://github.com/unclebob/crapper.git",
        "6fd92c4c9bcc56efb64a2f8743d5a2993bcfd42d",
    ),
    "dryer": (
        "https://github.com/unclebob/dryer.git",
        "66ff6d21a42c04afcad89c78a80066176d1294b0",
    ),
    "mutator": (
        "https://github.com/unclebob/mutator.git",
        "a5a0cb803b66e0cdb8bf471b3b08af701d424a41",
    ),
}

CACHE_ENV = "UB_MODE_CACHE"
DEFAULT_CACHE = "~/.cache/ub-mode"
DEFAULT_BASE = "origin/main"

CRAP_THRESHOLD = "10"
DRY_THRESHOLD = "0.8"

PYTHON_SUFFIXES = {".py"}
SCRIPT_SUFFIXES = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "testdata"}
TEST_MARKERS = (".test.", ".spec.")

# The tools write here; all stay out of git through .git/info/exclude.
OUTPUT_DIRS = (".metrics/", "target/", ".coverage")

PYTHON_LCOV = "target/coverage/python/lcov.info"
# {tests} is the pytest target, the whole suite by default.
UV_COVERAGE = (
    "uv run --with coverage coverage run -m pytest -q {tests}"
    " && uv run --with coverage coverage lcov -q -o " + PYTHON_LCOV
)
# Mutants go through uv run: calling .venv/bin/python from mutator's overlay
# reads the original sources and reports surviving mutants as killed.
UV_TESTS = "uv run pytest -q -x {tests}"
# uv run per mutant is slow under parallel workers; mutator's default factor
# (10x the baseline) times out and crashes the run.
MUTATOR_TIMEOUT_FACTOR = "30"
MUTATOR_MAX_WORKERS = "2"

GATES = ("crap", "dry", "mutate")
# mutate is opt-in until it gives reliable results on uv projects.
DEFAULT_GATES = ("crap", "dry")
