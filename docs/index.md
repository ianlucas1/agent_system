# Multi-Agent Chatbot GUI (SOP-based multi-agent coordination)

Welcome to the **agent_system** documentation site.

This project is an interactive Streamlit application for orchestrating **multiple cooperative LLM agents**. It features a structured Planner → Coder → QualityGate → Reviewer workflow (SOP coordination), a shared, file-locked **ContextBus** (MCP-lite memory), an extensible **ToolRegistry** (file ops, shell, git/gh, memory, workflow, etc.), built-in observability (Prometheus toggle, `/metrics`), strict quality gates (Ruff, pytest, MyPy/Bandit for touched files, auto QA for code-generating agents), and live documentation (MkDocs GH-Pages). The GUI serves as the central cockpit for these operations.

Recent updates include long-term vector memory, a headless web browser, a SQL analytics engine, task scheduling, and GUI automation tools—extending agent capabilities while keeping the system lean.

Use the sidebar (or the links below) to navigate:

- [Quickstart](quickstart.md) – get up and running in minutes.
- [Multi-Agent How-To](multi_agent.md) – deep-dive into the Planner, Coder, QA, and Reviewer agents.
- [CLI & GitOps](cli_gitops.md) – automate workflows from the command line.
- [Quality Policy](quality_policy.md) – learn about our code-quality ratchet and CI gates.
- [API Reference](api_reference.md) – public classes, functions, and configuration.

## Repository Highlights

- **Tools & Agents** live in `src/`.
- **Execution logs** are stored in `logs/`.
- **Agent workspaces** in `agent_workspace/` keep per-agent state.
- **Docs** are built with MkDocs Material and deployed via GitHub Pages.

## Contributing

See the [CONTRIBUTING guide](https://github.com/ianlucas1/agent_system/blob/main/CONTRIBUTING.md) for a concise development loop and PR checklist.

Happy building! 🚀 