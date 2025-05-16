from typing import List, Dict, Optional
import logging

# Attempt to import API libraries
try:
    from openai import OpenAI

    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    OpenAI = None  # Define for type hinting even if not available

try:
    import tiktoken  # Added for OpenAI token counting

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

try:
    import google.generativeai as genai

    GOOGLE_SDK_AVAILABLE = True
except ImportError:
    GOOGLE_SDK_AVAILABLE = False
    genai = None  # Define for type hinting

# Get a logger for this module
logger = logging.getLogger(__name__)

# Token accounting
from src.shared.usage_logger import UsageLogger


class OpenAIClientManager:
    def __init__(self, api_key: Optional[str], default_model_name: str = "o3"):
        self.client: Optional["OpenAI"] = None
        self.model_name: str = default_model_name
        self._available: bool = False

        if api_key and OPENAI_SDK_AVAILABLE:
            try:
                self.client = OpenAI(api_key=api_key)
                self._available = True
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
                self.client = None
                self._available = False
        elif not OPENAI_SDK_AVAILABLE:
            logger.warning(
                "OpenAI SDK not installed. OpenAIClientManager will be unavailable."
            )
        elif not api_key:
            logger.warning(
                "OpenAI API key not provided. OpenAIClientManager will be unavailable."
            )

    @property
    def available(self) -> bool:
        return self._available and self.client is not None

    def get_model_name(self) -> str:
        return self.model_name

    def set_model_name(self, model_name: str) -> None:
        if model_name:
            self.model_name = model_name
            # OpenAI client typically doesn't need re-initialization for just a model name change
            # as the model is specified in each API call.

    def generate_response(self, history: List[Dict[str, str]]) -> str:
        if not self.available:
            return "⚠️ OpenAI model is not available (client not initialized or SDK missing)."
        if not self.client:  # Should be caught by self.available but as a safeguard
            return "⚠️ OpenAI client is None, though manager reported as available."

        try:
            response = self.client.chat.completions.create(
                model=self.model_name, messages=history
            )
            # -------------------------------------------------------------
            # Token accounting: leverage the OpenAI response.usage field if
            # available; otherwise fall back to estimating via tiktoken.
            # -------------------------------------------------------------
            tokens_used = 0
            try:
                if hasattr(response, "usage") and response.usage is not None:
                    # Newer OpenAI SDK exposes prompt_tokens/completion_tokens/total_tokens
                    usage_obj = response.usage  # type: ignore[attr-defined]
                    if hasattr(usage_obj, "total_tokens") and usage_obj.total_tokens:
                        tokens_used = usage_obj.total_tokens  # type: ignore[attr-defined]
                    elif (
                        hasattr(usage_obj, "prompt_tokens")
                        and hasattr(usage_obj, "completion_tokens")
                    ):
                        tokens_used = (
                            (usage_obj.prompt_tokens or 0)
                            + (usage_obj.completion_tokens or 0)
                        )
                else:
                    # Fallback: estimate using token counter helper
                    prompt_text = "\n".join(m.get("content", "") for m in history)
                    tokens_used = self.count_tokens(prompt_text)
                    tokens_used += self.count_tokens(response.choices[0].message.content)
            except Exception as e_tok:
                logger.debug(f"Unable to determine token usage: {e_tok}")
                tokens_used = 0

            if tokens_used:
                UsageLogger.inc("openai", tokens_used)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error communicating with OpenAI: {e}", exc_info=True)
            return f"Error communicating with OpenAI: {e}"

    def count_tokens(self, text: str) -> int:
        """Counts tokens in a string using tiktoken for the current OpenAI model."""
        if not text:
            return 0
        if not self.available or not TIKTOKEN_AVAILABLE:
            # Fallback if client or tiktoken is not available
            logger.warning(
                "OpenAI client or tiktoken not available for token counting. Using word count."
            )
            return len(text.split())

        try:
            # self.model_name should be the string name like "gpt-4o-mini"
            encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            # Fallback for models not directly in tiktoken, e.g., potentially newer ones
            # cl100k_base is a common encoding for gpt-3.5-turbo and gpt-4 based models
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
            except Exception as e_enc:
                logger.warning(
                    f"Error getting tiktoken encoding (cl100k_base) for {self.model_name}: {e_enc}. Using word count."
                )
                return len(text.split())
        except Exception as e_model_name:
            logger.warning(
                f"Error getting tiktoken encoding for model {self.model_name}: {e_model_name}. Using word count."
            )
            return len(text.split())

        return len(encoding.encode(text))


class GeminiClientManager:
    def __init__(
        self,
        api_key: Optional[str],
        default_model_name: str = "gemini-2.5-pro-preview-05-06",
    ):
        self.client: Optional["genai.GenerativeModel"] = None
        self.model_name: str = default_model_name
        self._available: bool = False
        self._api_key: Optional[str] = api_key  # Store api_key for re-initialization

        if api_key and GOOGLE_SDK_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(self.model_name)
                self._available = True
            except Exception as e:
                logger.error(
                    f"Failed to initialize Gemini client ({self.model_name}): {e}",
                    exc_info=True,
                )
                self.client = None
                self._available = False
        elif not GOOGLE_SDK_AVAILABLE:
            logger.warning(
                "Google Generative AI SDK not installed. GeminiClientManager will be unavailable."
            )
        elif not api_key:
            logger.warning(
                "Google API key not provided. GeminiClientManager will be unavailable."
            )

    @property
    def available(self) -> bool:
        return self._available and self.client is not None

    def get_model_name(self) -> str:
        return self.model_name

    def set_model_name(self, model_name: str) -> bool:
        """
        Sets the model name. If the name changes and the client is available,
        it attempts to re-initialize the client.
        Returns True if successful or no change needed, False if re-initialization failed.
        """
        if not model_name:
            return False  # Or raise error? For now, just fail silently or log.

        if self.model_name == model_name and self.client is not None:
            return True  # No change needed

        self.model_name = model_name

        if not self._api_key or not GOOGLE_SDK_AVAILABLE:
            # Cannot re-initialize if key or SDK was missing initially
            self._available = False
            self.client = None
            logger.warning(
                "Gemini client cannot be re-initialized: API key or SDK missing."
            )
            return False

        # Attempt to re-initialize
        try:
            # genai.configure should have been called already
            self.client = genai.GenerativeModel(self.model_name)
            self._available = True  # Mark as available again if re-init succeeds
            logger.info(f"Gemini client re-initialized to model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(
                f"Error re-initializing Gemini client for model {self.model_name}: {e}",
                exc_info=True,
            )
            self.client = None
            self._available = False  # Mark as unavailable on failure
            return False

    def _format_history_for_gemini(self, history: List[Dict[str, str]]) -> str:
        prompt_parts = []
        for message in history:
            role = message["role"]
            content = message["content"]
            if role == "system":
                # Gemini doesn't have a direct "system" role in the same way as OpenAI for its basic text API.
                # Prepend system message content, or integrate it into the first user message if appropriate.
                # For now, let's just add it as a preamble.
                prompt_parts.append(f"System Information: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        # The final "Assistant:" turn is usually added by the calling code before sending to Gemini
        # to prompt its response. Here we just concatenate the history.
        return "\n\n".join(prompt_parts)

    def generate_response(self, history: List[Dict[str, str]]) -> str:
        if not self.available:
            return "⚠️ Gemini model is not available (client not initialized or SDK missing)."
        if not self.client:
            return "⚠️ Gemini client is None, though manager reported as available."

        # Construct the prompt from history
        # Gemini's basic generate_content often takes a single string prompt.
        # The history needs to be formatted appropriately.
        # The ChatSession used to append "Assistant:" to the prompt. Let's ensure the manager gets the raw history.

        prompt_string = self._format_history_for_gemini(history)
        # Add the final "Assistant:" to cue the model, if this is standard practice for the version of SDK/API.
        # Based on original ChatSession, it added "Assistant:" to a manually constructed prompt string.
        # So, if the _format_history_for_gemini doesn't add a trailing Assistant part based on last role,
        # it might be needed here or assumed to be part of the last user message content for the API.
        # For now, assuming formatted_prompt is ready.
        # The existing ChatSession logic for Gemini:
        # prompt = ""
        # for msg in self.gemini_history: ... prompt += f"Role: {content}\n"
        # prompt += "Assistant:"
        # So, the calling code (ChatSession) should ensure the history is appropriate,
        # or this manager should fully take over prompt construction including the final cue.
        # Let's refine _format_history_for_gemini to produce the full prompt string.

        # Re-evaluating gemini prompt construction.
        # The `genai.GenerativeModel(model_name)` can often handle chat history directly
        # with `start_chat(history=...)` and then `send_message()`.
        # Or, `generate_content` can take a list of `glm.Content` objects.
        # Let's adapt to use the list of dicts more directly if the SDK supports it well.
        # For now, sticking to reconstructing the string prompt as per original ChatSession logic for minimal change.

        full_prompt = (
            prompt_string + "\n\nAssistant:"
        )  # Mimicking original ChatSession prompt construction

        try:
            response = self.client.generate_content(full_prompt)
            # Ensure response.text is the correct way to access content.
            # Original code used response.text
            # -------------------------------------------------------------
            # Token accounting (Gemini) – use SDK-provided count if possible
            # else estimate via word/token count helper.
            # -------------------------------------------------------------
            try:
                tokens_used = 0
                if hasattr(response, "usage_metadata") and getattr(
                    response, "usage_metadata", None
                ) is not None:
                    usage_md = response.usage_metadata
                    if hasattr(usage_md, "total_tokens") and usage_md.total_tokens:
                        tokens_used = usage_md.total_tokens  # type: ignore[attr-defined]
                if tokens_used == 0:
                    # Estimate: prompt + response tokens
                    tokens_used = self.count_tokens(full_prompt)
                    tokens_used += self.count_tokens(response.text)
                if tokens_used:
                    UsageLogger.inc("gemini", tokens_used)
            except Exception as e_tok:
                logger.debug(f"Unable to determine Gemini token usage: {e_tok}")

            return response.text
        except Exception as e:
            logger.error(f"Error communicating with Gemini: {e}", exc_info=True)
            return f"Error communicating with Gemini: {e}"

    def count_tokens(self, text: str) -> int:
        """Counts tokens in a string using the Gemini client SDK method or a fallback."""
        if not text:
            return 0

        if self.available and self.client and hasattr(self.client, "count_tokens"):
            try:
                # Assuming self.client is the GenerativeModel instance
                token_count_response = self.client.count_tokens(text)
                return token_count_response.total_tokens
            except Exception as e:
                logger.warning(
                    f"Error using Gemini SDK count_tokens for model {self.model_name}: {e}. Using word count."
                )
                return len(text.split())  # Fallback on error
        else:
            # Fallback if client is not available or doesn't have count_tokens method
            if not self.available or not self.client:
                logger.warning(
                    f"Warning: Gemini client for model {self.model_name} not available for token counting. Using word count."
                )
            elif not hasattr(self.client, "count_tokens"):
                logger.warning(
                    f"Warning: Gemini client for model {self.model_name} does not have count_tokens method. Using word count."
                )
            return len(text.split())
