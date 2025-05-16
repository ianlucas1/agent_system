import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

# Example: Get a logger for this module itself (optional, mostly for app entry points)
# logger = logging.getLogger(__name__)
# logger.info("Logging configured.")
# --- End Logging Configuration ---

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Default Model Names
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o3")
DEFAULT_GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL", "gemini-2.5-pro-preview-05-06"
)  # Matched default from ChatSession

# Available Model Lists (previously in chat_gui.py)
# These should be updated to reflect actual, valid model names intended for support.
AVAILABLE_OPENAI_MODELS = ["gpt-4.1", "o4-mini", "o3"]

AVAILABLE_GEMINI_MODELS = [
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-preview-04-17"
]

# System Prompt for ChatSession (optional, can still be in ChatSession if preferred)
# For true centralization, it could live here.
# DEFAULT_SYSTEM_PROMPT = ("You are a helpful AI assistant. You have access to a local project file system. "
#                          "You can read files, write files (with user confirmation), and list directories when asked.")

# Add any other global configurations here, e.g.:
# MAX_FILE_READ_BYTES = 100 * 1024
# MAX_FILE_READ_LINES = 200

# You can also add functions here if complex config logic is needed.
# def get_model_info(provider: str, model_name: str) -> dict:
#     # ... logic to fetch model details ...
#     pass

# print("Config loaded:")
# print(f" DEFAULT_OPENAI_MODEL: {DEFAULT_OPENAI_MODEL}")
# print(f" AVAILABLE_OPENAI_MODELS: {AVAILABLE_OPENAI_MODELS}")
