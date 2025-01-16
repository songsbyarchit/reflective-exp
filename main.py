import os
import openai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import random
from questions import STAGE_QUESTIONS, HYPOTHETICAL_QUESTIONS
import logging
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

load_dotenv()  # Loads .env file

openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

last_user_input = ""  # Store the last state of the user's input

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
        "name": "Ethical Boundaries & Referral Points",
        "instruction": (
            "If the user expresses severe distress, direct them to professional help. "
            "Remind them this reflection is not therapy. Provide resource links if needed."
        )
    },
}

def classify_stage(user_input, conversation_summary):
    """
    Calls GPT to decide which stage (1-7) best fits the user's current reflection needs
    based on:
      - The user's last input
      - The conversation summary so far
    
    The function returns an integer from 1 to 7 if successful,
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

7. Ethical Boundaries & Referral Points
    - The user indicates severe distress, potential crisis, or content that may require professional help.
    - Aim is to provide disclaimers, referral info, or direct them to professional resources.

Here are some examples of user statements and the stage they might most likely need:

- "I feel really scared opening up about this." → Stage 1 (Psychological Safety)
- "I’m not sure what I actually want in life." → Stage 2 (Clarify Outcome)
- "I feel anxious every time I think about my job." → Stage 3 (Explore Emotional Landscape)
- "I always fail at everything I do." → Stage 4 (Limiting Beliefs)
- "I want to find a solution to get past this problem." → Stage 5 (Possible Solutions)
- "How do I keep track of my progress over the next month?" → Stage 6 (Self-Monitoring)
- "I feel I’m in crisis; I’m really scared I might hurt myself." → Stage 7 (Ethical Boundaries & Referral)

Now, consider:

Conversation so far:
{conversation_summary}

The user's latest statement is the most important for deciding the next stage. Pay special attention to this statement:
\"\"\"{user_input}\"\"\"

**Instruction**: 
1) Decide which ONE stage (1-7) most closely matches the user's immediate reflective need.
2) Do not provide an explanation or reasoning in the final output. 
3) Only output a single number (1, 2, 3, 4, 5, 6 or 7).

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
        if 1 <= possible_stage <= 7:
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
import random
from questions import STAGE_QUESTIONS, HYPOTHETICAL_QUESTIONS

def stage_chat(stage_id, conversation_summary, user_input):
    """
    Selects a stage-specific or hypothetical question based on a 50/50 chance.
    """
    stage_name = STAGES[stage_id]["name"]
    stage_instruction = STAGES[stage_id]["instruction"]

    # Always ask a generic stage-specific question
    system_message = {
        "role": "system",
        "content": (
            f"You are a highly skilled reflection coach with 50 years' experience. "
            f"Your role is to ask stage-specific questions that align with the current stage's goal "
            f"while tailoring the question to the user’s specific issue.\n\n"
            f"Stage Context:\n"
            f"- Current Stage: {stage_id} - {STAGES[stage_id]['name']}\n"
            f"- Stage Goal: {STAGES[stage_id]['instruction']}\n\n"
            f"Example of formatting a stage-specific question:\n"
            f"- User input: 'I always feel like I’m failing.'\n"
            f"- Stage: Identify and Challenge Limiting Beliefs (Stage 4)\n"
            f"'When you think about times you’ve succeeded, how does that change your perspective on failure?'\n\n"
            f"Now, ask a stage-specific question based on the user's input: {user_input}"
        )
    }

    # API logic for generating the response
    try:
        if stage_id == 7:
            return (
                "It sounds like you may be in a crisis or need urgent support. "
                "Please prioritize your safety and reach out to a trusted professional or emergency service immediately. "
                "Can you share if you've already contacted someone or how I can guide you further?"
            )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_message],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message["content"]

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "I'm sorry, I encountered an error."

# ----------------------------------------------------------------
# Function which simply tells the user a multiple choice question to give a rest from typing so they can just click an option
# ----------------------------------------------------------------
@app.route("/generate_think_smaller", methods=["POST"])
def generate_think_smaller():
    global conversation_summary, last_user_input
    logger.debug(f"Entered /generate_think_smaller with conversationSummary: {conversation_summary}, lastUserInput: {last_user_input}")
    try:
        # Get the updated conversation summary and last user input from the frontend
        data = request.get_json()
        logger.debug(f"Parsed request JSON: {data}")
        conversation_summary = data.get("conversationSummary", conversation_summary)
        last_user_input = data.get("lastUserInput", last_user_input)

        # Use the conversation summary and last user input as context
        system_message = {
            "role": "system",
            "content": (
                "You are a thoughtful assistant that creates reflection-focused multiple-choice questions. "
                "These questions are not meant to test the user's knowledge or have right or wrong answers. "
                "Instead, they are designed to help the user think more deeply about THOUGHTS and FEELINGS they've mentioned and continue journaling "
                "in a more guided and discrete way. The goal is to provide an easy break from long-form writing while encouraging "
                "reflection through thought-provoking options which take them deeper in the direction in which they've already been reflecting. "
                "Your output must strictly follow this exact format, including line breaks:\n\n"
                "<Insert question here>\n"
                "Option 1\n"
                "Option 2\n"
                "Option 3\n"
                "Something else\n\n"
                "Ensure the question is tailored to the user's input, and each option is concise (maximum 15 characters), realistic, and engaging. "
                "The fourth option must always be 'Something Else.' Do not include any numbering, letters, or additional punctuation."
            )
        }

        messages = [
            system_message,
            {
                "role": "user",
                "content": (
                    f"Here is the conversation summary so far:\n{conversation_summary}\n\n"
                    f"The user's latest input was:\n{last_user_input}\n\n"
                    "Using these details, generate a single multiple-choice question with four answer options."
                )
            }
        ]

        logger.debug(f"Calling OpenAI with conversationSummary: {conversation_summary} and lastUserInput: {last_user_input}")
        # Call GPT to generate the question and options
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=200,
        )

        response_text = response.choices[0].message["content"].strip()
        logger.debug(f"Received OpenAI response: {response_text}")
        lines = response_text.split("\n")
        if len(lines) < 5:
            logger.warning(f"Invalid response format: {response_text}")
            return jsonify({"error": "Invalid response format"}), 500

        question = lines[0]
        options = lines[1:5]
        logger.debug(f"Returning question: {question} with options: {options}")
        if len(options) == 4:
            return jsonify({"question": question, "options": options})
        else:
            logger.error(f"Invalid options generated: {options}")
            return jsonify({"error": "Failed to generate valid options"}), 500
    except Exception as e:
        logger.error(f"Error in /generate_think_smaller: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate question"}), 500

# ----------------------------------------------------------------
# Function which generates a summary
# ----------------------------------------------------------------
@app.route("/summarize_text", methods=["POST"])
def summarize_text_endpoint():
    try:
        data = request.get_json()
        # Accept input under either 'text' or 'choice' for compatibility
        input_text = data.get("text") or data.get("choice", "")
        if not input_text:
            return jsonify({"summary": ""}), 400

        summary = summarize_text(input_text)
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"Error in /summarize_text: {e}")
        return jsonify({"summary": ""}), 500


@app.route("/add_summary", methods=["POST"])
def add_summary():
    """
    Generate a contextual and logical sentence by combining a question and an answer.
    """
    try:
        # Parse incoming JSON data
        data = request.get_json()
        selected_option = data.get("selected_option", "").strip()  # The user's choice
        question_context = data.get("question_context", "").strip()  # The related question

        # Ensure both fields are present
        if not selected_option or not question_context:
            return jsonify({"error": "Missing question or selected option"}), 400

        # Build the AI prompt
        ai_prompt = f"""
        You are a helpful assistant that takes a question and an answer to form a logical, clear, and contextual sentence. 
        Ensure the sentence reads naturally and includes both the question and answer. 
        Examples:
        - Question: "What is your favorite drink?" 
          Answer: "Water" 
          Result: "My favorite drink is water."
        
        - Question: "What emotions do comfort foods evoke for you?" 
          Answer: "Comfort" 
          Result: "Comfort foods evoke the emotion of comfort for me."
        
        - Question: "What activity do you enjoy the most on weekends?" 
          Answer: "Hiking" 
          Result: "On weekends, I enjoy hiking the most."

        - Question: "Which skill would you like to improve?" 
          Answer: "Public speaking" 
          Result: "I would like to improve my public speaking skills."

        - Question: "What is the main source of your motivation?" 
          Answer: "Family" 
          Result: "The main source of my motivation is my family."


        Now, create a sentence based on the following:
        Question: "{question_context}"
        Answer: "{selected_option}"
        """

        # Call OpenAI to generate the sentence
        messages = [
            {"role": "system", "content": "You create logical and natural sentences based on questions and answers."},
            {"role": "user", "content": ai_prompt}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=50
        )

        # Extract the generated sentence
        generated_sentence = response.choices[0].message["content"].strip()

        # Log and return the result
        logger.info(f"Generated sentence: {generated_sentence}")
        return jsonify({"message": "Sentence added successfully", "generated_sentence": generated_sentence})

    except Exception as e:
        logger.error(f"Error in /add_summary: {e}", exc_info=True)
        return jsonify({"error": "Failed to add sentence"}), 500

# ----------------------------------------------------------------
# Function which simply tells the user how to think bigger with a powerful hypothetical question
# ----------------------------------------------------------------
@app.route("/generate_think_bigger", methods=["POST"])
def generate_think_bigger():
    global conversation_summary, last_user_input

    try:
        # Get user input if provided
        user_input = request.json.get("message", "").strip()

        if user_input:
            # Always update last_user_input and summarize before generating a question
            last_user_input = user_input
            summarized_input = summarize_text(user_input)
            if conversation_summary == "No conversation yet.":
                conversation_summary = summarized_input
            else:
                conversation_summary = f"{conversation_summary} | {summarized_input}"
            logger.debug(f"Updated last_user_input: {last_user_input}")
            logger.debug(f"Updated conversation_summary: {conversation_summary}")

        logger.debug(f"Conversation summary being passed to OpenAI: {conversation_summary}")
        logger.debug(f"Last user input being passed to OpenAI: {last_user_input}")

        # Prepare the OpenAI request
        system_message = {
            "role": "system",
            "content": (
                "You are a skilled reflection coach. Based on the user's input, craft a vivid and realistic scenario that directly relates to their concern or situation. "
                "The scenario should immerse them in a specific, relatable situation that resonates with their input, helping them see possibilities or alternatives. "
                "End the scenario with a highly specific and open-ended reflective question that encourages them to think deeply and explore actionable ideas. "
                "Avoid abstract, overly metaphorical, or flowery language. Keep the scenario relevant and focused on their context. It must strictly be 20 words maximum."
            )
        }

        messages = [
            system_message,
            {
                "role": "user",
                "content": (
                    f"The conversation summary so far is:\n{conversation_summary}\n\n"
                    f"The user's last input was:\n{last_user_input}\n\n"
                    f"Using these details, craft a hypothetical question that feels tailored to them."
                )
            }
        ]

        # Call OpenAI to generate the question
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        hypothetical_question = response.choices[0].message["content"].strip()
        logger.debug(f"Generated 'Think Bigger' question: {hypothetical_question}")
        return jsonify({"question": hypothetical_question})

    except Exception as e:
        logger.error(f"Error generating 'Think Bigger' question: {e}", exc_info=True)
        return jsonify({"question": "What could you do if there were no limits?"})


# ----------------------------------------------------------------
# Simple function to decide whether to move to the next stage
# (You can implement more advanced NLP-based logic here)
# ----------------------------------------------------------------
def determine_next_stage(user_input, current_stage, conversation_summary):
    """
    1. If user explicitly says "move on" or "next stage," jump to next stage (unless at 7).
    2. Otherwise, call classify_stage() to see what stage GPT recommends.
    3. If classify_stage() returns a valid stage, jump to it (or stay put if that logic suits you).
    4. Fallback: remain in current_stage.
    """
    lower_input = user_input.lower()

    # 1. Check if user explicitly requests to move on to next stage
    if "move on" in lower_input or "next stage" in lower_input:
        if current_stage < 7:
            return current_stage + 1
        else:
            return current_stage  # already at 7

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
    global conversation_summary, current_stage, last_user_input  # Maintain state between requests
    logger.debug("Entered /get_response route")  # Maintain state between requests

    try:
        # Log the incoming request
        logger.debug(f"Incoming POST request: {request.json}")

        user_input = request.json.get("message", "").strip()  # Get user input from the frontend

        if user_input:
            # Detect discrepancies directly by comparing current input with the last recorded input
            discrepancy = user_input if user_input != last_user_input else None
            last_user_input = user_input  # Update global last_user_input

            if discrepancy:
                summarized_input = summarize_text(discrepancy)  # Summarize the new input
                conversation_summary = f"{conversation_summary} | {summarized_input}".strip(" | ")  # Append and clean summary
                logger.debug(f"Updated conversation_summary: {conversation_summary}")

                # Determine the next stage if needed
                new_stage = determine_next_stage(user_input, current_stage, conversation_summary)
                if new_stage != current_stage:
                    logger.debug(f"Stage change detected: {current_stage} -> {new_stage}")
                    current_stage = new_stage

                # Generate a stage-specific response
                response_message = stage_chat(current_stage, conversation_summary, discrepancy)
                logger.debug(f"Generated response for stage {current_stage}: {response_message}")
            else:
                # No discrepancy, generate a generic AI-based question
                logger.debug("No discrepancy detected. Generating question via AI route.")
                response_message = stage_chat(current_stage, conversation_summary, user_input)
                logger.debug(f"Generated AI-based question for stage {current_stage}: {response_message}")
        else:
            # If the input box is empty when "Help Me Reflect" is pressed
            system_message = {
                "role": "system",
                "content": (
                    "Tell someone who is struggling to start journaling about something on their mind, a short, crisp way of framing how they should start writing. "
                    "Perhaps even a suggestion of WHY they're writing or what to start to write about, their day etc etc - but focus on ONE random thing not a list or generic overarching topic. "
                    "Your question should be 10 words maximum and can be a command if appropriate like imagine you're writing to ___ but go BEYOND this format. "
                    "No long sentences, DO NOT write lists or have lots of commas or clauses. Split into two sentences if necessary to keep it crisper and more readable. "
                    "Make it something a human would say to encourage someone to start writing. Not cringey, matter of fact and phrased in a simple way which makes someone easily start writing. "
                    "Be empathetic, but avoid being overly flowery or verbose."
                )
            }
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[system_message],
                    temperature=0.8,  # Encourage creativity
                    max_tokens=150,
                )
                response_message = response.choices[0].message["content"].strip()
                logger.debug(f"Generated creative writing suggestion: {response_message}")
            except Exception as e:
                logger.error(f"Error generating creative writing suggestion: {e}", exc_info=True)
                response_message = "Take your time. Imagine you're sharing your thoughts with someone who truly cares."

        return jsonify({"message": response_message})

    except Exception as e:
        logger.error(f"Error in /get_response: {e}", exc_info=True)
        return jsonify({"message": "I'm sorry, something went wrong."})

# ----------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)