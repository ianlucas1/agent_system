import argparse
from chat_session import ChatSession

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

    print(f"Attempting to initialize chat with {args.model.upper()} model.")
    chat_session = ChatSession()
    if args.model == "openai" and not chat_session.openai_available:
        print("Cannot start chat: OpenAI model is not available. Please check API key and installation.")
        return
    if args.model == "gemini" and not chat_session.gemini_available:
        print("Cannot start chat: Gemini model is not available. Please check API key and installation.")
        return
    if args.model == "both":
        if not chat_session.openai_available or not chat_session.gemini_available:
            print("Cannot start chat: Both models must be available (OpenAI or Gemini missing).")
            return
    print(f"Starting chat with {args.model.upper()}. Type 'exit' or 'quit' to end.")

    while True:
        try:
            user_input = input("You: ")
            if user_input is None:
                # In some environments, Ctrl+D might result in None
                print("Exiting chat.")
                break
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat.")
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
            print("\nExiting chat due to interrupt.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue

if __name__ == "__main__":
    main() 