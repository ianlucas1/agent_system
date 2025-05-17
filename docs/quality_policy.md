# Code-Quality Ratchet

_All checks run locally first._  Every contributor must run `tox -e ci` before
pushing which executes **exactly** the same pipeline as GitHub Actions.
If it is red locally it will be red in CI.

This repository follows a *ratchet* strategy: every pull-request should leave
quality at the same level or **better** than before, but historical debt does
not block feature work.

## 1. Quality Gates

| Tool              | CI status | Commit Hook | Rule                                                                      |
|-------------------|-----------|-------------|---------------------------------------------------------------------------|
| Ruff              | blocking  | yes         | Must pass with zero errors.                                               |
| Pytest + coverage | blocking  | yes         | All tests green; ≥55% coverage overall (enforced via `pytest.ini`).       |
| Bandit            | non-block | yes         | Issues in **touched files** must be fixed or annotated (`# nosec`).       |
| Semgrep (security) | non-block | no         | High-severity findings in **touched code** must be fixed or suppressed (with justification). |
| MyPy              | non-block | yes         | Touched files must be free of *new* errors; legacy debt may remain.       |
| Actionlint (workflow) | blocking | yes | GitHub workflow YAML must pass actionlint. |

Legacy issues remain visible in the CI log but do not fail the build until the
baseline is clean.

## 2. Definition of "Touched File"

A file is considered touched when it is added or modified in the current PR.
Deletion does not trigger quality upgrades.

## 3. Debt Tracking

When you suppress a Bandit issue or add a `# type: ignore`:

1. Add an inline comment explaining **why** the suppression is safe.
2. If a full fix is sizable, open an issue using the *Technical debt* template.

The template auto-labels as `debt` so we can schedule weekly clean-up sessions.

## 4. Weekly Clean-Up

The team dedicates ~1 hour each Friday to reduce outstanding debt issues or to
chip away at remaining MyPy/Bandit warnings in untouched files.

Once the debt queue is empty **and** CI is green for the full codebase, we will
flip MyPy & Bandit to *blocking* in CI. 