# Contributing to **agent_system**

Thank-you for helping improve this project!  Below is a concise, repeatable workflow that keeps the repository healthy and avoids the "untracked files" issue we occasionally hit.

👉  For the philosophy behind these gates (and how we handle legacy Bandit/MyPy
    findings) see `docs/quality_policy.md`.

---
## 1  Local Development Loop

```bash
# Sync and create a topic branch
git checkout main
git pull --ff-only origin main

git checkout -b feat/<topic>

# Make your changes…
#    • Write code
#    • Add / update tests
#    • Update docs

# Static style / linting – must pass
ruff check .

# Tests & coverage – must pass
pytest -q          # coverage gate (>=55% coverage) via pytest.ini

# Static typing – **non-blocking in CI** for now but please fix errors locally
mypy src || true   # remove `|| true` once codebase is type-clean

# Security scan – advisory
bandit -q -r src

# Additional static analysis – advisory
semgrep --config auto -q .

# Ensure package is installed in editable mode once per clone
pip install -e .

# Stage *everything* (tracked & untracked) so nothing is missed
# The -A flag catches new files you created.
git add -A

# Commit and push
git commit -m "<type>: <concise summary>"
git push --set-upstream origin $(git branch --show-current)
```

---
## 2  Create a Pull Request (GitHub CLI)

```bash
# Draft PR – auto-fills title & body from your commit history
gh pr create --base main --head $(git branch --show-current) --draft --fill

# When ready for review
gh pr ready <number>

# Check CI status – wait until all checks are green (✔)
gh pr checks <number> --watch

# Merge **only after CI passes** (also deletes remote & local branch)
printf "y\n" | gh pr merge <number> --merge --delete-branch

# Post-merge tidy-up
#   • Switch back to main and pull latest
#   • Delete the now-merged feature branch locally if it was **not** auto-deleted

git checkout main
git pull --ff-only origin main
git branch -d feat/<topic>
```

After cloning the repo run:

```bash
pre-commit install   # installs the git hooks (runs Ruff, Bandit, pytest-quick)
```

Before you push run **exactly** the same pipeline that GitHub CI does:

```bash
tox -e ci  # runs Ruff (full repo), pytest (minus slow tests), coverage
```

If `tox -e ci` passes locally your PR will be green – CI will abort after the fast
Ruff job if any lint error remains, saving minutes and tokens.