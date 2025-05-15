"""
collaboration.py - Optional module to facilitate Agents-to-Agents collaboration between OpenAI and Gemini.
If both models are available, this module orchestrates a dialogue loop and returns a combined answer.
"""

import logging
from typing import Any

# Assuming OPENAI_API_KEY and GOOGLE_API_KEY are managed by the calling environment (e.g. via ChatSession using config.py)
# Also assuming the client objects passed in are already initialized instances.
# For type hinting, we might need to import the client types if they are not just 'Any'
# from openai import OpenAI # Example for type hint
# from google.generativeai.generative_models import GenerativeModel # Example for type hint

logger = logging.getLogger(__name__)


def run(user_message: str, openai_client: Any, gemini_client: Any) -> str:
    """
    Run a collaborative dialogue between OpenAI (Agent A) and Google Gemini (Agent B) on the given user_message.
    Returns the final answer after agents' interaction.
    openai_client: An initialized OpenAI client instance (e.g., from OpenAIClientManager.client).
    gemini_client: An initialized Google Generative AI model client instance (e.g., from GeminiClientManager.client).
    """
    logger.info(
        f"Starting A2A collaboration for user message: '{user_message[:50]}...'"
    )
    if openai_client is None or gemini_client is None:
        logger.error(
            "A2A collaboration error: Both OpenAI and Gemini clients must be provided."
        )
        return "Error: Both OpenAI and Gemini clients must be initialized for A2A collaboration."

    question = user_message
    openai_answer = ""
    gemini_feedback = ""

    # Round 1: Agent A (OpenAI) gives initial answer
    try:
        logger.debug("A2A Round 1: OpenAI generating initial answer.")
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Consider making this configurable
            messages=[{"role": "user", "content": question}],
        )
        openai_answer = response.choices[0].message.content
        logger.debug(f"A2A Round 1: OpenAI initial answer: '{openai_answer[:100]}...'")
    except Exception as e:
        logger.error(f"A2A Error from OpenAI agent (Round 1): {e}", exc_info=True)
        return f"Error from OpenAI agent: {e}"

    # Round 2: Agent B (Gemini) provides critique or additional insight
    try:
        logger.debug("A2A Round 2: Gemini generating feedback.")
        critique_prompt = (
            f"User's question: {question}\n"
            f"Agent A's answer: {openai_answer}\n"
            "Agent B, provide your feedback or improvements to Agent A's answer."
        )
        gemini_response = gemini_client.generate_content(critique_prompt)
        gemini_feedback = gemini_response.text
        logger.debug(f"A2A Round 2: Gemini feedback: '{gemini_feedback[:100]}...'")
    except Exception as e:
        logger.error(f"A2A Error from Gemini agent (Round 2): {e}", exc_info=True)
        return f"Error from Gemini agent: {e}"

    # Round 3: Agent A (OpenAI) refines answer based on Agent B's feedback
    try:
        logger.debug("A2A Round 3: OpenAI refining answer.")
        refine_messages = [
            {
                "role": "system",
                "content": "You are Agent A. Another agent (Agent B) has given feedback on your answer.",
            },
            {
                "role": "user",
                "content": f"Question: {question}\nYour original answer: {openai_answer}\nAgent B's feedback: {gemini_feedback}\nPlease provide an improved final answer.",
            },
        ]
        final_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Consider making this configurable
            messages=refine_messages,
        )
        final_answer = final_response.choices[0].message.content
        logger.info(
            f"A2A collaboration completed. Final answer: '{final_answer[:100]}...'"
        )
    except Exception as e:
        logger.error(
            f"A2A Error during answer refinement (Round 3): {e}", exc_info=True
        )
        return f"Error during answer refinement: {e}"

    return final_answer
