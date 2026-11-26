# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Build the project index from the optional metadata block of each project README.

    uv run .github/scripts/build_index.py --check      # validate metadata only
    uv run .github/scripts/build_index.py --out _site  # write the GitHub Pages site
"""

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SITE_SRC = ROOT / ".github" / "site"
EXCLUDED = {".github", "_template"}
REQUIRED = {"titre": str, "auteurs": list, "description": str}
OPTIONAL = {"date": dt.date, "session": str, "stack": list}


def read_front_matter(readme: Path) -> dict | None:
    text = readme.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("metadata block opened with '---' but never closed")
    data = yaml.safe_load(text[4:end]) or {}
    if not isinstance(data, dict):
        raise ValueError("metadata block is not a YAML mapping")
    return data


def validate(meta: dict) -> list[str]:
    errors = []
    for key, kind in REQUIRED.items():
        if key not in meta:
            errors.append(f"missing '{key}'")
        elif not isinstance(meta[key], kind):
            errors.append(f"'{key}' must be a {kind.__name__}")
    for key, kind in OPTIONAL.items():
        if key in meta and not isinstance(meta[key], kind):
            errors.append(f"'{key}' must be a {'date (YYYY-MM-DD)' if kind is dt.date else kind.__name__}")
    for key in ("auteurs", "stack"):
        if isinstance(meta.get(key), list) and not all(isinstance(v, str) for v in meta[key]):
            errors.append(f"'{key}' must be a list of strings")
    if isinstance(meta.get("session"), str) and not meta["session"].startswith("https://"):
        errors.append("'session' must be an https:// URL")
    unknown = set(meta) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        errors.append(f"unknown keys: {', '.join(sorted(unknown))}")
    return errors


def collect() -> tuple[list[dict], list[str]]:
    projects, errors = [], []
    for readme in sorted(ROOT.glob("*/*/*/README.md")):
        rel = readme.parent.relative_to(ROOT)
        if rel.parts[0] in EXCLUDED or rel.parts[0].startswith("."):
            continue
        try:
            meta = read_front_matter(readme)
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"{rel}/README.md: {exc}")
            continue
        if meta is None:
            continue  # metadata is optional: the project is simply not indexed
        problems = validate(meta)
        if problems:
            errors.extend(f"{rel}/README.md: {p}" for p in problems)
            continue
        theme, sujet, projet = rel.parts
        projects.append({
            "theme": theme,
            "sujet": sujet,
            "projet": projet,
            "path": str(rel),
            "titre": meta["titre"],
            "auteurs": meta["auteurs"],
            "description": meta["description"],
            "date": meta["date"].isoformat() if "date" in meta else None,
            "session": meta.get("session"),
            "stack": meta.get("stack", []),
        })
    return projects, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="validate metadata only")
    group.add_argument("--out", type=Path, help="directory to write the site into")
    args = parser.parse_args()

    projects, errors = collect()
    for error in errors:
        print(f"::error::{error}")
    if errors:
        print("Metadata format: README.md, section Métadonnées.")
        return 1
    print(f"{len(projects)} indexed project(s)")

    if args.out:
        if args.out.exists():
            shutil.rmtree(args.out)
        shutil.copytree(SITE_SRC, args.out)
        (args.out / "projects.json").write_text(
            json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
