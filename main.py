import os
import openai
from dotenv import load_dotenv

load_dotenv()  # Loads .env file

openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------
# Helper Function to Call the ChatGPT 3.5 API
# ---------------------------------------------------------
def chat_with_gpt(messages):
    """
    Sends a list of messages (dicts) to the OpenAI ChatCompletion endpoint.
    Returns the response text from the assistant.
    
    :param messages: A list of messages in the format:
                     [{"role": "system"|"user"|"assistant", "content": "..."}]
    :return: The content of the assistant's response.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,      # Adjust for more/less creative responses
            max_tokens=300,       # Adjust for desired response length
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "I'm sorry, I encountered an error."

# ---------------------------------------------------------
# Basic Reflection Flow
# ---------------------------------------------------------
def run_reflection_session():
    """
    A simple interactive loop that demonstrates a basic reflection session.
    You can expand this to include multiple 'stages' or to detect
    user needs in real time (writing vs. voice, short vs. long, etc.).
    """

    # 1. System instructions (context) for ChatGPT to serve as reflection guide
    system_context = {
        "role": "system",
        "content": (
            "You are a highly skilled reflection coach with 50 years of experience. "
            "You adapt your style based on user input. You gently guide the user to reflect, "
            "but you're not a therapist. You create psychological safety, ask powerful questions, "
            "and help them gain insights and action steps if needed."
        )
    }

    # 2. Start the conversation with a check-in stage
    messages = [system_context]
    user_input = input("Welcome! How are you feeling today? (Type your response) \n> ")
    messages.append({"role": "user", "content": user_input})

    # First assistant response
    reflection_response = chat_with_gpt(messages)
    print(f"\n[Reflection Coach]: {reflection_response}")

    # 3. Simple loop to continue the session
    while True:
        user_input = input("\n(Type your reply or 'exit' to end) \n> ")

        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for reflecting. Take care!")
            break

        # Append user message
        messages.append({"role": "user", "content": user_input})
        
        # Get assistant response
        reflection_response = chat_with_gpt(messages)
        print(f"\n[Reflection Coach]: {reflection_response}")
        
        # For a real V1, you could insert logic here:
        # - If user says "I only have 2 minutes," switch to a "timed writing" style prompt.
        # - If user expresses confusion, pivot to a "clarify your goals" stage, etc.

# ---------------------------------------------------------
# Main entry point
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== Reflection App (V1) ===")
    run_reflection_session()