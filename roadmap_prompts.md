<!--
⚠️  THIS FILE IS AUTO-GENERATED. DO NOT EDIT BY HAND.
Run:  python scripts/build_prompts.py > roadmap_prompts.md
-->

# Roadmap Prompts

Each section below is a stand-alone prompt that can be copy-pasted into a new
Cursor IDE chat session. Begin with Task 1 and proceed sequentially. A fresh
agent instance should be used for every task to avoid context bloat.

## Task 1: Purge Legacy Crypto Artifacts (branch `cleanup/eth-vestiges`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 1` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b cleanup/eth-vestiges
- 1.1 `git rm -r reports exec_requests`
- 1.3 Edit pyproject.toml: replace
- 1.5 Update README.md top title to `"Multi-Agent Chatbot GUI"` and eliminate any remaining crypto-specific wording.
- 1.6 `pre-commit run --all-files` to lint all modified files.
- 1.7 `pytest -q` to ensure tests still pass.
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "task-1: purge-legacy-crypto-artifacts"
git push --set-upstream origin cleanup/eth-vestiges
gh pr create --base main --head cleanup/eth-vestiges --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d cleanup/eth-vestiges
```
### Debrief template

```markdown
## Debrief for Task 1

- Task Completed: Task 1: Purge Legacy Crypto Artifacts (branch `cleanup/eth-vestiges`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 1` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_1.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 1 complete```

---

## Task 2: Patch CI Workflow (branch `ci/metrics-job`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 2` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_2_step_1_block1.sh`

### Steps to perform

- git checkout -b ci/metrics-job
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_2_step_1_block1.sh`
- 2.1 Save the provided ci_patch.diff to a temp file (e.g. `patch.tmp`) and apply it:
- 2.2 Verify the GitHub Actions workflow was updated: `grep -n "metrics:" .github/workflows/ci.yml` should show the new metrics job added.
- 2.3 Run a local CI test (using `act`): `act -j metrics` and expect exit code 0 within \~60s.
- 2.4 `git add .github/workflows/ci.yml && git commit -m "ci: add metrics sanity job"`
- If the `act` CLI is not available, install it (e.g., `brew install act` or download the binary from https://github.com/nektos/act) and then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "ci: add metrics sanity job"
git push --set-upstream origin ci/metrics-job
gh pr create --base main --head ci/metrics-job --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d ci/metrics-job
```
### Debrief template

```markdown
## Debrief for Task 2

- Task Completed: Task 2: Patch CI Workflow (branch `ci/metrics-job`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 2` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_2.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 2 complete```

---

## Task 3: Introduce UsageLogger (branch `feature/usage-logger`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 3` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_3_step_1_scaffold.py`
  - `agent_workspace/task_3_step_2_block2.py`
  - `agent_workspace/task_3_step_3_block3.py`

### Steps to perform

- git checkout -b feature/usage-logger
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_3_step_1_scaffold.py`, `agent_workspace/task_3_step_2_block2.py`, `agent_workspace/task_3_step_3_block3.py`
- 3.1 Create file `src/shared/usage_logger.py` with the following scaffold:
- 3.2 In `src/llm/openai_client.py` and `src/llm/gemini_client.py`, import the logger and increment counts after each API call. For example:
- 3.3 If `ENABLE_METRICS=1`: inside `UsageLogger.inc()`, also increment Prometheus counters. For example:
- 3.4 Add unit test tests/test\_usage\_logger.py: call `UsageLogger.inc("openai", 5)`, then force a flush (e.g. sleep slightly and call `UsageLogger._flush()`), and assert the last line of `usage_log.json` contains `"openai": 5`.
- 3.5 `git add -A && git commit -m "feat: persistent token UsageLogger"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: persistent token UsageLogger"
git push --set-upstream origin feature/usage-logger
gh pr create --base main --head feature/usage-logger --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/usage-logger
```
### Debrief template

```markdown
## Debrief for Task 3

- Task Completed: Task 3: Introduce UsageLogger (branch `feature/usage-logger`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 3` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_3.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 3 complete```

---

## Task 4: Implement ChatHistoryManager (branch `feature/persistent-history`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 4` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_4_step_1_scaffold.py`
  - `agent_workspace/task_4_step_2_scaffold.py`
  - `agent_workspace/task_4_step_3_block3.py`

### Steps to perform

- git checkout -b feature/persistent-history
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_4_step_1_scaffold.py`, `agent_workspace/task_4_step_2_scaffold.py`, `agent_workspace/task_4_step_3_block3.py`
- 4.1 Create `src/shared/history.py` with basic persistent history API:
- 4.2 Modify `ChatSession.send()` logic: after each user or agent message is processed, call `history.append(role, content)` to save it (use `"user"` or `"openai"/"gemini"` as role).
- 4.3 On app startup in `src/interfaces/gui.py`, pre-load past messages into session state:
- 4.4 Add a Clear Chat button in the sidebar to wipe history:
- 4.5 Create tests/test\_history.py to verify that saving and loading history works (append some messages, reset, etc.).
- 4.6 `git add -A && git commit -m "feat: persistent chat history storage"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: persistent chat history storage"
git push --set-upstream origin feature/persistent-history
gh pr create --base main --head feature/persistent-history --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/persistent-history
```
### Debrief template

```markdown
## Debrief for Task 4

- Task Completed: Task 4: Implement ChatHistoryManager (branch `feature/persistent-history`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 4` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_4.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 4 complete```

---

## Task 5: Sidebar Token Dashboard (branch `ui/token-dashboard`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 5` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_5_step_1_block1.py`

### Steps to perform

- git checkout -b ui/token-dashboard
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_5_step_1_block1.py`
- 5.1 Extend the Streamlit sidebar to show token usage stats. For example, insert under the model selector:
- 5.2 Enable auto-refresh of this panel (every \~5 seconds). E.g., use `st.experimental_rerun()` or `st.sidebar.empty().add_static()` trick to periodically refresh.
- 5.3 `git add -u && git commit -m "ui: add live token usage sidebar"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "ui: add live token usage sidebar"
git push --set-upstream origin ui/token-dashboard
gh pr create --base main --head ui/token-dashboard --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d ui/token-dashboard
```
### Debrief template

```markdown
## Debrief for Task 5

- Task Completed: Task 5: Sidebar Token Dashboard (branch `ui/token-dashboard`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 5` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_5.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 5 complete```

---

## Task 6: CostMonitor (Billing Polling) (branch `feature/cost-monitor`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 6` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_6_step_1_scaffold.py`
  - `agent_workspace/task_6_step_2_block2.py`

### Steps to perform

- git checkout -b feature/cost-monitor
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_6_step_1_scaffold.py`, `agent_workspace/task_6_step_2_block2.py`
- 6.1 Create `src/shared/cost_monitor.py` to periodically fetch API billing info:
- 6.2 Import `shared.cost_monitor` at app startup (just importing will start the background polling thread).
- 6.3 In the sidebar, display the cost info if available. For example:
- 6.4 Write tests for CostMonitor with a mocked `requests.get` to return sample JSON (e.g. `{"total_usage": 12345}`) and verify the cached values.
- 6.5 `git add -A && git commit -m "feat: cost monitoring (OpenAI & Gemini billing)"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: cost monitoring (OpenAI & Gemini billing)"
git push --set-upstream origin feature/cost-monitor
gh pr create --base main --head feature/cost-monitor --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/cost-monitor
```
### Debrief template

```markdown
## Debrief for Task 6

- Task Completed: Task 6: CostMonitor (Billing Polling) (branch `feature/cost-monitor`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 6` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_6.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 6 complete```

---

## Task 7: Streamlit GUI Redesign (Dark Theme) (branch `ui/dark-redesign`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 7` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_7_step_1_block1.toml`

### Steps to perform

- git checkout -b ui/dark-redesign
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_7_step_1_block1.toml`
- 7.1 Create a Streamlit config file to enforce dark mode. In .streamlit/config.toml:
- 7.2 *(Optional)* Rename `src/interfaces/gui.py` to `src/interfaces/app.py` for clarity. If renamed, update any entry points (e.g., in pyproject.toml `[project.scripts]` for the CLI/GUI command).
- 7.3 Refactor the GUI code for the new layout:
- 7.4 Add a copy-to-clipboard button for any code blocks in agent responses. (Inject a small JS snippet in `st.markdown` that appends a "Copy" button to `<pre><code>` elements.)
- 7.5 `git add -A && git commit -m "ui: modern dark-theme chat interface redesign"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "ui: modern dark-theme chat interface redesign"
git push --set-upstream origin ui/dark-redesign
gh pr create --base main --head ui/dark-redesign --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d ui/dark-redesign
```
### Debrief template

```markdown
## Debrief for Task 7

- Task Completed: Task 7: Streamlit GUI Redesign (Dark Theme) (branch `ui/dark-redesign`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 7` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_7.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 7 complete```

---

## Task 8: Metrics GUI Hook (branch `metrics/gui-hook`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 8` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_8_step_1_block1.py`

### Steps to perform

- git checkout -b metrics/gui-hook
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_8_step_1_block1.py`
- 8.1 If Prometheus metrics are enabled (`ENABLE_METRICS=1`), add a quick link in the sidebar to the metrics endpoint. For example:
- 8.2 `git add -u && git commit -m "feat: add Prometheus /metrics link in GUI"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: add Prometheus /metrics link in GUI"
git push --set-upstream origin metrics/gui-hook
gh pr create --base main --head metrics/gui-hook --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d metrics/gui-hook
```
### Debrief template

```markdown
## Debrief for Task 8

- Task Completed: Task 8: Metrics GUI Hook (branch `metrics/gui-hook`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 8` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_8.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 8 complete```

---

## Task 9: README & Docs Refresh (branch `docs/refresh`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 9` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.

- The following artifact file(s) are provided in `agent_workspace/`:
  - `agent_workspace/task_9_step_1_block1.sh`

### Steps to perform

- git checkout -b docs/refresh
- Read the content of the following artifact file(s) listed under "Inputs required": `agent_workspace/task_9_step_1_block1.sh`
- 9.2 Update docs/index.md (MkDocs home) to match the new branding and features described in the README.
- 9.3 Run `mkdocs build --strict` to ensure documentation builds without warnings or errors.
- 9.4 `git add -A && git commit -m "docs: overhaul README and index for new scope"`
- 10.1 `pre-commit run --all-files` to run all linters/formatters on the entire codebase.
- 10.2 `pytest -q` and confirm the coverage report is ≥ 55% (the minimum coverage gate).
- 10.3 Perform a manual smoke test of the app:
- 10.4 Tag the release:
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "docs: overhaul README and index for new scope"
git push --set-upstream origin docs/refresh
gh pr create --base main --head docs/refresh --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d docs/refresh
```
### Debrief template

```markdown
## Debrief for Task 9

- Task Completed: Task 9: README & Docs Refresh (branch `docs/refresh`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 9` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_9.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 9 complete```

---

## Task 11: Integrate Chroma Vector Memory (branch `feature/memory-chroma`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 11` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b feature/memory-chroma
- 11.1 Append `chromadb` to `requirements.txt` and install it (`pip install chromadb`).
- 11.2 Create `src/tools/memory.py` implementing a memory tool using Chroma. Initialize a local Chroma client and collection (e.g. `agent_memory`) at module import.
- 11.3 Implement new memory commands: `/remember <text>` to embed and store the given text in the vector DB, and `/recall <query>` to perform a similarity search and return relevant stored content. Register these in the ToolRegistry (so the agent can call them via `ToolRegistry.get("memory").execute(...)`).
- 11.4 Add unit tests for memory persistence: e.g., use `/remember` to add a sample fact, then call `/recall` with a related query and assert that the fact is retrieved. (Use a small embedding model or stub for determinism in tests.)
- 11.5 Run `pre-commit run --all-files` and then `pytest -q` to ensure lint and tests pass (update tests if needed to keep coverage ≥ 55%).
- 11.6 `git add -A && git commit -m "feat: long-term memory via Chroma vector DB"`
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: long-term memory via Chroma vector DB"
git push --set-upstream origin feature/memory-chroma
gh pr create --base main --head feature/memory-chroma --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/memory-chroma
```
### Debrief template

```markdown
## Debrief for Task 11

- Task Completed: Task 11: Integrate Chroma Vector Memory (branch `feature/memory-chroma`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 11` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_11.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 11 complete```

---

## Task 12: Integrate Playwright Browser Tool (branch `feature/browser-tool`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 12` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b feature/browser-tool
- 12.1 Append `playwright` to `requirements.txt` and install it. Then run `playwright install` to download browser engines for headless operation.
- 12.2 Create `src/tools/browser.py` containing a `BrowserTool` class. Use `playwright.sync_playwright()` (in setup) to launch a headless browser context (Chromium). Implement a method like `open_url(url: str) -> str` that navigates to the URL and returns the page text (you can use `page.content()` or similar).
- 12.3 Register a new slash command `/browse <URL>` that instantiates `BrowserTool` (or uses a singleton instance) and returns the fetched page content or a summary of it. Include basic error handling for navigation timeouts or invalid URLs.
- 12.4 Write a basic test for the browser tool (mark it with `@pytest.mark.slow` if it uses actual browsing): e.g., use a local HTML file or a lightweight public page and assert that `/browse <file_or_url>` returns a snippet of expected text.
- 12.5 Run all linters and tests (`pre-commit` and `pytest`) to ensure nothing regresses.
- 12.6 `git add -A && git commit -m "feat: web browsing capability via Playwright"`
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: web browsing capability via Playwright"
git push --set-upstream origin feature/browser-tool
gh pr create --base main --head feature/browser-tool --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/browser-tool
```
### Debrief template

```markdown
## Debrief for Task 12

- Task Completed: Task 12: Integrate Playwright Browser Tool (branch `feature/browser-tool`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 12` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_12.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 12 complete```

---

## Task 13: Integrate DuckDB Embedded Database (branch `feature/analytics-db`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 13` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b feature/analytics-db
- 13.1 Append `duckdb` to `requirements.txt` and install it (`pip install duckdb`).
- 13.2 Create `src/tools/db_tool.py` with a `DatabaseTool` (DuckDB-backed). On initialization, open or create a DuckDB database file (e.g. `agent_workspace/analytics.duckdb`).
- 13.3 Implement a method `run_query(sql: str) -> str` that executes the given SQL on the DuckDB connection and returns the results (e.g., as a CSV string or formatted table). Support read-only queries (you may allow CREATE/INSERT if needed to log data).
- 13.4 Register a slash command `/query <SQL>` that passes the SQL string to the `DatabaseTool` and returns the output or any error message. Consider restricting potentially destructive commands in this context.
- 13.5 Add tests for the DB tool: for example, pre-load a small table, then use `/query` to select from it and verify the expected output. Also test that a malformed query returns an error string.
- 13.6 Run `pre-commit` and `pytest -q` to ensure the new code is linted and tested.
- 13.7 `git add -A && git commit -m "feat: embedded DuckDB for analytics queries"`
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: embedded DuckDB for analytics queries"
git push --set-upstream origin feature/analytics-db
gh pr create --base main --head feature/analytics-db --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/analytics-db
```
### Debrief template

```markdown
## Debrief for Task 13

- Task Completed: Task 13: Integrate DuckDB Embedded Database (branch `feature/analytics-db`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 13` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_13.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 13 complete```

---

## Task 14: Integrate APScheduler for Task Scheduling (branch `feature/scheduler`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 14` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b feature/scheduler
- 14.1 Append `apscheduler` to `requirements.txt` and install it.
- 14.2 Create `src/tools/scheduler.py`. Initialize a `BackgroundScheduler` (e.g., `sched = BackgroundScheduler()` and `sched.start()`) when the app launches.
- 14.3 Implement a function (or Tool method) `schedule_task(command: str, trigger: dict)` that uses `sched.add_job` to schedule execution of a given slash command or tool function at a later time or on an interval. For example, allow usage like `/schedule "every 5m" "/browse example.com"`.
- 14.4 Register a slash command `/schedule <cron_or_interval> <command>` that parses the interval (e.g., using APScheduler's CRON or interval syntax) and schedules the specified command. Provide user feedback confirming the scheduling.
- 14.5 Add a test (could be an integration test marked slow) that schedules a one-off job with a short delay (e.g., 2 seconds), then uses a callback or shared flag to verify the job ran. Use `monkeypatch` or a dummy tool to avoid real sleep delays in the test.
- 14.6 Run `pre-commit` and `pytest -q` to ensure all quality gates pass (scheduler might spawn threads; ensure tests handle that deterministically or mark appropriately).
- 14.7 `git add -A && git commit -m "feat: background task scheduling via APScheduler"`
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: background task scheduling via APScheduler"
git push --set-upstream origin feature/scheduler
gh pr create --base main --head feature/scheduler --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/scheduler
```
### Debrief template

```markdown
## Debrief for Task 14

- Task Completed: Task 14: Integrate APScheduler for Task Scheduling (branch `feature/scheduler`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 14` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_14.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 14 complete```

---

## Task 15: Integrate PyAutoGUI for OS Automation (branch `feature/gui-automation`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 15` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b feature/gui-automation
- 15.1 Append `pyautogui` to `requirements.txt` and install it (`pip install pyautogui`).
- 15.2 Create `src/tools/rpa.py` implementing basic RPA (robotic process automation) tools. For example, define `type_text(text: str)` to simulate keyboard typing (`pyautogui.write(text)`) and `capture_screen(path: str)` to take a screenshot (`pyautogui.screenshot(path)`).
- 15.3 Register slash commands for these actions, e.g.: `/type "<text>"` to type text into the active window, and `/screenshot <filename>` to save a screenshot. Include safeguards: PyAutoGUI should not run if no display is available (you can detect CI via env and no-op or raise a friendly error).
- 15.4 Implement a dry-run mode for CI: if an env var like `CI=true` is detected, have the RPA functions log an action instead of performing it (to allow testing without actual GUI interaction).
- 15.5 Add a test for RPA tooling using the dry-run mode or monkeypatch PyAutoGUI: verify that calling `/type "hello"` results in a log or state indicating the text "hello" would be typed, and that `/screenshot` attempts to write a file (you can simulate the file write).
- 15.6 Run `pre-commit run --all-files` and `pytest -q` to ensure the RPA integration does not break any existing tests (mark RPA tests to skip in headless CI if needed).
- 15.7 `git add -A && git commit -m "feat: OS automation via PyAutoGUI (RPA)"`
- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: OS automation via PyAutoGUI (RPA)"
git push --set-upstream origin feature/gui-automation
gh pr create --base main --head feature/gui-automation --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d feature/gui-automation
```
### Debrief template

```markdown
## Debrief for Task 15

- Task Completed: Task 15: Integrate PyAutoGUI for OS Automation (branch `feature/gui-automation`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 15` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_15.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 15 complete```

---

## Task 16: Define Coordination Schema (branch `coord/schema-keys`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 16` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/schema-keys
- 16.1 Create `src/coordination/schema.py` defining structured artifact classes: `Plan`, `CodePatch`, `TestReport`, `Review`. Implement each as a dataclass or simple class with fields capturing the essential data (e.g., Plan might include a list of steps; CodePatch contains file diffs; TestReport has status and log; Review has final verdict and comments). Include `to_json()`/`from_json()` methods for serialization.
- 16.2 Extend the ContextBus to support new coordination keys. In `src/shared/context_bus.py`, add enum entries or constants for each artifact (e.g., `plan_draft`, `code_patch`, `test_report`, `final_review`). This ensures a canonical place in the shared state for each step's output.
- 16.3 Create tests/unit/test\_schema.py to verify the new schema classes. For each class, construct an instance, round-trip it via `to_json()`/`from_json()`, and assert the result matches the original.
- 16.4 Run `pytest -q tests/unit/test_schema.py` and confirm all tests pass.
- 16.5 `git add -A && git commit -m "feat: coordination schema & ContextBus keys"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: coordination schema & ContextBus keys"
git push --set-upstream origin coord/schema-keys
gh pr create --base main --head coord/schema-keys --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/schema-keys
```
### Debrief template

```markdown
## Debrief for Task 16

- Task Completed: Task 16: Define Coordination Schema (branch `coord/schema-keys`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 16` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_16.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 16 complete```

---

## Task 17: Add SOP Prompt Templates (branch `coord/prompts`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 17` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/prompts
- 17.1 Create directory `src/coordination/prompts/` and add role-specific prompt files: planner.txt, coder.txt, reviewer.txt.
- 17.2 Ensure these prompt files are loaded by the agent system when spawning the respective agents (for example, modify the agent initialization or MultiAgentTool to fetch the content of these files as the `role_prompt`).
- 17.3 (No direct code to test here, but) do a quick manual check that the files are readable and contain no syntax errors (the content will be indirectly validated when the agents produce the expected structured outputs).
- 17.4 `git add -A && git commit -m "feat: add SOP prompts for Planner, Coder, Reviewer roles"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: add SOP prompts for Planner, Coder, Reviewer roles"
git push --set-upstream origin coord/prompts
gh pr create --base main --head coord/prompts --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/prompts
```
### Debrief template

```markdown
## Debrief for Task 17

- Task Completed: Task 17: Add SOP Prompt Templates (branch `coord/prompts`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 17` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_17.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 17 complete```

---

## Task 18: Implement Coordinator FSM (branch `coord/orchestrator`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 18` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/orchestrator
- 18.1 Create `src/coordination/orchestrator.py` with a new `Coordinator` class. Define an enum of states or steps (e.g., `CoordStage` with values PLANNING, CODING, TESTING, REVIEW).
- 18.2 Implement `Coordinator.run(user_task: str) -> Review` to execute the SOP workflow deterministically:
- 18.3 Register a new chat command for this pipeline. For now, use a separate trigger (e.g., `/workflow2 <task>`) in the ToolRegistry or command parser that will instantiate `Coordinator` and call `run(task)`. (This allows side-by-side testing with the legacy `/workflow` command initially.)
- 18.4 Ensure each agent invocation uses only the relevant context: e.g., the Coder sees just the Plan (not the entire chat history), the Reviewer sees Plan+Patch+Report. Leverage the ContextBus and the structured outputs to avoid prompt injection between agents.
- 18.5 Run `pytest -q` to confirm no existing unit tests break due to these additions (adjust or skip legacy workflow tests if necessary). The new coordinator will be tested in Task 22.
- 18.6 `git add -A && git commit -m "feat: deterministic Planner→Coder→QualityGate→Reviewer workflow"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: deterministic Planner→Coder→QualityGate→Reviewer workflow"
git push --set-upstream origin coord/orchestrator
gh pr create --base main --head coord/orchestrator --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/orchestrator
```
### Debrief template

```markdown
## Debrief for Task 18

- Task Completed: Task 18: Implement Coordinator FSM (branch `coord/orchestrator`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 18` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_18.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 18 complete```

---

## Task 19: Integrate QualityGate Hook (branch `coord/quality-gate`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 19` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/quality-gate
- 19.1 Append `semgrep` to the development requirements (e.g., add to `requirements-dev.txt` and ensure it's installed in CI) to include static security scanning.
- 19.2 Create `src/coordination/quality_gate.py` with a function `run_gate(work_dir: Path) -> dict`. This function will execute all quality checks within the given temporary workspace:
- 19.3 Integrate this QualityGate into the Coordinator (Task 18): after applying the code patch in the CODING step, call `run_gate(temp_workspace)`. If the returned status is "FAIL", record the failure info and allow the Coordinator to invoke a fix (retry the Coder agent) if `max_retries` > 0 (to be implemented in Task 23).
- 19.4 Create tests/unit/test\_quality\_gate.py to unit-test the quality gate logic. For example, in a temp directory, write a sample file with an obvious lint error or failing test, then call `run_gate(temp_dir)` and assert that the returned `status` is "FAIL" and `qa_output` contains the expected error message. Also test a scenario with no issues to confirm a "PASS".
- 19.5 Run `pytest -q tests/unit/test_quality_gate.py` to ensure the QualityGate function behaves as expected in both pass and fail scenarios.
- 19.6 `git add -A && git commit -m "feat: integrate QualityGate checks into coordination flow"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: integrate QualityGate checks into coordination flow"
git push --set-upstream origin coord/quality-gate
gh pr create --base main --head coord/quality-gate --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/quality-gate
```
### Debrief template

```markdown
## Debrief for Task 19

- Task Completed: Task 19: Integrate QualityGate Hook (branch `coord/quality-gate`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 19` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_19.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 19 complete```

---

## Task 20: Add Coordination Metrics (branch `coord/metrics`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 20` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/metrics
- 20.1 Extend MetricsManager (in `src/shared/metrics.py`) with new Prometheus counters for the coordination pipeline:
- 20.2 In the Coordinator workflow (Task 18), hook into these metrics:
- 20.3 Manually test metrics output (if possible): run the app with metrics enabled and execute a sample `/workflow2` task. Then visit the metrics endpoint (`/metrics`) and verify that the new counters (e.g., `coord_agent_calls_total`) are present and increasing.
- 20.4 `git add -u && git commit -m "feat: add Prometheus counters for coordination roles"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: add Prometheus counters for coordination roles"
git push --set-upstream origin coord/metrics
gh pr create --base main --head coord/metrics --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/metrics
```
### Debrief template

```markdown
## Debrief for Task 20

- Task Completed: Task 20: Add Coordination Metrics (branch `coord/metrics`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 20` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_20.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 20 complete```

---

## Task 21: GUI Toggle for Coordination v2 (branch `coord/gui-toggle`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 21` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/gui-toggle
- 21.1 Add a user-facing option in the GUI to switch on the new coordination pipeline. For example, in the sidebar settings, include a checkbox: "Use Coordinated Workflow (SOP mode)".
- 21.2 In the command handling logic (where `/workflow` is parsed), check the state of this toggle. If the SOP mode is enabled (`True`), route the `/workflow <task>` command to use the new `Coordinator.run(task)` (Task 18) instead of the old `WorkflowTool.execute(...)`. If the toggle is off, fall back to the legacy workflow for backward compatibility.
- 21.3 Update any on-screen help or documentation in the app UI to reflect this option (e.g., a tooltip or sidebar note that enabling SOP mode will orchestrate Planner→Coder→QA→Reviewer automatically).
- 21.4 Test in the Streamlit GUI: run with the new setting off and on. With it on, issue a `/workflow <task>` command and observe that the multi-agent sequence runs (Plan/Code/QA/Review messages appear). With it off, ensure the old behavior (if still supported) runs.
- 21.5 `git add -u && git commit -m "feat: GUI option to enable SOP coordination pipeline"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: GUI option to enable SOP coordination pipeline"
git push --set-upstream origin coord/gui-toggle
gh pr create --base main --head coord/gui-toggle --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/gui-toggle
```
### Debrief template

```markdown
## Debrief for Task 21

- Task Completed: Task 21: GUI Toggle for Coordination v2 (branch `coord/gui-toggle`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 21` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_21.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 21 complete```

---

## Task 22: End-to-End Coordination Test (branch `coord/e2e-tests`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 22` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/e2e-tests
- 22.1 Write an integration test covering the entire coordinated workflow. In tests/e2e/test\_coordination\_pipeline.py:
- 22.2 Mark this test with `@pytest.mark.slow` to exclude it from regular CI runs due to time and API usage (it will run the actual LLM calls unless those are stubbed/mocked). If possible, stub out the LLM agents with deterministic fake outputs to run this test purely offline.
- 22.3 Execute `pytest -q tests/e2e/test_coordination_pipeline.py` locally to verify the happy-path scenario works end-to-end.
- 22.4 `git add tests/e2e/test_coordination_pipeline.py && git commit -m "test: add end-to-end coordination pipeline test"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "test: add end-to-end coordination pipeline test"
git push --set-upstream origin coord/e2e-tests
gh pr create --base main --head coord/e2e-tests --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/e2e-tests
```
### Debrief template

```markdown
## Debrief for Task 22

- Task Completed: Task 22: End-to-End Coordination Test (branch `coord/e2e-tests`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 22` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_22.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 22 complete```

---

## Task 23: Add Retry and Budget Guards (branch `coord/retries-budget`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 23` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/retries-budget
- 23.1 Augment the `Coordinator` (Task 18) with robustness features:
- 23.2 Implement budget checks in `Coordinator.run()`: before invoking each agent, compare the cumulative tokens used (accessible via UsageLogger or MetricsManager) against a threshold (maybe configurable via an environment variable or passed-in parameter). If the next call would exceed the budget, skip that call and instead produce a Review output indicating the task was aborted due to budget limits.
- 23.3 Add/adjust tests for these scenarios:
- 23.4 Run `pytest -q` for the relevant test suite and confirm all new logic is covered and passing. Confirm that overall test coverage is still above the required threshold.
- 23.5 `git add -u && git commit -m "feat: add retry limit and budget guardrails to Coordinator"`

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "feat: add retry limit and budget guardrails to Coordinator"
git push --set-upstream origin coord/retries-budget
gh pr create --base main --head coord/retries-budget --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/retries-budget
```
### Debrief template

```markdown
## Debrief for Task 23

- Task Completed: Task 23: Add Retry and Budget Guards (branch `coord/retries-budget`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 23` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_23.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 23 complete```

---

## Task 24: Security Sanitization (branch `coord/security-sanitization`)

You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.

### Inputs required

- Section `### 24` of `consolidated_development_roadmap.md`.

- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.


### Steps to perform

- git checkout -b coord/security-sanitization
- 24.1 Implement a sanitization utility to scrub potentially malicious content from agent outputs before they are reused. For example, create `coordination/util.py` with a function `sanitize_json(text: str) -> str` that removes known prompt injection patterns (e.g., any occurrence of `"Ignore previous instructions"` or similar phrases) from the given text.
- 24.2 Apply this sanitization step at each hand-off point in the Coordinator:
- 24.3 Add unit tests for `sanitize_json`. Include cases like a string containing `"<|Ignore previous instructions|>"` (or other prompt injection samples) and ensure the function strips or neutralizes them. Also verify it doesn't alter innocent content.
- 24.4 Run `

### Do-Not-Stop-Until checklist

- All code / docs edits are applied.

- Quality gates pass: `ruff`, `pytest -q`, etc.

- GitHub workflow executed (see snippet below).

- Debrief block posted in this chat using the template.

### GitHub CLI workflow (copy/paste)

```bash
git add -A
git commit -m "task-24: security-sanitization"
git push --set-upstream origin coord/security-sanitization
gh pr create --base main --head coord/security-sanitization --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf "y\n" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d coord/security-sanitization
```
### Debrief template

```markdown
## Debrief for Task 24

- Task Completed: Task 24: Security Sanitization (branch `coord/security-sanitization`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```
### Persistence actions

After you paste the debrief above, also **append** `Task 24` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).

Save the same debrief block to `agent_workspace/debrief_task_24.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.

When **everything** above is complete, reply only with:
```success: Task 24 complete```

---

