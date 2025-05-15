# Quickstart

This page provides a quick guide to getting started with the agent_system project.

## 1. Installation

Clone the repository:

```bash
git clone <repository_url>
cd agent_system
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run src/bootstrap.py
```

## 2. One-Minute Demo

Once the application is running, you can try a simple workflow using the `/workflow` command:

```
/workflow Build hello
```

This should trigger the Planner, Coder, Quality Gate, and potentially the Reviewer agents to build and test a simple "hello world" type task.

## 3. Further Reading

- [Multi-Agent How-To](multi_agent.md)
- [CLI & GitOps](cli_gitops.md)
- [Quality Policy](quality_policy.md)
- [API Reference](api_reference.md) 