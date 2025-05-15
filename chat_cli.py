import argparse
import os
from dotenv import load_dotenv

# API clients
openai_client = None
gemini_client = None

def initialize_clients():
    """Load API keys and initialize clients."""
    global openai_client, gemini_client
    load_dotenv() # Load environment variables from .env

    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if openai_api_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            print("OpenAI client initialized successfully.")
        except ImportError:
            print("OpenAI library not found. Please install it with 'pip install openai'")
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
    else:
        print("Warning: OPENAI_API_KEY not found in .env. OpenAI model will not be available.")

    if google_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_api_key)
            gemini_client = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
            print("Google Gemini client initialized successfully.")
        except ImportError:
            print("Google GenerativeAI library not found. Please install it with 'pip install google-generativeai'")
        except Exception as e:
            print(f"Failed to initialize Google Gemini client: {e}")
    else:
        print("Warning: GOOGLE_API_KEY not found in .env. Gemini model will not be available.")

def send_to_openai(message):
    """Sends a message to OpenAI and gets a response."""
    if not openai_client:
        return "OpenAI client not initialized. Please check your OPENAI_API_KEY and ensure the client was initialized."
    try:
        response = openai_client.chat.completions.create(
            model="o4-mini", # Updated to gpt-4.1 as per user request
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with OpenAI: {e}"

def send_to_gemini(message):
    """Sends a message to Gemini and gets a response."""
    if not gemini_client:
        return "Gemini client not initialized. Please check your GOOGLE_API_KEY and ensure the client was initialized."
    try:
        response = gemini_client.generate_content(message)
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini: {e}"

def main():
    parser = argparse.ArgumentParser(description="Command-line chat interface for LLMs.")
    parser.add_argument(
        "--model",
        type=str,
        choices=["openai", "gemini"],
        default="openai", # Default to OpenAI
        help="Specify the LLM to chat with (openai or gemini). Default is openai."
    )
    args = parser.parse_args()

    print(f"Attempting to initialize chat with {args.model.upper()} model.")
    initialize_clients()

    if args.model == "openai" and not openai_client:
        print("Cannot start chat: OpenAI client failed to initialize. Please check API key and library installation.")
        return
    if args.model == "gemini" and not gemini_client:
        print("Cannot start chat: Gemini client failed to initialize. Please check API key and library installation.")
        return
    
    print(f"Starting chat with {args.model.upper()}. Type 'exit' or 'quit' to end.")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat.")
                break

            if not user_input.strip():
                continue

            agent_response = ""
            if args.model == "openai":
                if not openai_client:
                    print("Agent: OpenAI client is not available.")
                    continue
                agent_response = send_to_openai(user_input)
            elif args.model == "gemini":
                if not gemini_client:
                    print("Agent: Gemini client is not available.")
                    continue
                agent_response = send_to_gemini(user_input)
            
            print(f"Agent: {agent_response}")

        except KeyboardInterrupt:
            print("\nExiting chat due to interrupt.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            # Optionally, decide if you want to break the loop on all errors
            # For now, it continues unless it's a KeyboardInterrupt or unhandled client init
            # but LLM communication errors will be printed and loop continues.
            # Consider if a critical error should break. For now, let's keep it simple.
            # break # Uncomment to exit on any error during chat.

if __name__ == "__main__":
    main() 