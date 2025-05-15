# CLI Usage Notes for agent_system

This document provides quick instructions on how to activate the project's Python virtual environment and use the command-line interface (`chat_cli.py`) to interact with the configured Large Language Models (LLMs).

## 1. Activate the Virtual Environment

Before running any project scripts, ensure you have the `ethereum-project-venv` virtual environment activated. Open your terminal in the project root (`/Users/ianlucas/agent_system`) and run:

```bash
# To activate for the current shell session (recommended for working on the project)
pyenv shell ethereum-project-venv
```

Alternatively, to activate it more permanently for this directory until you deactivate or change it:

```bash
pyenv activate ethereum-project-venv
```

Your terminal prompt should change to indicate the environment is active (e.g., `(ethereum-project-venv) your-username@your-machine ...`).

## 2. Install/Update Dependencies

If you haven't installed dependencies yet, or if `requirements.txt` has been updated, run the following command *after* activating the virtual environment:

```bash
pip install -r requirements.txt
```

## 3. Using the Chat CLI (`chat_cli.py`)

Once the virtual environment is active and dependencies are installed, you can use `chat_cli.py` to talk to the LLMs.

*   **To chat with OpenAI (default, currently set to `o4-mini` as per your last edit):**
    ```bash
    python chat_cli.py
    ```
    or explicitly:
    ```bash
    python chat_cli.py --model openai
    ```

*   **To chat with Gemini (currently set to `gemini-2.5-pro-preview-05-06`):**
    ```bash
    python chat_cli.py --model gemini
    ```

**Inside the chat:**
*   Type your message and press Enter.
*   To exit, type `exit` or `quit` and press Enter.

## Troubleshooting

*   **`ModuleNotFoundError`**: Ensure the virtual environment is active. If it is, try reinstalling dependencies (`pip install -r requirements.txt`).
*   **API Key Errors**: Double-check that your `.env` file in the project root (`/Users/ianlucas/agent_system/.env`) contains the correct `OPENAI_API_KEY` and `GOOGLE_API_KEY`.
*   **`pyenv: command not found` or `pip: command not found`**: Make sure `pyenv` is correctly installed and configured in your shell environment. 