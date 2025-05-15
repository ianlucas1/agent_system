import argparse
from src.core.chat_session import ChatSession
import logging
from src import config

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Command-line chat interface for LLMs.")
    parser.add_argument(
        "--model",
        type=str,
        choices=["openai", "gemini", "both"],
        default="openai",
        help="Specify the LLM to chat with: 'openai', 'gemini', or 'both'. Default is openai."
    )
    args = parser.parse_args()

    logger.info(f"Attempting to initialize chat with {args.model.upper()} model via CLI.")
    chat_session = ChatSession()
    if args.model == "openai" and not chat_session.openai_available:
        logger.error("Cannot start chat: OpenAI model is not available. Please check API key and installation.")
        return
    if args.model == "gemini" and not chat_session.gemini_available:
        logger.error("Cannot start chat: Gemini model is not available. Please check API key and installation.")
        return
    if args.model == "both":
        # TODO: Implement 'both' (A2A collaboration) model logic
        # This will likely involve calling a method on chat_session or a dedicated collaboration module
        # and ensuring both openai_manager and gemini_manager are available and their clients accessible.
        if not chat_session.openai_available or not chat_session.gemini_available:
            logger.error("Cannot start chat: Both models must be available for 'both' mode (OpenAI or Gemini missing).")
            return
        logger.info("'both' model mode selected - A2A collaboration to be implemented.")
        # For now, we can prevent it from running further or default to one model
        # For this refactor, let's just acknowledge and prevent it from proceeding if selected.
        # If you want to test, you might default it to 'openai' or 'gemini' for now.
        # For a real implementation, ChatSession.process_user_message would need to handle model_choice="both"

    logger.info(f"Starting chat with {args.model.upper()}. Type 'exit' or 'quit' to end.")

    while True:
        try:
            user_input = input("You: ")
            if user_input is None:
                # In some environments, Ctrl+D might result in None
                logger.info("Exiting chat due to None input (Ctrl+D).")
                break
            if user_input.lower() in ["exit", "quit"]:
                logger.info("Exiting chat due to user command (exit/quit).")
                break
            if not user_input.strip():
                continue

            responses = chat_session.process_user_message(user_input, model_choice=args.model)
            for sender, message in responses:
                if sender == "openai":
                    print(f"Agent (OpenAI): {message}")
                elif sender == "gemini":
                    print(f"Agent (Gemini): {message}")
                elif sender == "collab":
                    print(f"Agent (OpenAI & Gemini): {message}")
                else:
                    print(f"Agent: {message}")

        except KeyboardInterrupt:
            logger.info("\nExiting chat due to interrupt.")
            break
        except Exception as e:
            logger.exception(f"An error occurred in CLI main loop: {e}")
            continue

if __name__ == "__main__":
    main() 