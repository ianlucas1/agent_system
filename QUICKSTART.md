# Quickstart: Running the AI Chat Interface

This guide provides the minimal steps to get the AI Chat Interface running.

## 1. Activate Virtual Environment & Install Dependencies

First, ensure your Python virtual environment is active and dependencies are installed.

From the project root (`/Users/ianlucas/agent_system`):

```bash
# Activate your preferred virtual environment (e.g., using pyenv)
# Example: pyenv shell ethereum-project-venv 

# Install/update dependencies
pip install -r requirements.txt
```

**Note:** You generally only need to run `pip install -r requirements.txt` once after cloning the project or when the `requirements.txt` file is updated with new dependencies. The packages are installed directly into your active virtual environment.

## 2. Run the Chat GUI

Once the environment is set up:

```bash
streamlit run chat_gui.py
```

This will start the web server and should automatically open the chat interface in your default web browser.

## API Keys

Ensure your API keys are correctly set up in a `.env` file in the project root (`/Users/ianlucas/agent_system/.env`):

```
OPENAI_API_KEY="your_openai_key_here"
GOOGLE_API_KEY="your_google_key_here"
``` 

## 3. (Optional) Automatic Virtual Environment Activation

To avoid manually activating your virtual environment every time you open the project, you can set up automatic activation.

### Using `direnv` with `pyenv`

`direnv` is a shell extension that loads and unloads environment variables depending on the current directory. If you use `pyenv` for managing Python versions and virtual environments, you can use `direnv` to automatically activate your project's `pyenv` virtual environment.

1.  **Install `direnv`**: Follow the installation instructions for your operating system on the [direnv website](https://direnv.net/docs/installation.html). Make sure to hook it into your shell.
2.  **Create a `.python-version` file (if you haven't already)**: In your project root (`/Users/ianlucas/agent_system`), ensure you have a `.python-version` file specifying your desired `pyenv` virtual environment. You can create/update this by running:
    ```bash
    pyenv local ethereum-project-venv
    ```
    This tells `pyenv` to use the `ethereum-project-venv` environment for this directory.
3.  **Create a `.envrc` file**: In your project root (`/Users/ianlucas/agent_system`), create a file named `.envrc` with the following content:
    ```bash
    # For .envrc
    use pyenv
    # Or, if 'use pyenv' doesn't pick up the virtualenv correctly:
    # layout python <path_to_your_python_executable_in_venv>
    # e.g. layout python $(pyenv which python)

    # You can also add other environment-specific commands here,
    # for example, to load variables from your .env file:
    # dotenv
    ```
4.  **Allow `direnv`**: The first time you `cd` into the directory (or when `.envrc` changes), `direnv` will show a message saying it's blocked. Run `direnv allow` in your terminal to enable it for this project.

Now, whenever you navigate to your project directory in the terminal, `direnv` should automatically configure your shell to use the `ethereum-project-venv` environment managed by `pyenv`.

### Cursor-Specific Settings

Your IDE, Cursor, might also have built-in features or extensions to automatically activate a virtual environment when a project is loaded. Check Cursor's documentation or settings for "Python interpreter selection" or "terminal profiles" that might allow project-specific configurations. 