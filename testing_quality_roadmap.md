## test\_strategy.md

# Testing & Quality Roadmap for Agent System

This document outlines a phased plan to introduce automated quality safeguards into the **agent\_system** Python project. It covers unit tests (focusing on high-impact modules first), integration tests (covering critical workflows), additional static analysis tools to complement Ruff, and code coverage tracking with thresholds. This strategy aligns with the project’s blueprint (Phase 5: CI/CD and hardening) and leverages the Python ecosystem’s strong testing support (e.g. **pytest**).

## 1. Unit Test Suite (High-Value Modules First)

**Goal:** Establish a basic unit-test suite targeting the most critical and risk-prone parts of the codebase. This builds confidence in core functionality and prevents regressions in key logic.

**Key Modules to Prioritize:**

* **File System Tools (`src/tools/file_system.py`):** This is critical for safe file operations. It includes path resolution to prevent directory traversal and file read/write logic with truncation for large files. Bugs here could compromise data or security, so we will write unit tests for:

  * `_resolve_path`: ensure it blocks paths outside the project (e.g., `../secret.txt` raises an error).
  * `read_file_content`: test reading a normal text file vs. a binary file (expecting a Unicode decode error) and verify truncation messaging for large files.
  * `list_directory_contents`: use a temp directory to check correct listing format (folders vs files, size labels).
  * `write_content_to_file`: verify that writing content creates files and returns correct byte count, and that writing to an existing file without overwrite flag triggers the expected warning/status.

* **Command Handler (`src/handlers/command.py`):** This module parses user commands and executes them via the file tool. It’s high-risk because it interprets user input and manages state for writes. We will unit test:

  * **Parsing logic:** Ensure `/read`, `/write`, `/list`, `/overwrite` commands are recognized with proper arguments, including edge cases (like missing filepath after `/read` yielding an UNKNOWN command with usage hint). Also test natural language triggers (e.g., "save this to X") are parsed into the correct `CommandType`.
  * **Execution logic:** Simulate various command executions in isolation by injecting a dummy `FileManagerTool`. For example, test that a `/write` to a new file returns a success message and that writing to an existing file without overwrite sets the `pending_write` state and returns an overwrite prompt. Similarly, test that `/overwrite` with a matching pending filename completes the write and clears the pending state. We’ll use temporary files/directories in tests to avoid touching real workspace data.
    *Rationale:* Command handling is a complex stateful process (especially the write→overwrite flow) that is crucial to get right.

* **Chat Session Core (`src/core/chat_session.py`):** This class orchestrates conversation flow, model selection, and integration of tool outputs, making it central to system behavior. We will write targeted unit tests for its internal logic:

  * **Message history:** Verify that adding messages and clearing history works as expected (ensuring the system prompt is re-added on clear).
  * **System prompt:** Ensure the default system prompt is set and included in the history on initialization.
  * **Pending write logic:** Test the `confirm_overwrite()` method to ensure it writes the pending content to file and clears the pending fields. (This is important for the GUI’s overwrite button; our test can set up a pending write scenario and call `confirm_overwrite` to verify the file is saved and state reset.)
  * We will use dependency injection or monkeypatching to isolate ChatSession from external APIs. For example, replace `OpenAIClientManager.generate_response` with a stub that returns a fixed string to test that ChatSession correctly appends the assistant’s response to history and outputs it. We’ll also force scenarios where the model is unavailable (no API key) to confirm ChatSession returns the appropriate warning (`"⚠️ OpenAI model is not available."`).

* **LLM Client Managers (`src/llm/clients.py`):** These manage interactions with OpenAI and Gemini APIs. While they mainly wrap external SDKs, we will add small tests to ensure they handle missing credentials and errors gracefully:

  * Instantiate `OpenAIClientManager` with no API key and confirm `available` is False and any call to `generate_response` returns the warning message.
  * Monkeypatch the internal `client` to throw an exception on `.chat.completions.create` and verify `generate_response` catches it and returns an error string.
  * Test the token counting utility (`count_tokens`) with and without the `tiktoken` module available. For instance, if `tiktoken` is missing, ensure it falls back to a word count approximation and logs a warning. We can simulate this by temporarily modifying `clients.TIKTOKEN_AVAILABLE` in the test.

**Approach & Milestones:** We will create a `tests/` directory and add **pytest** tests focusing on these modules first. Each test will be small and fast, covering one behavior or edge case. As a solo developer, you can start with one module (e.g., file\_system) and get those tests passing, then proceed module by module. This iterative approach yields quick feedback. For example:

* *Milestone 1:* Basic file tool tests (covering read/write path errors and successes).
* *Milestone 2:* Command parsing and simple execution tests (reads and lists).
* *Milestone 3:* Full write→overwrite flow test and ChatSession integration for file commands.
* *Milestone 4:* ChatSession with stubbed model responses and error-handling tests.
* *Milestone 5:* LLM client edge-case tests (no API key, exception handling).

After these, we will have solid baseline coverage on the core logic. Initially, we expect coverage to easily exceed 60% once these high-value areas are tested.

## 2. Integration Test Suite (Critical Workflows & Interfaces)

**Goal:** Ensure that the system’s components work together correctly on crucial execution paths, beyond what unit tests cover. Integration tests will mimic real-world usage scenarios, especially those spanning multiple modules or involving external interfaces.

**Core Integration Scenarios:**

* **Interactive Chat Flow:** Simulate a user session via the `ChatSession` API (without the GUI/CLI). For example, an integration test can feed a sequence of messages to `ChatSession.process_user_message` and assert on the combined outcomes:

  * Scenario: User asks a question (we monkeypatch the LLM response), then uses a file command. E.g., *User:* "Hello", *Agent:* "Hi..." (stubbed), *User:* "/list logs", *Agent:* returns directory listing. This test would cover the hand-off from user input to either LLM or tool response seamlessly.
  * **Dual-agent (collaborative) mode:** If the **both** model option is used, `ChatSession` invokes the A2A collaboration routine. We can test the logic that requires both clients to be available. By stubbing `openai_client.chat.completions.create` and `gemini_client.generate_content` with dummy outputs, we verify that `a2a_collab.run` returns a combined answer which is properly added to history with sender "collab". (We’ll likely defer full testing of the multi-round A2A loop due to external API calls, but we can ensure the integration point is triggered correctly when both models are present.)
  * **Error flows:** Test a conversation where the OpenAI key is missing. The first user prompt in OpenAI mode should result in an immediate `"model not available"` warning from `ChatSession`. This validates that integration between config and ChatSession error handling works (no crash when APIs are unavailable).

* **File Operation End-to-End:** Start a chat session and simulate a user saving the last assistant answer to a file using natural language:

  1. Seed the history with an assistant message (or call the model stub once).
  2. User inputs: "save this to `test.txt`".
  3. Verify: The content was written to `test.txt` and the assistant’s reply confirms the save (`✅ Saved 'test.txt' ...`). This single test goes through: command parsing of natural language, fetching the last assistant message from history, writing the file, and returning a success message via the command handler.
  4. Extend this with an overwrite: If the user repeats "save this to `test.txt`", the first attempt sets a pending overwrite state and returns a warning. The next user input `/overwrite test.txt` should then trigger the actual file save via the integration of `ChatSession.command_handler` and `FileManagerTool`, clearing the pending state. The test will confirm the file content is updated and the final response is a success confirmation.

* **CLI Interface Behavior:** Since the CLI (`chat_cli.py`) is a thin wrapper around `ChatSession` and `input()`, we won’t write complicated automation for it initially. Instead, we ensure that the logic gating model availability works (e.g., launching `ChatSession()` without a key yields an error log and exit). We might use a small test invoking `src.interfaces.cli.main()` with a patched `ChatSession` to simulate this, or simply rely on unit tests for `ChatSession.openai_available` as a proxy. Full interactive CLI tests can be done manually, as the automated tests above already validate the core loop logic (reading input → `process_user_message` → output formatting).

**Organization:** We can separate pure unit tests and integration tests. One approach is to mark integration tests with `@pytest.mark.integration` and perhaps run them conditionally (so a quick run can skip them if needed). However, if integration tests remain fast (no external API calls or long waits), we can run all tests in CI. The test files could be structured as:

* `tests/unit/test_file_tool.py`, `tests/unit/test_command_handler.py`, etc.
* `tests/integration/test_chat_session_flow.py`, etc.

Each integration test may use **pytest fixtures** to set up temp directories or monkeypatch external calls (e.g., using `monkeypatch` fixture to replace network calls with dummy functions). This ensures tests run offline and deterministically.

**Milestones:** After establishing unit tests, add integration tests for the above scenarios:

* *Milestone 6:* Basic chat Q\&A flow with stubbed LLM (ensuring ChatSession integrates history and response correctly).
* *Milestone 7:* File save and overwrite workflow through ChatSession end-to-end.
* *Milestone 8:* (Optional) A2A collaboration trigger test with dual model stubs.
* *Milestone 9:* Review coverage for any gaps; add tests for any remaining critical path (e.g., perhaps the streamlit interface’s file command integration, which could be indirectly tested by ensuring `ChatSession.confirm_overwrite` works as intended when called).

## 3. Static Analysis Tools (Beyond Ruff)

Ruff is already in use for fast linting and style checks. We will introduce **additional static/semantic analysis** tools that address areas Ruff doesn’t cover, to catch bugs and security issues early. These tools are chosen for popularity, ease of use, and low overhead:

* **Mypy (Static Type Checking):** Add mypy to enforce type correctness. The codebase includes type hints (e.g., function signatures and class properties in `clients.py`), but without a type checker, certain mistakes might go unnoticed. Mypy will verify that function calls and returns match the declared types. This can catch errors like mismatched function arguments or misuse of return values that would not be flagged by Ruff. For instance, if a function is expected to return a `ToolOutput` but returns `None` in some branch, mypy can warn about it. We will configure mypy in *strict but gradual* mode:

  * Include a `mypy.ini` (or add to `pyproject.toml`) to at least ignore third-party library imports that lack type stubs (e.g., `openai`, `google-generativeai`) so that mypy focuses on our code. For example, use `ignore_missing_imports = True` for those packages.
  * Run `mypy src` as part of CI. Initially, mypy might reveal some typing issues or require adding type hints in a few places (e.g., the `collaboration.py` function uses `Any` for clients, which we can document or refine later). We will treat mypy warnings as non-failing at first if they are numerous, then tighten the settings over time as types improve.

* **Bandit (Security Linter):** Introduce Bandit to statically scan for common security vulnerabilities. This is important as the project evolves to handle financial data and possibly secrets. Bandit will check for issues like use of insecure functions, improper file access patterns, etc. For example, if a developer accidentally introduced an `eval()` call or used a weak random for security, Bandit would flag it. In our current code, file operations are a potential area of concern; we expect Bandit to compliment our tests by ensuring no obvious vulnerabilities (e.g., it might double-check that we’re not writing to world-accessible paths, though our `_resolve_path` already guards against that). We’ll run `bandit -q -r src` in CI to get a quick report. Any findings will be addressed (or explicitly annotated to ignore if they're false positives), keeping the Bandit scan clean.

* **(Optional) Black (Code Formatter):** While Ruff covers most style issues, adding **Black** for automatic formatting can further reduce stylistic churn. Black doesn’t overlap with Ruff’s lint rules; instead, it enforces a uniform code style. This can be run locally (and even in CI as a check with `--check` flag). Since Black is very popular and configuration-free, it’s an easy win for consistency. This is recommended as a future enhancement: for now, we focus on tests and static analysis that affect correctness.

By integrating these tools, we create a robust safety net: Ruff for syntax and common errors, mypy for type correctness, and Bandit for security. All are lightweight and widely used, so they fit well in a solo-developer workflow on modest hardware. **Pytest** remains our primary test framework (as identified in the project’s tech stack report), and these tools complement it without duplicating efforts. We will update documentation to instruct how to run them (e.g., “run `ruff .`, `mypy src`, `bandit -r src` before committing”).

## 4. Code Coverage Tracking and Improvement Plan

**Coverage Setup:** We will use **pytest-cov** (coverage plugin for pytest) to measure test coverage. A minimal `pytest.ini` configuration (see below) will ensure that when tests run, a coverage report is produced and a minimum threshold is enforced. We start with a **60% coverage threshold**, meaning the test suite must exercise at least 60% of the code lines. This threshold is intentionally modest for initial adoption, given no tests existed before. It will prevent the introduction of completely untested new modules while not immediately failing the build for legacy code that still lacks tests. The threshold will be enforced via `--cov-fail-under=60` in pytest settings.

**Gradually Raising the Bar:** Achieving high coverage will be incremental:

* Once the foundational tests (unit tests for core modules) are in place, we expect to reach or surpass 60%. At that point, we will raise the minimum to, say, 70% to encourage writing tests for new features.
* As integration tests and additional unit tests for less-critical modules (e.g., CLI interface, or future Ethereum data modules) are added, we will continue increasing the threshold (perhaps 10% at a time). The target is to reach **90% coverage** eventually, as stated. This high level ensures most lines are exercised, though we acknowledge some parts (like defensive branches or external API calls) might remain hard to test.
* We will document a policy to not just chase the number, but also consider coverage *quality*. For example, writing trivial tests just to hit lines isn’t useful; instead we’ll focus on meaningful scenarios. The **coverage report** (we’ll use `--cov-report=term-missing` to see which lines are untested) will guide us to any critical code paths that still lack tests.

**CI Integration:** A continuous integration workflow will run all quality checks on each push/PR:

1. **Install deps and run Ruff** to catch lint issues early.
2. **Run mypy and Bandit** to catch type and security issues.
3. **Run `pytest`** to execute unit/integration tests with coverage. The CI will rely on the coverage threshold to fail if below target. We’ll start with `fail-under=60`% and update this value in the config as we raise the standard.

All these steps should complete in under 5 minutes on a typical runner:

* Ruff, mypy, and bandit are fast (and operate only on our relatively small codebase).
* The test suite, designed with unit tests and small integrations, should also be quick (no test should rely on sleep or external network calls – we use monkeypatching to simulate external responses). Any slow tests will be reviewed and optimized or marked to skip on CI if truly needed.

**Example Pytest/Coverage Config (`pytest.ini`):**

```ini
[pytest]
addopts = --cov=src --cov-report=term-missing --cov-fail-under=60
```

*(We include the `--cov-report=term-missing` to list uncovered lines for easy reference in CI logs. Developers can locally generate an HTML report for detailed coverage info.)*

**Milestone Targets:** As we add tests:

* Reach 60% by covering core logic (milestones 1–5 above). **\[Then set `--cov-fail-under=70`.]**
* Reach \~80% with broader integration tests and additional module coverage (e.g., future modules for data analysis). **\[Increase fail-under to 80%.]**
* Approach 90% by testing edge cases and any new features (ensuring even error-handling branches run in tests). At this stage, we will also consider if some auto-generated or trivial code should be excluded from coverage to focus on relevant logic (using `.coveragerc` or `# pragma: no cover` for guard clauses, if needed).

## 5. Continuous Integration Workflow

We will add a GitHub Actions workflow (YAML) to automate the above. The workflow will be triggered on each push and pull request to the main branch. Key steps:

* **Setup Python 3.12** on the runner (ensuring consistency with the project’s Python 3.12.10 environment).
* **Install dependencies** using `pip` (including dev tools like pytest, pytest-cov, mypy, bandit). Caching can be added later to speed this up.
* **Run Ruff**: `ruff .` will lint the entire project.
* **Run Mypy**: `mypy .` (or `mypy src`) to type-check our code.
* **Run Bandit**: `bandit -q -r src` for a quiet recursive scan.
* **Run Tests**: `pytest` (Pytest will pick up our `pytest.ini` config to include coverage and threshold enforcement).

If any step fails (lint error, type error, security warning, or test failure/low coverage), the workflow will fail, preventing a merge. This ensures that code quality remains high as development continues. The CI status gives the solo developer immediate feedback on each commit.

The CI configuration will be kept minimal and within 120 lines as requested. See the accompanying **`.github/workflows/ci.yml`** for the exact implementation. Having this in place will continuously enforce the practices outlined in this roadmap, ultimately leading to a robust, maintainable codebase with high test coverage and strong guarantees of quality.

## Appendix A — Sequential Implementation Checklist (Cursor-Agent Friendly)

*(Execute each task in order. Each task is self-contained and idempotent; skip if already complete.)*

| ID  | Objective                     | Description / Exact Actions                                                                                                                                                                                                                                                                                                                                                                                                           |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | - | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| A0  | Create feature branch         | `bash\ngit checkout -b feat/quality-safeguards\n`                                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A1  | Add dev dependencies          | 1. **Create `requirements-dev.txt`** with:<br/>`text\npytest>=8.2\npytest-cov>=5.0\nmypy>=1.10\nbandit>=1.7\nruff>=0.4\n`\n2. **Install locally** → `bash\npython -m pip install -r requirements-dev.txt\n`                                                                                                                                                                                                                           |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A2  | Bootstrap test directory      | `bash\nmkdir -p tests/unit tests/integration\n`                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A3  | Seed example unit tests       | Create `tests/unit/test_file_system.py`:<br/>`python\nimport tempfile, os, pytest\nfrom src.tools.file_system import FileSystemTool\n\ndef test_resolve_path_blocks_escape(tmp_path):\n    fs = FileSystemTool(base_dir=tmp_path)\n    with pytest.raises(ValueError):\n        fs._resolve_path('../hack.txt')\n` *(repeat for other critical cases as you add coverage)*                                                            |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A4  | Seed example integration test | Create `tests/integration/test_chat_flow.py`:<br/>`python\nfrom unittest.mock import MagicMock\nfrom src.core.chat_session import ChatSession\n\ndef test_basic_flow(tmp_path, monkeypatch):\n    cs = ChatSession(workspace=tmp_path)\n    monkeypatch.setattr(cs, '_choose_client', lambda *_: MagicMock(generate_response=lambda **_: 'pong'))\n    reply = cs.process_user_message('ping')\n    assert 'pong' in reply.lower()\n` |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A5  | Add `pytest.ini`              | `ini\n[pytest]\naddopts = --cov=src --cov-report=term-missing --cov-fail-under=60\n`\n\*(place at repo root)\*                                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A6  | Add `mypy.ini`                | `ini\n[mypy]\npython_version = 3.12\nignore_missing_imports = true\nstrict = False\n`\n\*(can tighten later)\*                                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A7  | Add Bandit configuration      | Optional: `bandit.yaml` if exclusions needed; otherwise Bandit runs with defaults.                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A8  | Add CI workflow               | Create `.github/workflows/ci.yml` (≤120 lines):<br/>\`\`\`yaml\nname: CI\non: \[push, pull\_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout\@v4\n      - uses: actions/setup-python\@v5\n        with:\n          python-version: '3.12'\n      - name: Install deps\n        run:                                                                                                   | \n          python -m pip install --upgrade pip\n          python -m pip install -r requirements-dev.txt\n          python -m pip install -e .\n      - name: Ruff\n        run: ruff .\n      - name: Mypy\n        run: mypy src |   | true  # non-blocking initial pass\n      - name: Bandit\n        run: bandit -q -r src\n      - name: Tests & Coverage\n        run: pytest\n\`\`\` |
| A9  | Run suite locally             | `bash\npytest\nruff .\nmypy src  # expect some warnings initially\nbandit -q -r src\n` Ensure all pass/meet thresholds.                                                                                                                                                                                                                                                                                                               |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A10 | Commit & push                 | `bash\ngit add .\ngit commit -m \"feat: initial test/CI framework with 60% cov gate\"\ngit push --set-upstream origin feat/quality-safeguards\n`                                                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A11 | Create PR                     | Open a pull request → target `main`. GitHub Actions must show ✅ before merge.                                                                                                                                                                                                                                                                                                                                                         |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |
| A12 | Iteratively raise coverage    | After merge, repeat Tasks A3/A4 to add tests; raise `--cov-fail-under` in `pytest.ini` by +10 each ≈two milestones until reaching **90 %**. Commit & PR each increment.                                                                                                                                                                                                                                                               |                                                                                                                                                                                                                                    |   |                                                                                                                                                     |

### File Reference Digest

*(for agent copy-pasting)*

<details><summary><code>pytest.ini</code></summary>

```ini
[pytest]
addopts = --cov=src --cov-report=term-missing --cov-fail-under=60
```

</details>

<details><summary><code>.github/workflows/ci.yml</code></summary>

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements-dev.txt
          python -m pip install -e .
      - name: Ruff
        run: ruff .
      - name: Mypy
        run: mypy src || true
      - name: Bandit
        run: bandit -q -r src
      - name: Tests & Coverage
        run: pytest
```

</details>

---

**End of Appendix A**