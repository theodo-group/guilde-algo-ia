# CLAUDE.md

Monorepo of independent projects by guild members, laid out as `<theme>/<sujet>/<projet>/`. Naming conventions and the steps to add a project: `README.md`.

## Working on a project

- Scope = the project folder. Read, edit and run only inside `<theme>/<sujet>/<projet>/`; other projects belong to other people.
- Each project is self-contained: its dependencies, config, `.gitignore` and tooling live in its own folder. Install and run from that folder.
- New project → copy `_template/` (`cp -r _template <theme>/<sujet>/<projet>`), fill its `README.md`, and add its owner line to `.github/CODEOWNERS`. Create the subject folder if missing, following the naming rules in `README.md`.
- New environment variable → add it to the project's `.env.example`, name only, no value. Real values stay in `.env`.
- Before a PR, `.github/scripts/check-structure.sh` passes (the CI runs the same script).
- Data goes in `data/`, which git ignores; the project's README says how to get it.

## Repo-level files

`README.md`, `CLAUDE.md`, `_template/` and the root `.gitignore` define the standard for everyone. Change them only when the request is about the standard itself.

## Good practice for code

The `ub-mode` skill (`.claude/skills/ub-mode/`) and its `architecture.md` are available as good practice, not a rule: no CI checks them. The repo tooling in `.github/` follows them. A project follows them only if its author says so in its README.

## Dev workflow

- Checks: the commands of `.github/workflows/checks.yml`, run from the repo root.
- Architecture rules: `.claude/skills/ub-mode/architecture.md`, only for code in `.github/` and in projects that follow `ub-mode` (see Good practice for code); they do not apply to other projects.
- Quality gates: only for code in `.github/` and in projects that follow `ub-mode` (see Good practice for code); they do not apply to other projects. From the root of the changed project (the folder with `pyproject.toml` or `package.json`, for example `.github/project-index/`), `uv run --script "$(git rev-parse --show-toplevel)/.claude/skills/ub-mode/scripts/quality.py" --base origin/<target branch> --tests <path of the project tests>`.
- Worktrees: `.claude/worktrees/`
