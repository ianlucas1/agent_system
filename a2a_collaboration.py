"""
a2a_collaboration.py - Optional module to facilitate Agents-to-Agents collaboration between OpenAI and Gemini.
If both models are available, this module orchestrates a dialogue loop and returns a combined answer.
"""
def run(user_message: str, openai_client, gemini_client) -> str:
    """
    Run a collaborative dialogue between OpenAI (Agent A) and Google Gemini (Agent B) on the given user_message.
    Returns the final answer after agents' interaction.
    openai_client: the OpenAI API module or client (must have ChatCompletion.create)
    gemini_client: the Google Generative AI model client (must have generate_content)
    """
    if openai_client is None or gemini_client is None:
        return "Error: Both OpenAI and Gemini clients must be initialized for A2A collaboration."
    question = user_message
    # Round 1: Agent A (OpenAI) gives initial answer
    try:
        response = openai_client.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}]
        )
        openai_answer = response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error from OpenAI agent: {e}"
    # Round 2: Agent B (Gemini) provides critique or additional insight
    try:
        critique_prompt = (f"User's question: {question}\n"
                           f"Agent A's answer: {openai_answer}\n"
                           "Agent B, provide your feedback or improvements to Agent A's answer.")
        gemini_response = gemini_client.generate_content(critique_prompt)
        gemini_feedback = gemini_response.text
    except Exception as e:
        return f"Error from Gemini agent: {e}"
    # Round 3: Agent A (OpenAI) refines answer based on Agent B's feedback
    try:
        refine_messages = [
            {"role": "system", "content": "You are Agent A. Another agent (Agent B) has given feedback on your answer."},
            {"role": "user", "content": f"Question: {question}\nYour original answer: {openai_answer}\nAgent B's feedback: {gemini_feedback}\nPlease provide an improved final answer."}
        ]
        final_response = openai_client.ChatCompletion.create(
            model="gpt-4",
            messages=refine_messages
        )
        final_answer = final_response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error during answer refinement: {e}"
    return final_answer
