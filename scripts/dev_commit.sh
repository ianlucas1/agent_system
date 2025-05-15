#!/usr/bin/env bash
# Quick dev loop helper — run quality checks, stage all, commit, push.
# Usage: ./scripts/dev_commit.sh "feat: concise message"
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"commit message\"" >&2
  exit 1
fi

MSG="$1"

# Run fast quality checks
pip install -e .  >/dev/null 2>&1 || true
ruff check .
pytest -q
mypy src || true  # non-blocking for now
bandit -q -r src

echo "Quality checks complete. Committing…"

git add -A
if git diff --cached --quiet; then
  echo "Nothing to commit." && exit 0
fi

git commit -m "$MSG"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

git push --set-upstream origin "$CURRENT_BRANCH"

echo "Pushed to origin/$CURRENT_BRANCH" 