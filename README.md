````markdown
# Autonomous Ethereum Valuation Agent

This project seeds an autonomous agent that will grow—through its own iterative planning and coding—into a production-grade Ethereum valuation framework grounded in rigorous data analysis and PhD-level research.

## Bootstrapping the Agent

Run the bootstrap script:

```bash
python3 bootstrap_agent.py
```

The script creates the required workspace folders and a `session_bootstrap.json` file whose `next_task` is **toolchain_discovery**.

## CEO Interaction Model

* **Agent → CEO** When the agent needs credentials, approvals, or budget changes, it writes a checklist Markdown file in **`exec_requests/`**.  
* **CEO → Agent** You respond by dropping a Markdown file in **`inbox/`** (or later via an optional CLI).  
  No other manual intervention is required unless the agent pauses for input.

Logs and decision records live in **`logs/`** for you to inspect at any time.

*(See `blueprint.json` for the full roadmap and design.)*
````
