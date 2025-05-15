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