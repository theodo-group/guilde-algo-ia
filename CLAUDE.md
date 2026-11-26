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
