# Quickstart: AI Chat Interface

This guide helps you get the AI Chat Interface up and running.

## Running the AI Chat Interface (Regular Use)

Once the first-time setup (see below) is complete, follow these steps each time you want to use the chat interface:

1.  **Open Your Terminal in the Project Directory**:
    Navigate to the project root (`/Users/ianlucas/agent_system`).

2.  **Automatic Virtual Environment Activation**:
    If `direnv` is set up correctly (as per first-time setup), it will automatically detect the `.envrc` and `.python-version` files and activate the `agent_system-venv` virtual environment. Your terminal prompt should change to indicate this (e.g., `(agent_system-venv) ...`).
    *   If it doesn't activate, ensure `direnv` is installed, hooked into your shell, and you've run `direnv allow` in this directory.

3.  **Run the Chat GUI**:
    With the `agent_system-venv` active, run:
    ```bash
    streamlit run src/interfaces/gui.py
    ```
    This will start the web server and should automatically open the chat interface in your default web browser.

4.  **API Keys**:
    The application requires API keys for OpenAI and/or Google Gemini. Ensure these are correctly set up in a `.env` file located at `/Users/ianlucas/agent_system/.env`. See the "API Key Setup" section under "First-Time Setup" for details.

4.5 **Command-Line Interface (optional)**:
    To run the text-only CLI instead of the GUI:

    ```bash
    python -m src.interfaces.cli --model openai   # or gemini | both
    ```

5.  **Dependencies (`requirements.txt`)**:
    You generally **do not** need to run `pip install -r requirements.txt` every time. This is only required during the first-time setup or if the `requirements.txt` file has been updated with new dependencies.

---

## First-Time Setup (or New Machine)

Follow these steps to set up the project from scratch.

### 1. Prerequisites

*   **Git**: For cloning the repository.
*   **Python**: It's highly recommended to manage Python versions using `pyenv`.
    *   Install `pyenv`: Follow instructions at [pyenv installer](https://github.com/pyenv/pyenv-installer).
*   **`direnv`**: For automatic virtual environment activation.
    *   Install `direnv`: Follow instructions at [direnv installation guide](https://direnv.net/docs/installation.html). Ensure it's hooked into your shell (e.g., by adding `eval "$(direnv hook zsh)"` to your `.zshrc`).

### 2. Clone the Repository

```bash
# Replace with the correct repository URL if different
git clone https://github.com/ianlucas1/agent_system.git
cd agent_system
```

### 3. Set Up Python Virtual Environment

The project is configured to use a `pyenv` virtual environment named `agent_system-venv`.

1.  **Ensure a base Python version is installed via `pyenv`** (e.g., 3.11, 3.12). If you need to install one:
    ```bash
    # Example: Install Python 3.12.0
    pyenv install 3.12.0 
    ```
2.  **Create the `agent_system-venv` virtual environment** (if it doesn't exist from a previous setup or another machine):
    ```bash
    # Replace 3.12.0 with your desired base Python version if different
    pyenv virtualenv 3.12.0 agent_system-venv
    ```
    The `.python-version` file in the repository is already set to `agent_system-venv`.

### 4. Activate Environment with `direnv`

1.  Navigate to the project directory (if not already there).
2.  `direnv` will notice the `.envrc` file (already committed) which tells it to activate the `agent_system-venv` via an explicit `layout python …/agent_system-venv/bin/python` command. The first time (or whenever `.envrc` changes) it will be blocked. Allow it:
    ```bash
    direnv allow
    ```
    Your terminal prompt should now show `(agent_system-venv)`.

### 5. Install Dependencies

With the `agent_system-venv` active, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 6. API Key Setup (`.env` file)

1.  Create a file named `.env` in the project root (`/Users/ianlucas/agent_system/.env`).
2.  Add your API keys to this file in the following format:
    ```env
    OPENAI_API_KEY="your_openai_api_key_here"
    GOOGLE_API_KEY="your_google_api_key_here"
    ```
    Replace the placeholder values with your actual keys. This file is ignored by Git (due to `.gitignore`) to keep your keys private.

After completing these steps, you can run the application as described in "Running the AI Chat Interface (Regular Use)". 