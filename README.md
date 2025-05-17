# Multi-Agent Chatbot GUI (SOP-based multi-agent coordination)

[![Docs](https://img.shields.io/badge/docs-latest-brightgreen)](https://ianlucas1.github.io/agent_system/)

This project is an interactive Streamlit application that lets a human (or supervising LLM) orchestrate **multiple cooperative LLM agents**. It features an explicit *A2A-lite* workflow (e.g., via `/workflow` triggering Planner → Coder → QualityGate → Reviewer), a shared, file-locked **ContextBus** (our *MCP-lite* memory), an extensible **ToolRegistry** (file ops, shell, git/gh, memory, workflow, etc.), built-in observability (Prometheus toggle, `/metrics`), strict quality gates (Ruff, pytest, MyPy/Bandit for touched files, auto QA for code-generating agents), and live documentation (MkDocs GH-Pages). The GUI serves as the central cockpit for these operations.

It now integrates long-term vector memory, a headless web browser, a SQL analytics engine, task scheduling, and GUI automation tools to extend the agent's capabilities while keeping the system lean.

## Bootstrapping the Agent

Run the bootstrap script (creates workspace directories and seeds `session_bootstrap.json`):

```bash
python -m src.bootstrap
```

The script creates the required workspace folders and a `session_bootstrap.json` file whose `next_task` is **toolchain_discovery**.

## CEO Interaction Model

* **Agent → CEO** When the agent needs credentials, approvals, or budget changes, it writes a checklist Markdown file in **`exec_requests/`**.  
* **CEO → Agent** You respond by dropping a Markdown file in **`inbox/`** (or later via an optional CLI).  
  No other manual intervention is required unless the agent pauses for input.

Logs and decision records live in **`logs/`** for you to inspect at any time.

*(See `blueprint.json` for the full roadmap and design.)*

## Chat Interface Usage

### Command-Line Interface (CLI)

Ensure you have set your OpenAI and Google API keys in the `.env` file (`OPENAI_API_KEY` and `GOOGLE_API_KEY`). Launch the CLI with:

```bash
python -m src.interfaces.cli [--model openai|gemini|both]
```

By default, the CLI uses OpenAI. Use `--model gemini` to use Google Gemini, or `--model both` to query both models in parallel. In both mode, the CLI will display two answers (labeled by model). Type your messages and press Enter. To exit, type `exit` or `quit`.

You can use special slash commands in the chat (for file operations and more):
- **Read a file:** Type `/read <path>` (e.g. `/read README.md`) to output a file's contents.
- **Write to a file:** Type `/write <path> <content>` to create or overwrite a file with the given content. *If the file exists, you'll be prompted to confirm overwrite.*
- **List directory:** Type `/list <directory>` to list contents of a directory (e.g. `/list data/`).
- **Confirm overwrite:** If prompted (from a `/write` to an existing file), type `/overwrite <filename>` to confirm replacing it.
- **Browse web:** Type `/browse <URL>` to fetch the text content of a webpage (uses a headless browser tool).
- **Memory store/retrieve:** Type `/remember <text>` to save information to the AI's long-term memory, and `/recall <query>` to query that memory by semantic similarity.

All file operations are sandboxed to the project directory for safety. Errors or confirmations will be shown as system messages in the chat.

### Streamlit Web GUI

To launch the web interface, run:

```bash
streamlit run src/interfaces/gui.py
```

This will open a local browser app. The GUI displays the conversation and provides:
- A **Model selector** dropdown to choose **OpenAI**, **Gemini**, or **Both (OpenAI + Gemini)**. You can switch models during a conversation.
- If "Both" is selected, an optional **"Enable collaboration (A2A)"** checkbox appears. When enabled, the two agents will critique and refine answers collaboratively (using Google's A2A framework) instead of just responding independently.
- A chat input box to send messages. Press "Send" or hit Enter to submit.
- Support for the same **file commands** as the CLI (e.g. typing `/read file.txt` or asking "what's in the logs folder?").
- If a file write operation requires confirmation, an **Overwrite** button will appear to finalize it.
- API connection status indicators in the sidebar (shows whether OpenAI/Gemini API keys are properly loaded).
- A **Clear Chat** button to reset the conversation.

The web UI maintains multi-turn context. You can observe both model responses side by side when using dual-model mode. The interface labels each response with the agent name for clarity. Ensure your API keys are set before running, so the models can respond.

## Contributing

Please read the [CONTRIBUTING.md](CONTRIBUTING.md) guide for a quick development loop, GitHub CLI workflow, and pre-commit setup.

Before running the CLI or GUI you should install the package in *editable* mode so `src/` is importable:

```bash
pip install -e .
```

## Development Quick-Start

```bash
# one-time
pip install -r requirements-dev.txt
pre-commit install   # git hooks (Ruff, Bandit, pytest)

# before every push
tox -e ci             # runs the identical pipeline that GitHub CI will run
```

The first Ruff pass fixes most style issues automatically; if `tox -e ci` is
green, the GitHub workflow will be green as well.

<!-- Test comment for hook validation V3 -->
