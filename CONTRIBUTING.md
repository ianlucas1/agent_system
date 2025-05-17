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
## Understanding and Handling Pre-commit Hooks

This project uses pre-commit hooks (defined in `.pre-commit-config.yaml`) to automatically check and sometimes fix your code before it's committed. These hooks run when you type `git commit`.

**What happens if a hook modifies files?**

Some hooks, especially linters and formatters (like Ruff when configured to fix), might change your files to correct issues. This is helpful, but can sometimes lead to a confusing commit cycle if not handled correctly:

1.  You run `git commit`.
2.  A hook runs and modifies some staged files.
3.  The commit process might then:
    *   Abort, because the files changed after being staged.
    *   Succeed, but commit the files as they were *before* the hook modified them, meaning the fixes aren't actually committed.

**How to handle this (The "add-commit-add-commit" cycle):**

If you suspect or see that hooks have modified your files after a commit attempt:

1.  **Check the status:** Run `git status`. It will show you the files modified by the hooks.
2.  **Add the changes:** Stage these new modifications: `git add -A` (or `git add <specific files>`).
3.  **Commit again:** Now, run `git commit` again.
    *   If you want to keep your original commit message, you can use: `git commit --amend --no-edit`
    *   Alternatively, just type your commit message again.
    This time, the hooks should pass without issues because the files are already in the corrected state.

**Using `git commit --no-verify` (Use with caution!):**

In rare cases, like when adding a large number of new files for the first time (e.g., an entire workspace directory) where hooks might cause repeated issues, you can temporarily bypass hooks for a single commit using:
```bash
git commit --no-verify -m "<type>: <concise summary>"
```
**Warning:** This bypasses ALL pre-commit checks for that commit. Only use this if you are confident the changes are correct and understand the risks. It's not a standard practice for day-to-day commits. After such a commit, it's good practice to run the checks manually (e.g., `pre-commit run --all-files` or `tox -e ci`) to ensure everything is still in order.

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