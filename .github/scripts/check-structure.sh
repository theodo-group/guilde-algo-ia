#!/usr/bin/env bash
# Checks the repo standard on tracked files. Run from the repo root.
set -uo pipefail

MAX_BYTES=$((10 * 1024 * 1024))
NAME_RE='^[a-z0-9]+(-[a-z0-9]+)*$'
errors=0
fail() { echo "::error::$1"; errors=$((errors + 1)); }

while IFS= read -r f; do
  base=$(basename "$f")
  if [[ "$base" == .env || ( "$base" == .env.* && "$base" != .env.example ) ]]; then
    fail "$f: secret file committed, keep it local and list its variables in .env.example"
  fi
  size=$(wc -c < "$f")
  if (( size > MAX_BYTES )); then
    fail "$f: $((size / 1024 / 1024)) MB, over the 10 MB limit (put data in data/, which is not versioned)"
  fi
done < <(git ls-files)

# Projects are the tracked folders at depth 3: <theme>/<sujet>/<projet>/
projects=$(git ls-files | grep -vE '^(\.claude|\.github|_template)/' | awk -F/ 'NF > 3 { print $1 "/" $2 "/" $3 }' | sort -u)
for p in $projects; do
  IFS=/ read -r theme sujet projet <<< "$p"
  for part in "$theme" "$sujet" "$projet"; do
    [[ "$part" =~ $NAME_RE ]] || fail "$p: '$part' is not kebab-case (lowercase, digits, dashes)"
  done
  git ls-files --error-unmatch "$p/README.md" > /dev/null 2>&1 || fail "$p: missing README.md"
  grep -qF "/$p/" .github/CODEOWNERS || fail "$p: missing owner line in .github/CODEOWNERS"
done

# Files sitting directly in a theme or subject folder, outside any project
while IFS= read -r f; do
  fail "$f: file outside a project, expected <theme>/<sujet>/<projet>/..."
done < <(git ls-files | grep -vE '^(\.claude|\.github|_template)/' | awk -F/ 'NF == 2 || NF == 3')

if (( errors > 0 )); then
  echo "$errors problem(s) found. Rules: README.md, section Conventions."
  exit 1
fi
echo "Structure OK"
