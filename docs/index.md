# agent_system

Welcome to the **agent_system** documentation site.

This project focuses on providing a robust framework for multi-agent LLM orchestration and collaboration. It features an interactive Streamlit GUI as the primary interface, an A2A-lite workflow, a shared ContextBus (MCP-lite memory), an extensible ToolRegistry, and built-in observability and quality gates.

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