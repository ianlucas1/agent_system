# Contributing to **agent_system**

Thank-you for helping improve this project!  Below is a concise, repeatable workflow that keeps the repository healthy and avoids the "untracked files" issue we occasionally hit.

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

# Run quality checks early & often
ruff check .
pytest          # includes coverage gate via pytest.ini
mypy src || true   # non-blocking for now – tighten later
bandit -q -r src   # security scan

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

# Check CI status
gh pr checks <number>

# Merge (deletes remote & local branch)
printf "y\n" | gh pr merge <number> --merge --delete-branch
```

*(Replace `<number>` with the PR number shown by GitHub.)*

---
## 3  Helper Script (optional)

You can also run `./scripts/dev_commit.sh "feat: message"` which performs steps 1 & 2 automatically (see the script for details).

---
## 4  Pre-commit Hooks (optional but recommended)

We ship a `.pre-commit-config.yaml` that runs Ruff, Bandit, and a quick test subset before each commit.  Enable it once per clone:

```bash
pip install pre-commit
pre-commit install
```

Afterwards, bad commits are blocked automatically. 