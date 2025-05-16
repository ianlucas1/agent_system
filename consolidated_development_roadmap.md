# consolidated_development_roadmap.md 

## agent_system [https://github.com/ianlucas1/agent_system.git]

## Phase 1: Codebase Cleanup and Core Improvements (Release v0.2.0)

### 1  Purge Legacy Crypto Artifacts  → branch `cleanup/eth-vestiges`

* **1.1** `git rm -r reports exec_requests`
* **1.3** Edit **pyproject.toml**: replace
  → `description = "Multi-Agent Chat GUI"`.
* **1.5** Update **README.md** top title to `"Multi-Agent Chatbot GUI"` and eliminate any remaining crypto-specific wording.
* **1.6** `pre-commit run --all-files` to lint all modified files.
* **1.7** `pytest -q` to ensure tests still pass.

### 2  Patch CI Workflow  → branch `ci/metrics-job`

* **2.1** Save the provided **ci\_patch.diff** to a temp file (e.g. `patch.tmp`) and apply it:

  ```bash
  git apply patch.tmp
  ```
* **2.2** Verify the GitHub Actions workflow was updated: `grep -n "metrics:" .github/workflows/ci.yml` should show the new **metrics** job added.
* **2.3** Run a local CI test (using `act`): `act -j metrics` and expect exit code 0 within \~60s.
* **2.4** `git add .github/workflows/ci.yml && git commit -m "ci: add metrics sanity job"`

### 3  Introduce UsageLogger  → branch `feature/usage-logger`

* **3.1** Create file `src/shared/usage_logger.py` with the following scaffold:

  ```python
  import json, threading, time, pathlib
  LOG_PATH = pathlib.Path("agent_workspace/usage_log.json")
  FLUSH_SEC = 60

  class UsageLogger:
      _totals = {"openai": 0, "gemini": 0}
      _accum  = {"openai": 0, "gemini": 0}

      @classmethod
      def inc(cls, provider: str, n: int):
          cls._accum[provider] += n
          cls._totals[provider] += n

      @classmethod
      def get_totals(cls) -> dict:
          return cls._totals.copy()

      @classmethod
      def _flush(cls):
          data = {"timestamp": int(time.time())} | cls._accum
          LOG_PATH.parent.mkdir(exist_ok=True)
          with LOG_PATH.open("a") as f:
              f.write(json.dumps(data) + '\n')
          cls._accum = {"openai": 0, "gemini": 0}

  def _loop():
      while True:
          time.sleep(FLUSH_SEC)
          UsageLogger._flush()

  threading.Thread(target=_loop, daemon=True).start()
  ```
* **3.2** In `src/llm/openai_client.py` and `src/llm/gemini_client.py`, import the logger and increment counts after each API call. For example:

  ```python
  from shared.usage_logger import UsageLogger
  # ... after receiving response:
  UsageLogger.inc("openai", prompt_tokens + completion_tokens)
  ```

  (Adjust provider name for Gemini in its client.)
* **3.3** If `ENABLE_METRICS=1`: inside `UsageLogger.inc()`, also increment Prometheus counters. For example:

  ```python
  from shared.metrics import MetricsManager
  MetricsManager().openai_tokens_total.inc(n)
  ```
* **3.4** Add unit test **tests/test\_usage\_logger.py**: call `UsageLogger.inc("openai", 5)`, then force a flush (e.g. sleep slightly and call `UsageLogger._flush()`), and assert the last line of `usage_log.json` contains `"openai": 5`.
* **3.5** `git add -A && git commit -m "feat: persistent token UsageLogger"`

### 4  Implement ChatHistoryManager  → branch `feature/persistent-history`

* **4.1** Create `src/shared/history.py` with basic persistent history API:

  ```python
  import json, pathlib
  HIST_PATH = pathlib.Path("agent_workspace/chat_history.json")

  def load() -> list:
      if HIST_PATH.exists():
          return json.loads(HIST_PATH.read_text())
      return []

  def append(role: str, content: str):
      convo = load()
      convo.append({"r": role, "c": content})
      HIST_PATH.parent.mkdir(exist_ok=True)
      HIST_PATH.write_text(json.dumps(convo, indent=0))

  def reset():
      HIST_PATH.unlink(missing_ok=True)
  ```
* **4.2** Modify `ChatSession.send()` logic: after each user or agent message is processed, call `history.append(role, content)` to save it (use `"user"` or `"openai"/"gemini"` as role).
* **4.3** On app startup in `src/interfaces/gui.py`, pre-load past messages into session state:

  ```python
  import shared.history as history
  st.session_state.setdefault("messages", history.load())
  ```
* **4.4** Add a **Clear Chat** button in the sidebar to wipe history:

  ```python
  if st.sidebar.button("🗑 Clear Chat"):
      history.reset()
      st.session_state["messages"] = []
      st.experimental_rerun()
  ```
* **4.5** Create **tests/test\_history.py** to verify that saving and loading history works (append some messages, reset, etc.).
* **4.6** `git add -A && git commit -m "feat: persistent chat history storage"`

### 5  Sidebar Token Dashboard  → branch `ui/token-dashboard`

* **5.1** Extend the Streamlit sidebar to show token usage stats. For example, insert under the model selector:

  ```python
  import shared.usage_logger as UL
  with st.sidebar.expander("Token & Cost Stats", expanded=True):
      totals = UL.UsageLogger.get_totals()
      st.markdown(f"**OpenAI:** {totals['openai']:,} tok")
      st.markdown(f"**Gemini:** {totals['gemini']:,} tok")
  ```
* **5.2** Enable auto-refresh of this panel (every \~5 seconds). E.g., use `st.experimental_rerun()` or `st.sidebar.empty().add_static()` trick to periodically refresh.
  *(One approach:* insert a hidden `st.empty()` that calls `st.experimental_rerun()` on an interval timer.)\*
* **5.3** `git add -u && git commit -m "ui: add live token usage sidebar"`

### 6  CostMonitor (Billing Polling)  → branch `feature/cost-monitor`

* **6.1** Create `src/shared/cost_monitor.py` to periodically fetch API billing info:

  ```python
  import os, time, json, pathlib, threading, requests
  CACHE = pathlib.Path("agent_workspace/cost_cache.json")
  TTL   = 900  # 15 minutes

  def _poll_openai():
      key = os.getenv("OPENAI_API_KEY")
      if not key: return None
      try:
          url = "https://api.openai.com/v1/dashboard/billing/usage"
          since = int(time.time() - 86400)
          res = requests.get(f"{url}?start_time={since}&end_time={int(time.time())}",
                              headers={"Authorization": f"Bearer {key}"}, timeout=5)
          res.raise_for_status()
          data = res.json()
          return data.get("total_usage", 0) / 100.0  # cents to dollars
      except Exception:
          return None

  def _poll():
      from shared.usage_logger import UsageLogger
      while True:
          snapshot = {"ts": int(time.time())}
          snapshot["openai_24h"] = _poll_openai()
          # Estimate Gemini cost via token count (if no direct API):
          gem_tokens = UsageLogger.get_totals().get("gemini", 0)
          snapshot["gemini_est"] = gem_tokens * 0.00003  # $0.00003 per token approx
          CACHE.parent.mkdir(exist_ok=True)
          CACHE.write_text(json.dumps(snapshot))
          time.sleep(TTL)

  threading.Thread(target=_poll, daemon=True).start()
  ```
* **6.2** Import `shared.cost_monitor` at app startup (just importing will start the background polling thread).
* **6.3** In the sidebar, display the cost info if available. For example:

  ```python
  cost_path = pathlib.Path("agent_workspace/cost_cache.json")
  if cost_path.exists():
      data = json.loads(cost_path.read_text())
      st.sidebar.markdown(f"💵 OpenAI last 24h: ${data.get('openai_24h', 'N/A'):.2f}")
      st.sidebar.markdown(f"💵 Gemini est.: ${data.get('gemini_est', 'N/A'):.2f}")
  ```
* **6.4** Write tests for CostMonitor with a mocked `requests.get` to return sample JSON (e.g. `{"total_usage": 12345}`) and verify the cached values.
* **6.5** `git add -A && git commit -m "feat: cost monitoring (OpenAI & Gemini billing)"`

### 7  Streamlit GUI Redesign (Dark Theme)  → branch `ui/dark-redesign`

* **7.1** Create a Streamlit config file to enforce dark mode. In **.streamlit/config.toml**:

  ```toml
  [theme]
  base = "dark"
  primaryColor = "#2E85FF"
  textColor = "#F5F5F5"
  ```
* **7.2** *(Optional)* Rename `src/interfaces/gui.py` to `src/interfaces/app.py` for clarity. If renamed, update any entry points (e.g., in **pyproject.toml** `[project.scripts]` for the CLI/GUI command).
* **7.3** Refactor the GUI code for the new layout:

  * Call `st.set_page_config(page_title="AI Chat Interface", layout="wide")`.
  * Use a fixed sidebar (`st.sidebar`) for model selection, settings, and stats (as implemented in Tasks 5–6).
  * Ensure the main area scrolls chat messages (iterate over `st.session_state["messages"]` and render them with role labels, e.g., "**You:**" for user, "🤖 **OpenAI:**" for agent).
  * Provide a multiline `st.text_area` for input and a Send button that triggers the send handler.
* **7.4** Add a copy-to-clipboard button for any code blocks in agent responses. (Inject a small JS snippet in `st.markdown` that appends a "Copy" button to `<pre><code>` elements.)
* **7.5** `git add -A && git commit -m "ui: modern dark-theme chat interface redesign"`

### 8  Metrics GUI Hook  → branch `metrics/gui-hook`

* **8.1** If Prometheus metrics are enabled (`ENABLE_METRICS=1`), add a quick link in the sidebar to the metrics endpoint. For example:

  ```python
  from shared.metrics import MetricsManager
  metrics_url = f"http://localhost:{MetricsManager().port}/metrics"
  st.sidebar.markdown(f"[📊 Prometheus]({metrics_url})")
  ```
* **8.2** `git add -u && git commit -m "feat: add Prometheus /metrics link in GUI"`

### 9  README & Docs Refresh  → branch `docs/refresh`

* **9.2** Update **docs/index.md** (MkDocs home) to match the new branding and features described in the README.
* **9.3** Run `mkdocs build --strict` to ensure documentation builds without warnings or errors.
* **9.4** `git add -A && git commit -m "docs: overhaul README and index for new scope"`

### 10  Final QA + Release Tag

* **10.1** `pre-commit run --all-files` to run all linters/formatters on the entire codebase.
* **10.2** `pytest -q` and confirm the coverage report is ≥ 55% (the minimum coverage gate).
* **10.3** Perform a manual smoke test of the app:

  * Launch the Streamlit GUI (`streamlit run src/interfaces/app.py`), send a sample message, and verify the token counters update live.
  * Wait at least 60 seconds and check that **agent\_workspace/usage\_log.json** has a new entry (usage persisted).
  * Verify the sidebar cost panel shows values (or `N/A` if not configured).
  * Click **Clear Chat** and confirm the chat history file is cleared and UI resets.
* **10.4** Tag the release:

  ```bash
  git tag v0.2.0 -m "Persistent history, metrics, dark GUI"
  git push origin --tags
  ```

  (This marks the completion of Phase 1 deliverables.)

## Phase 2: Integrate Extended Tools (Memory, Web, Data, Automation)

### 11  Integrate Chroma Vector Memory  → branch `feature/memory-chroma`

* **11.1** Append **`chromadb`** to `requirements.txt` and install it (`pip install chromadb`).
* **11.2** Create `src/tools/memory.py` implementing a memory tool using Chroma. Initialize a local Chroma client and collection (e.g. `agent_memory`) at module import.
* **11.3** Implement new memory commands: `/remember <text>` to embed and store the given text in the vector DB, and `/recall <query>` to perform a similarity search and return relevant stored content. Register these in the ToolRegistry (so the agent can call them via `ToolRegistry.get("memory").execute(...)`).
* **11.4** Add unit tests for memory persistence: e.g., use `/remember` to add a sample fact, then call `/recall` with a related query and assert that the fact is retrieved. (Use a small embedding model or stub for determinism in tests.)
* **11.5** Run `pre-commit run --all-files` and then `pytest -q` to ensure lint and tests pass (update tests if needed to keep coverage ≥ 55%).
* **11.6** `git add -A && git commit -m "feat: long-term memory via Chroma vector DB"`

### 12  Integrate Playwright Browser Tool  → branch `feature/browser-tool`

* **12.1** Append **`playwright`** to `requirements.txt` and install it. Then run `playwright install` to download browser engines for headless operation.
* **12.2** Create `src/tools/browser.py` containing a `BrowserTool` class. Use `playwright.sync_playwright()` (in setup) to launch a headless browser context (Chromium). Implement a method like `open_url(url: str) -> str` that navigates to the URL and returns the page text (you can use `page.content()` or similar).
* **12.3** Register a new slash command `/browse <URL>` that instantiates `BrowserTool` (or uses a singleton instance) and returns the fetched page content or a summary of it. Include basic error handling for navigation timeouts or invalid URLs.
* **12.4** Write a basic test for the browser tool (mark it with `@pytest.mark.slow` if it uses actual browsing): e.g., use a local HTML file or a lightweight public page and assert that `/browse <file_or_url>` returns a snippet of expected text.
* **12.5** Run all linters and tests (`pre-commit` and `pytest`) to ensure nothing regresses.
* **12.6** `git add -A && git commit -m "feat: web browsing capability via Playwright"`

### 13  Integrate DuckDB Embedded Database  → branch `feature/analytics-db`

* **13.1** Append **`duckdb`** to `requirements.txt` and install it (`pip install duckdb`).
* **13.2** Create `src/tools/db_tool.py` with a `DatabaseTool` (DuckDB-backed). On initialization, open or create a DuckDB database file (e.g. `agent_workspace/analytics.duckdb`).
* **13.3** Implement a method `run_query(sql: str) -> str` that executes the given SQL on the DuckDB connection and returns the results (e.g., as a CSV string or formatted table). Support read-only queries (you may allow CREATE/INSERT if needed to log data).
* **13.4** Register a slash command `/query <SQL>` that passes the SQL string to the `DatabaseTool` and returns the output or any error message. Consider restricting potentially destructive commands in this context.
* **13.5** Add tests for the DB tool: for example, pre-load a small table, then use `/query` to select from it and verify the expected output. Also test that a malformed query returns an error string.
* **13.6** Run `pre-commit` and `pytest -q` to ensure the new code is linted and tested.
* **13.7** `git add -A && git commit -m "feat: embedded DuckDB for analytics queries"`

### 14  Integrate APScheduler for Task Scheduling  → branch `feature/scheduler`

* **14.1** Append **`apscheduler`** to `requirements.txt` and install it.
* **14.2** Create `src/tools/scheduler.py`. Initialize a `BackgroundScheduler` (e.g., `sched = BackgroundScheduler()` and `sched.start()`) when the app launches.
* **14.3** Implement a function (or Tool method) `schedule_task(command: str, trigger: dict)` that uses `sched.add_job` to schedule execution of a given slash command or tool function at a later time or on an interval. For example, allow usage like `/schedule "every 5m" "/browse example.com"`.
* **14.4** Register a slash command `/schedule <cron_or_interval> <command>` that parses the interval (e.g., using APScheduler's CRON or interval syntax) and schedules the specified command. Provide user feedback confirming the scheduling.
* **14.5** Add a test (could be an integration test marked slow) that schedules a one-off job with a short delay (e.g., 2 seconds), then uses a callback or shared flag to verify the job ran. Use `monkeypatch` or a dummy tool to avoid real sleep delays in the test.
* **14.6** Run `pre-commit` and `pytest -q` to ensure all quality gates pass (scheduler might spawn threads; ensure tests handle that deterministically or mark appropriately).
* **14.7** `git add -A && git commit -m "feat: background task scheduling via APScheduler"`

### 15  Integrate PyAutoGUI for OS Automation  → branch `feature/gui-automation`

* **15.1** Append **`pyautogui`** to `requirements.txt` and install it (`pip install pyautogui`).
* **15.2** Create `src/tools/rpa.py` implementing basic RPA (robotic process automation) tools. For example, define `type_text(text: str)` to simulate keyboard typing (`pyautogui.write(text)`) and `capture_screen(path: str)` to take a screenshot (`pyautogui.screenshot(path)`).
* **15.3** Register slash commands for these actions, e.g.: `/type "<text>"` to type text into the active window, and `/screenshot <filename>` to save a screenshot. Include safeguards: PyAutoGUI should not run if no display is available (you can detect CI via env and no-op or raise a friendly error).
* **15.4** Implement a **dry-run mode** for CI: if an env var like `CI=true` is detected, have the RPA functions log an action instead of performing it (to allow testing without actual GUI interaction).
* **15.5** Add a test for RPA tooling using the dry-run mode or monkeypatch PyAutoGUI: verify that calling `/type "hello"` results in a log or state indicating the text "hello" would be typed, and that `/screenshot` attempts to write a file (you can simulate the file write).
* **15.6** Run `pre-commit run --all-files` and `pytest -q` to ensure the RPA integration does not break any existing tests (mark RPA tests to skip in headless CI if needed).
* **15.7** `git add -A && git commit -m "feat: OS automation via PyAutoGUI (RPA)"`

## Phase 3: SOP Coordination Pipeline Implementation (Planner→Coder→QualityGate→Reviewer)

\**(Prerequisite: complete Phase 2 tasks before proceeding, so that new tools like memory and browsing are available during coordinated workflows.)*

### 16  Define Coordination Schema  → branch `coord/schema-keys`

* **16.1** Create `src/coordination/schema.py` defining structured artifact classes: `Plan`, `CodePatch`, `TestReport`, `Review`. Implement each as a dataclass or simple class with fields capturing the essential data (e.g., Plan might include a list of steps; CodePatch contains file diffs; TestReport has status and log; Review has final verdict and comments). Include `to_json()`/`from_json()` methods for serialization.
* **16.2** Extend the **ContextBus** to support new coordination keys. In `src/shared/context_bus.py`, add enum entries or constants for each artifact (e.g., `plan_draft`, `code_patch`, `test_report`, `final_review`). This ensures a canonical place in the shared state for each step’s output.
* **16.3** Create **tests/unit/test\_schema.py** to verify the new schema classes. For each class, construct an instance, round-trip it via `to_json()`/`from_json()`, and assert the result matches the original.
* **16.4** Run `pytest -q tests/unit/test_schema.py` and confirm all tests pass.
* **16.5** `git add -A && git commit -m "feat: coordination schema & ContextBus keys"`

### 17  Add SOP Prompt Templates  → branch `coord/prompts`

* **17.1** Create directory `src/coordination/prompts/` and add role-specific prompt files: **planner.txt**, **coder.txt**, **reviewer.txt**.

  * **planner.txt:** Instructions for the Planner agent (e.g., “You are a planning assistant. Analyze the user request and output a JSON Plan with steps, requirements, etc.”). Emphasize that output **must** be valid JSON fitting the Plan schema.
  * **coder.txt:** Instructions for the Coder agent (e.g., “You are a coding assistant. Produce a unified diff of code changes that implement the Plan, inside `diff ... ` fences, with no extra explanation.”).
  * **reviewer.txt:** Instructions for the Reviewer agent (e.g., “You are a code reviewer. You will receive the Plan, CodePatch, and TestReport. Output a JSON Review with fields: status (approved or changes\_requested), comments, and action\_required (true/false).”).
* **17.2** Ensure these prompt files are loaded by the agent system when spawning the respective agents (for example, modify the agent initialization or MultiAgentTool to fetch the content of these files as the `role_prompt`).
* **17.3** (No direct code to test here, but) do a quick manual check that the files are readable and contain no syntax errors (the content will be indirectly validated when the agents produce the expected structured outputs).
* **17.4** `git add -A && git commit -m "feat: add SOP prompts for Planner, Coder, Reviewer roles"`

### 18  Implement Coordinator FSM  → branch `coord/orchestrator`

* **18.1** Create `src/coordination/orchestrator.py` with a new `Coordinator` class. Define an enum of states or steps (e.g., `CoordStage` with values PLANNING, CODING, TESTING, REVIEW).
* **18.2** Implement `Coordinator.run(user_task: str) -> Review` to execute the SOP workflow deterministically:

  * **PLANNING:** Call the Planner LLM agent with the user\_task and `prompts/planner.txt`. Obtain a Plan (JSON string). Store it to ContextBus under the `plan_draft` key.
  * **CODING:** Provide the Plan to the Coder agent (using `prompts/coder.txt`). Get the `CodePatch` result (expected as a unified diff or JSON with file changes). Apply the patch to a temporary workspace (use existing file management tools to write the changes). Store the patch content under `code_patch` in ContextBus.
  * **TESTING:** Invoke the QualityGate (Task 19) on the temporary workspace to run all tests/linters. Capture the outcome (TestReport with pass/fail status and summary) and store it as `test_report`. If the report indicates failure and a retry is allowed (see Task 23), go back to the CODING step (providing the failure info to the Coder agent for a fix).
  * **REVIEW:** If tests passed, call the Reviewer agent with `prompts/reviewer.txt`, giving it access to the Plan, Patch, and TestReport from ContextBus. Collect the `Review` output (JSON summary and approval status) and store as `final_review`.
  * Return the final Review object (or message) as the result of `Coordinator.run()`.
* **18.3** Register a new chat command for this pipeline. For now, use a separate trigger (e.g., `/workflow2 <task>`) in the ToolRegistry or command parser that will instantiate `Coordinator` and call `run(task)`. (This allows side-by-side testing with the legacy `/workflow` command initially.)
* **18.4** Ensure each agent invocation uses only the relevant context: e.g., the Coder sees just the Plan (not the entire chat history), the Reviewer sees Plan+Patch+Report. Leverage the ContextBus and the structured outputs to avoid prompt injection between agents.
* **18.5** Run `pytest -q` to confirm no existing unit tests break due to these additions (adjust or skip legacy workflow tests if necessary). The new coordinator will be tested in Task 22.
* **18.6** `git add -A && git commit -m "feat: deterministic Planner→Coder→QualityGate→Reviewer workflow"`

### 19  Integrate QualityGate Hook  → branch `coord/quality-gate`

* **19.1** Append **`semgrep`** to the development requirements (e.g., add to `requirements-dev.txt` and ensure it's installed in CI) to include static security scanning.
* **19.2** Create `src/coordination/quality_gate.py` with a function `run_gate(work_dir: Path) -> dict`. This function will execute all quality checks within the given temporary workspace:

  * Run Ruff linting (`ruff .`).
  * Run tests with coverage (`pytest --maxfail=1 --disable-warnings -q`).
  * Run MyPy type check (`mypy .`) and Bandit security scan (`bandit -q -r .`) on the changed files.
  * Run Semgrep security rules (`semgrep --config auto -q .`) for any high-level vulnerabilities.
  * Collect the results: determine an overall **status** `"PASS"` if tests and Ruff passed (non-blocking issues like MyPy/Bandit/Semgrep can be treated as warnings but still pass), otherwise `"FAIL"`. Gather a brief `qa_output` (e.g., lint/test failures truncated to \~2KB) and list any files created or modified by tests (if relevant).
  * Return a dictionary or `TestReport` object with fields like `status`, `log` (the summary output), and `synced_files` (for any artifacts to persist).
* **19.3** Integrate this QualityGate into the Coordinator (Task 18): after applying the code patch in the CODING step, call `run_gate(temp_workspace)`. If the returned status is "FAIL", record the failure info and allow the Coordinator to invoke a fix (retry the Coder agent) if `max_retries` > 0 (to be implemented in Task 23).
* **19.4** Create **tests/unit/test\_quality\_gate.py** to unit-test the quality gate logic. For example, in a temp directory, write a sample file with an obvious lint error or failing test, then call `run_gate(temp_dir)` and assert that the returned `status` is "FAIL" and `qa_output` contains the expected error message. Also test a scenario with no issues to confirm a "PASS".
* **19.5** Run `pytest -q tests/unit/test_quality_gate.py` to ensure the QualityGate function behaves as expected in both pass and fail scenarios.
* **19.6** `git add -A && git commit -m "feat: integrate QualityGate checks into coordination flow"`

### 20  Add Coordination Metrics  → branch `coord/metrics`

* **20.1** Extend **MetricsManager** (in `src/shared/metrics.py`) with new Prometheus counters for the coordination pipeline:

  * `coord_agent_calls_total` with a label (role) to count how many times each agent role (Planner, Coder, Reviewer) is invoked.
  * `coord_gate_pass_total` with a label (status) to count QualityGate outcomes (e.g., pass vs fail occurrences).
    Define these counters under the appropriate section (guarded by metrics enabled flag to avoid errors if Prometheus client is off).
* **20.2** In the Coordinator workflow (Task 18), hook into these metrics:

  * After each agent runs, increment `coord_agent_calls_total{"role": <agent_name>}`.
  * After running the QualityGate, increment `coord_gate_pass_total{"status": "PASS"}` or `{"status": "FAIL"}` based on the TestReport.
* **20.3** Manually test metrics output (if possible): run the app with metrics enabled and execute a sample `/workflow2` task. Then visit the metrics endpoint (`/metrics`) and verify that the new counters (e.g., `coord_agent_calls_total`) are present and increasing.
* **20.4** `git add -u && git commit -m "feat: add Prometheus counters for coordination roles"`

### 21  GUI Toggle for Coordination v2  → branch `coord/gui-toggle`

* **21.1** Add a user-facing option in the GUI to switch on the new coordination pipeline. For example, in the sidebar settings, include a checkbox: **"Use Coordinated Workflow (SOP mode)"**.
* **21.2** In the command handling logic (where `/workflow` is parsed), check the state of this toggle. If the SOP mode is enabled (`True`), route the `/workflow <task>` command to use the new `Coordinator.run(task)` (Task 18) instead of the old `WorkflowTool.execute(...)`. If the toggle is off, fall back to the legacy workflow for backward compatibility.
* **21.3** Update any on-screen help or documentation in the app UI to reflect this option (e.g., a tooltip or sidebar note that enabling SOP mode will orchestrate Planner→Coder→QA→Reviewer automatically).
* **21.4** Test in the Streamlit GUI: run with the new setting off and on. With it on, issue a `/workflow <task>` command and observe that the multi-agent sequence runs (Plan/Code/QA/Review messages appear). With it off, ensure the old behavior (if still supported) runs.
* **21.5** `git add -u && git commit -m "feat: GUI option to enable SOP coordination pipeline"`

### 22  End-to-End Coordination Test  → branch `coord/e2e-tests`

* **22.1** Write an integration test covering the entire coordinated workflow. In **tests/e2e/test\_coordination\_pipeline.py**:

  * Set up a temporary workspace (use `WorkspaceManager` or `tempfile.TemporaryDirectory`) and initialize a minimal git repository or file structure if needed.
  * Create a simple scenario: e.g., a Python function with a bug and a failing unit test for it in the temp workspace.
  * Invoke the coordination pipeline: you can directly call `Coordinator.run("Fix the failing test for X")` or simulate the `/workflow` tool execution.
  * Wait for the process to complete. Capture the returned Review object or final ContextBus state.
  * Assert that the final review `status` is "approved" (or no action required) and that the failing test has been resolved (you can re-run pytest on the temp workspace to confirm all tests pass).
* **22.2** Mark this test with `@pytest.mark.slow` to exclude it from regular CI runs due to time and API usage (it will run the actual LLM calls unless those are stubbed/mocked). If possible, stub out the LLM agents with deterministic fake outputs to run this test purely offline.
* **22.3** Execute `pytest -q tests/e2e/test_coordination_pipeline.py` locally to verify the happy-path scenario works end-to-end.
* **22.4** `git add tests/e2e/test_coordination_pipeline.py && git commit -m "test: add end-to-end coordination pipeline test"`

### 23  Add Retry and Budget Guards  → branch `coord/retries-budget`

* **23.1** Augment the `Coordinator` (Task 18) with robustness features:

  * Introduce a parameter or attribute `max_retries` (default 1) for the Coder stage. Modify the logic so that if QualityGate returns a fail status, the coordinator will automatically loop back to the CODING step to give the Coder agent another attempt, up to `max_retries` times. After exceeding retries without a pass, the workflow should abort and return the failure review.
  * Track token usage or cost during the workflow: e.g., sum the tokens consumed by each agent call (this info can be obtained via UsageLogger or API usage metrics). Define a safe budget (for example, stop if > N tokens or > \$M cost have been used in this run).
* **23.2** Implement budget checks in `Coordinator.run()`: before invoking each agent, compare the cumulative tokens used (accessible via UsageLogger or MetricsManager) against a threshold (maybe configurable via an environment variable or passed-in parameter). If the next call would exceed the budget, skip that call and instead produce a Review output indicating the task was aborted due to budget limits.
* **23.3** Add/adjust tests for these scenarios:

  * Simulate a failing QA scenario and ensure that with `max_retries=1` the coordinator calls the Coder twice (original attempt + one retry) and then stops. You can mock QualityGate to fail on first attempt and pass on second to test the retry flow.
  * Simulate a budget exhaustion by pre-setting the UsageLogger counts near the limit and confirm the Coordinator aborts with a safe failure message when budget is exceeded.
* **23.4** Run `pytest -q` for the relevant test suite and confirm all new logic is covered and passing. Confirm that overall test coverage is still above the required threshold.
* **23.5** `git add -u && git commit -m "feat: add retry limit and budget guardrails to Coordinator"`

### 24  Security Sanitization  → branch `coord/security-sanitization`

* **24.1** Implement a sanitization utility to scrub potentially malicious content from agent outputs before they are reused. For example, create `coordination/util.py` with a function `sanitize_json(text: str) -> str` that removes known prompt injection patterns (e.g., any occurrence of `"Ignore previous instructions"` or similar phrases) from the given text.
* **24.2** Apply this sanitization step at each hand-off point in the Coordinator:

  * After getting the Plan from Planner, run `plan = sanitize_json(plan)` before storing it.
  * Similarly sanitize the diff/patch from Coder and the review comments from Reviewer before usage.
    This ensures that if an agent tries to insert a rogue instruction, it won't propagate to the next agent.
* **24.3** Add unit tests for `sanitize_json`. Include cases like a string containing `"<|Ignore previous instructions|>"` (or other prompt injection samples) and ensure the function strips or neutralizes them. Also verify it doesn’t alter innocent content.
* **24.4** Run `pytest -q tests/unit/test_sanitization.py` to validate the sanitization logic works as intended.
* **24.5** `git add -u && git commit -m "sec: sanitize inter-agent JSON artifacts for safety"`

### 25  Deprecate Legacy Coordination Mode  → branch `coord/retire-legacy`

* **25.1** Remove references to the old multi-agent orchestration to avoid confusion now that SOP coordination is in place. This includes retiring the `WorkflowTool` in `src/tools/workflow.py` and any legacy agent collaboration logic.
* **25.2** Eliminate the temporary toggle introduced in Task 21: the new SOP pipeline becomes the default behavior for `/workflow`. (In other words, `/workflow <task>` should now always invoke the Coordinator, and the checkbox or config controlling it can be removed.)
* **25.3** Search the codebase for any conditional branches or flags related to "legacy" or "A2A" mode. Delete or refactor those sections so that only the new Planner→Coder→QualityGate→Reviewer path exists moving forward.
* **25.4** Update or remove outdated tests tied to the old workflow. For example, if there were unit tests for `WorkflowTool`, consider removing them or replacing them with tests for the new Coordinator. Ensure all test files now pass with only the new coordination logic present.
* **25.5** Run a full quality check: `pre-commit run --all-files` and `pytest -q`. All linters and tests should remain green with the legacy code gone.
* **25.6** `git add -A && git commit -m "chore: remove legacy A2A workflow implementation"`

### 26  Documentation & Release  → branch `docs/coordination-v2`

* **26.1** Update **README.md** to document the new capabilities:

  * Revise the project description to highlight SOP coordination (structured multi-agent workflow) as the default mode.
  * In the usage section, add instructions for the `/workflow` command, explaining that it will autonomously execute a series of steps (planning, coding, testing, reviewing) to complete complex tasks.
  * Incorporate the newly integrated tools (long-term memory via `/remember`/`/recall`, web browsing via `/browse`, etc.) into the features list and usage examples.
* **26.2** Update contributor guides and policies:

  * **CONTRIBUTING.md:** emphasize running the full test & lint suite (including the new tools) and note that the coordinated workflow can be used for automating development tasks. Ensure the branching strategy (use `feat/` prefixes, etc.) and commit conventions are up-to-date.
  * **docs/quality\_policy.md:** adjust the quality gate documentation if needed (for instance, if Semgrep is now part of checks or if coverage threshold has changed, reflect that here).
* **26.3** Bump the version in project metadata (e.g., `__version__` or pyproject.toml) to **0.3.0** to mark this major update.
* **26.4** Perform a final integration test of the entire system on a clean environment (simulate as if an agent or a developer is using it from scratch). This includes verifying that `agent_workspace` setup, all new slash commands, and the `/workflow` pipeline function as documented.
* **26.5** Tag the new release:

  ```bash
  git tag v0.3.0 -m "v0.3.0 – SOP Coordination & Tool Integrations"
  git push origin --tags
  ```
* **26.6** `git add -A && git commit -m "docs: update README, CONTRIBUTING, and quality policy for v0.3.0 release"` (ensure all documentation changes are committed).
