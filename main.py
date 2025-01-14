import os
import openai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, static_folder="static")

load_dotenv()  # Loads .env file

openai.api_key = os.getenv("OPENAI_API_KEY")

# ----------------------------------------------------------------
# A dictionary to store instructions/intent for each psychological stage
# ----------------------------------------------------------------
STAGES = {
    1: {
        "name": "Establish Psychological Safety & Trust",
        "instruction": (
            "Your priority is to make the user feel safe and at ease. "
            "Reassure them they have full control, clarify the purpose of reflection, "
            "and start with gentle, open-ended questions. Keep your tone calm and empathetic."
        )
    },
    2: {
        "name": "Clarify the User’s Desired Outcome",
        "instruction": (
            "Help the user clarify their goals or the main issue they wish to address. "
            "Ask questions to uncover why this matters to them. Keep them focused on identifying "
            "the outcome they most desire."
        )
    },
    3: {
        "name": "Explore Current Reality & Emotional Landscape",
        "instruction": (
            "Invite the user to expand on their current situation and emotions. "
            "Encourage them to label their feelings. Ask open-ended questions that allow "
            "for deeper exploration of challenges, thoughts, and recurring patterns."
        )
    },
    4: {
        "name": "Identify and Challenge Limiting Beliefs",
        "instruction": (
            "Listen for statements indicating limiting beliefs (like 'I can't,' 'I always,' 'I never'). "
            "Gently question these assumptions using Socratic questioning. Encourage perspective shifts."
        )
    },
    5: {
        "name": "Guide Toward Possible Solutions or Next Steps",
        "instruction": (
            "Help the user brainstorm and evaluate potential solutions or action steps. "
            "Focus on realistic, actionable ideas that align with their goals and resources."
        )
    },
    6: {
        "name": "Encourage Self-Monitoring & Reflection Loop",
        "instruction": (
            "Prompt the user to think about how they can keep track of progress. "
            "Suggest ways to self-reflect and adjust their plan over time."
        )
    },
    7: {
        "name": "Personalization & Context Awareness",
        "instruction": (
            "Reference the user's unique history, values, and previous reflections. "
            "Help them feel this process is tailored to them."
        )
    },
    8: {
        "name": "Sequencing & Nuance of Question Delivery",
        "instruction": (
            "Ensure questions are not overwhelming. Use progressive depth: start broad, "
            "gradually get more specific. Use language that is clear, empathetic, and non-judgmental."
        )
    },
    9: {
        "name": "Empathic Tone & Validation (Without Becoming Therapy)",
        "instruction": (
            "Validate the user’s feelings and experiences without providing clinical therapy. "
            "Offer empathy and understanding; avoid diagnostic language."
        )
    },
    10: {
        "name": "Ethical Boundaries & Referral Points",
        "instruction": (
            "If the user expresses severe distress, direct them to professional help. "
            "Remind them this reflection is not therapy. Provide resource links if needed."
        )
    },
}

def classify_stage(user_input, conversation_summary):
    """
    Calls GPT to decide which stage (1-10) best fits the user's current reflection needs
    based on:
      - The user's last input
      - The conversation summary so far
    
    The function returns an integer from 1 to 10 if successful,
    or None if it can't parse a valid answer.
    """

    # A more detailed classification prompt, giving GPT robust context:
    classification_prompt = f"""
We have 10 psychological stages of reflection with these detailed definitions:

1. Establish Psychological Safety & Trust
   - The user might be anxious, uncertain, or reluctant to share. 
   - Aim is to reduce threat response and build a sense of safety.

2. Clarify the User’s Desired Outcome
   - The user is uncertain about what they want or their main focus.
   - Aim is to uncover goals or clarify reasons for reflection.

3. Explore Current Reality & Emotional Landscape
   - The user is sharing experiences, emotions, challenges.
   - Aim is open-ended exploration, understanding context, labeling emotions.

4. Identify and Challenge Limiting Beliefs
   - The user expresses negative self-talk or absolute statements (e.g., "I can't," "I never," "I always").
   - Aim is to recognize and gently question these beliefs.

5. Guide Toward Possible Solutions or Next Steps
   - The user is ready to brainstorm or look for practical ideas.
   - Aim is to explore action steps, practical strategies.

6. Encourage Self-Monitoring & Reflection Loop
   - The user has potential actions or insights and wants to track progress.
   - Aim is to set up personal check-ins, accountability, or feedback loops.

7. Personalization & Context Awareness
   - The user needs deeply tailored questions referencing their values, history, or environment.
   - Aim is to make the reflection very relevant and personalized.

8. Sequencing & Nuance of Question Delivery
   - The user might be overwhelmed or need a carefully paced approach.
   - Aim is to ensure step-by-step progression, not bombarding them with complexity.

9. Empathic Tone & Validation (Without Becoming Therapy)
   - The user needs emotional validation but not clinical diagnosis.
   - Aim is to acknowledge feelings, show understanding, remain non-therapeutic.

10. Ethical Boundaries & Referral Points
    - The user indicates severe distress, potential crisis, or content that may require professional help.
    - Aim is to provide disclaimers, referral info, or direct them to professional resources.

Here are some examples of user statements and the stage they might most likely need:

- "I feel really scared opening up about this." → Stage 1 (Psychological Safety)
- "I’m not sure what I actually want in life." → Stage 2 (Clarify Outcome)
- "I feel anxious every time I think about my job." → Stage 3 (Explore Emotional Landscape)
- "I always fail at everything I do." → Stage 4 (Limiting Beliefs)
- "I want to find a solution to get past this problem." → Stage 5 (Possible Solutions)
- "How do I keep track of my progress over the next month?" → Stage 6 (Self-Monitoring)
- "My personal experiences with X factor really shape how I think about this." → Stage 7 (Personalization)
- "I might need a more step-by-step approach; this is too overwhelming." → Stage 8 (Sequencing & Nuance)
- "I’m feeling sad, and I just need some empathy." → Stage 9 (Empathic Tone & Validation)
- "I feel I’m in crisis; I’m really scared I might hurt myself." → Stage 10 (Ethical Boundaries & Referral)

Now, consider:

Conversation so far:
{conversation_summary}

The user's latest statement is the most important for deciding the next stage. Pay special attention to this statement:
\"\"\"{user_input}\"\"\"

**Instruction**: 
1) Decide which ONE stage (1-10) most closely matches the user's immediate reflective need.
2) Do not provide an explanation or reasoning in the final output. 
3) Only output a single number (1, 2, 3, ..., or 10).

If you are unsure, choose the stage that seems the closest match.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a reflection stage classifier. Reason internally but output only the stage number."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0.0,  # More deterministic
            max_tokens=10,
        )
        # Extract raw text
        stage_text = response.choices[0].message["content"].strip()
        # Attempt to parse an integer from the response
        possible_stage = int("".join(filter(str.isdigit, stage_text)))
        if 1 <= possible_stage <= 10:
            return possible_stage

    except Exception as e:
        print(f"Error in classify_stage: {e}")

    return None  # fallback if unable to parse

# ----------------------------------------------------------------
# Helper function: Summarize the user's last input
# ----------------------------------------------------------------
def summarize_text(text):
    """
    Summarizes the user's latest input to keep conversation memory concise.
    You can refine or replace this approach with your own summarization logic.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes text succinctly."},
        {"role": "user", "content": f"Please summarize the following text in 1-2 sentences:\n\n{text}"}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2,
            max_tokens=60,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"Error calling OpenAI for summarization: {e}")
        return text  # fallback: just return original text if error

# ----------------------------------------------------------------
# Helper function: Chat with GPT in the context of a specific stage
# ----------------------------------------------------------------
def stage_chat(stage_id, conversation_summary, user_input):
    """
    Build a dynamic system prompt that:
      1) Declares which stage we are in and why
      2) Provides stage-specific instructions
      3) Shares a short summary of conversation so far
      4) Includes the new user input
    """
    stage_name = STAGES[stage_id]["name"]
    stage_instruction = STAGES[stage_id]["instruction"]

    # Build system message with stage context
    system_message = {
        "role": "system",
        "content": (
            f"You are a highly skilled reflection coach with 50 years' experience. "
            f"Your role is to guide the user through reflection by asking powerful, stage-specific questions. "
            f"Do NOT provide any affirmations, opinions, or prescriptive advice except in Stage 10.\n\n"
            f"Stage Context:\n"
            f"- Current Stage: {stage_id} - {stage_name}\n"
            f"- Stage Goal: {stage_instruction}\n\n"
            f"Instructions for this Response:\n"
            f"1. ONLY ask a single open-ended, stage-appropriate question.\n"
            f"2. Do NOT include affirmations, guidance, or advice unless Stage 10.\n"
            f"3. Your tone must align with the stage-specific context and goal.\n"
            f"4. Avoid generic or repetitive phrasing; your question must be thoughtful and relevant.\n\n"
            f"Conversation Summary so far: {conversation_summary}\n\n"
            f"User's Latest Statement: \"{user_input}\"\n\n"
            f"Now, ask a single, stage-appropriate question."
        )
    }

    # The user message for this turn
    user_message = {"role": "user", "content": user_input}

    if stage_id == 10:
        return (
            "It sounds like you may be in a crisis or need urgent support. "
            "Please prioritize your safety and reach out to a trusted professional or emergency service immediately. "
            "Can you share if you've already contacted someone or how I can guide you further?"
        )

    # Call the API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "I'm sorry, I encountered an error."

# ----------------------------------------------------------------
# Simple function to decide whether to move to the next stage
# (You can implement more advanced NLP-based logic here)
# ----------------------------------------------------------------
def determine_next_stage(user_input, current_stage, conversation_summary):
    """
    1. If user explicitly says "move on" or "next stage," jump to next stage (unless at 10).
    2. Otherwise, call classify_stage() to see what stage GPT recommends.
    3. If classify_stage() returns a valid stage, jump to it (or stay put if that logic suits you).
    4. Fallback: remain in current_stage.
    """
    lower_input = user_input.lower()

    # 1. Check if user explicitly requests to move on to next stage
    if "move on" in lower_input or "next stage" in lower_input:
        if current_stage < 10:
            return current_stage + 1
        else:
            return current_stage  # already at 10

    # 2. Otherwise, use GPT classification to see what stage is most relevant
    recommended_stage = classify_stage(user_input, conversation_summary)
    if recommended_stage:
        # Example logic: always jump to the recommended stage if it's higher than current_stage
        # If you want to allow backward jumps, remove or modify the check below
        if recommended_stage:
            return recommended_stage  # Allow movement to any recommended stage, higher or lower

# ----------------------------------------------------------------
# Main Reflection Flow
# ----------------------------------------------------------------
def run_reflection_session():
    print("=== Reflection App (V1 - Multi-Stage) ===")

    current_stage = 1  # Start at stage 1 (Psychological Safety)
    conversation_summary = "No conversation yet."

    # Initial user check-in
    user_input = input("\n[You] Welcome! How are you feeling today? (Type your response) \n> ")

    # Summarize the user's initial response
    summarized = summarize_text(user_input)
    conversation_summary = summarized  # update global summary

    # Determine the stage based on the first input
    current_stage = classify_stage(user_input, conversation_summary)
    if not current_stage:
        current_stage = 1  # Fallback to Stage 1 if classification fails

    # Get GPT's first response for the determined stage
    assistant_reply = stage_chat(current_stage, conversation_summary, user_input)
    print(f"\n[Reflection Coach | Stage {current_stage}]: {assistant_reply}")

    while True:
        user_input = input("\n[You] (Type your reply or 'exit' to end) \n> ")

        if user_input.lower() in ["exit", "quit"]:
            print("\n[Reflection Coach] Thank you for reflecting with me. Take care!")
            break

        # Summarize user input to keep track of key points
        summarized_input = summarize_text(user_input)
        # Update the conversation summary (append new summarized input)
        conversation_summary += f" | {summarized_input}"

        # Check if we should move to a new stage
        new_stage = determine_next_stage(user_input, current_stage, conversation_summary)
        if new_stage != current_stage:
            print(f"\n[System] Moving from Stage {current_stage} to Stage {new_stage}...\n")
            current_stage = new_stage


        # Get GPT's response for the current stage
        assistant_reply = stage_chat(current_stage, conversation_summary, user_input)
        print(f"\n[Reflection Coach | Stage {current_stage}]: {assistant_reply}")

@app.route("/")
def index():
    return render_template("index.html")  # Frontend UI

# Global state variables
conversation_summary = "No conversation yet."  # Initialize summary globally
current_stage = 1  # Default starting stage

@app.route("/get_response", methods=["POST"])
def get_response():
    global conversation_summary, current_stage  # Maintain state between requests

    user_input = request.json.get("message", "")  # Get user input from the frontend
    response_message = ""

    try:
        if user_input.strip() == "":  # If the user hasn't entered any input (first question)
            response_message = "Hey, so what brings you here? :)"
        else:
            # Summarize user input and append it to the conversation summary
            summarized_input = summarize_text(user_input)
            conversation_summary += f" | {summarized_input}"  # Update global conversation state

            # Determine if we need to move to the next stage
            new_stage = determine_next_stage(user_input, current_stage, conversation_summary)
            if new_stage != current_stage:
                current_stage = new_stage  # Update the stage globally

            # Generate GPT response for the current stage
            response_message = stage_chat(current_stage, conversation_summary, user_input)

    except Exception as e:
        print(f"Error in /get_response: {e}")
        response_message = "I'm sorry, something went wrong."

    return jsonify({"message": response_message})

# ----------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)