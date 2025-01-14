import random

STAGE_QUESTIONS = {
    1: {
        "name": "Establish Psychological Safety & Trust",
        "questions": [
            "What brings you here today, and what would make this space feel more inviting for you?",
            "How can I help ease any heaviness you might be carrying, so you can open up freely?",
            "Before we begin, is there something on your mind that would make this conversation more comfortable?",
            "What kind of support would you need to feel both heard and at ease in this moment?",
            "When you begin to share, what helps you feel grounded and in control?",
            "What would make this process feel lighter and allow you to reflect without worry?",
            "How can we make this space one where you can feel both safe and curious about what’s next?",
            "Is there something about today’s reflection that you need to understand more clearly before we start?",
            "If at any point you feel unsure, how can I help bring you back to a place of calm?",
            "Let’s begin with something simple—what’s one thing you’re hoping to gain from this moment?"
        ]
    },

    2: {
        "name": "Clarify the User’s Desired Outcome",
        "questions": [
            "What do you want to achieve from this conversation?",
            "If you could press pause on everything and shape your future, what would that look like?",
            "What is the one thing you wish could shift, making everything feel just right?",
            "What is the quiet dream you've been carrying that you want to see unfold?",
            "How would you know you've truly arrived at the place you're seeking to reach?",
            "If you could untangle the knots in your path, what would the clear road ahead look like?",
            "What small change would make everything feel just a bit more in alignment?",
            "What would you consider the perfect version of your reality, given everything you're facing?",
            "If you were to find your purpose in this moment, what would that clarity feel like?",
            "What is that singular, powerful thing you’re ready to claim for yourself?"
        ]
    },

    3: {
        "name": "Explore Current Reality & Emotional Landscape",
        "questions": [
            "When you pause and reflect on your current situation, which emotions seem to step into the spotlight?",
            "What are the recurring thoughts that echo in your mind when this issue arises?",
            "As you face these challenges, how do the emotions shift when you think about them?",
            "Which aspect of this situation feels the heaviest in your heart, and what makes it so?",
            "When you confront these obstacles, which thoughts seem to circle back again and again?",
            "How do your feelings transform when you compare the present reality to the one you envision?",
            "What recurring patterns do you notice in your emotions as you navigate through this challenge?",
            "Can you recall a moment when the weight of this situation overwhelmed you? What emotions were alive in that moment?",
            "What actions or behaviors have you found yourself repeating in response to this, and how do they leave you feeling?",
            "When you look at what’s unfolding right now, what part of the situation feels the furthest from your grasp?"
        ]
    },

    4: {
        "name": "Identify (and Gently Challenge) Assumptions or Limiting Beliefs",
        "questions": [
            "When you say 'I can't,' what are the roots of that belief, and where do they come from?",
            "Is there a time, however small, when this belief wasn’t entirely true, even for a moment?",
            "What if, instead of seeing this as a permanent barrier, you viewed it as a challenge meant to be overcome?",
            "If a close friend were walking this path, how would you gently guide them past this belief?",
            "Can you recall a time when you broke free from a belief that once seemed impossible to change?",
            "How would it feel to look at this belief as something transient, a shadow that might soon pass?",
            "What experiences or evidence do you hold that could begin to loosen the grip of this assumption?",
            "When you reflect on this belief, does it feel like it's nurturing you, or quietly holding you back?",
            "Could there be another way of viewing this moment, one that opens doors instead of closing them?",
            "What would it be like to step forward into this situation with the unwavering belief that you can find a way through?"
        ]
    },

    5: {
        "name": "Guide Toward Possible Solutions or Next Steps",
        "questions": [
            "If you could step forward without the weight of fear, what would be your first leap?",
            "What small act could you take today that would bring you closer to the life you envision?",
            "If nothing stood in your way, what would the next step toward your dream look like?",
            "Among the paths before you, which one feels most true to the vision of where you want to go?",
            "What small shift, even today, might start to nudge the course of your journey in a new direction?",
            "Of the possibilities ahead, which one seems most attainable right now, and what makes it feel right?",
            "What one action can you take in the next day that will help you move with more purpose toward your goal?",
            "Out of all the routes available, which feels the gentlest to begin, requiring the least emotional weight?",
            "If you could simplify this into one step, what would it be, and how can you make it real today?",
            "What would the first step on your path look like, and how can you make it a reality in this moment?"
        ]
    },

    6: {
        "name": "Encourage Self-Monitoring & Reflection Loop",
        "questions": [
            "What measurable progress have you made, and what specific results are you still aiming for?",
            "Which actions have delivered the most tangible results so far?",
            "What concrete evidence shows you’re moving in the right direction?",
            "Where are you consistently succeeding, and where are gaps still evident?",
            "What one measurable outcome would signal real progress to you right now?",
            "What daily actions are driving the most impact, and which feel ineffective?",
            "What specific results do you expect to see in the next week, and how will you track them?",
            "What is one clear improvement you’ve noticed in your habits or outcomes recently?",
            "Which of your strategies has proven most effective, and how can you build on it?",
            "What’s the next small, actionable step that will produce a measurable result?"
        ]
    },
}

HYPOTHETICAL_QUESTIONS = [
    "If you could pause everything right now and focus on one thing, what would feel most important to address?",
    "What would it look like if this situation were simpler or less overwhelming?",
    "If you had all the support you needed, what would be your next step?",
    "Imagine you’re looking back on this moment from the future—what do you think will stand out the most?",
    "What might this situation teach you about yourself if you allowed it to?",
    "If you could describe your ideal outcome in one sentence, what would it be?",
    "What would change if you focused on what you can control?",
    "If you could ask someone you admire for advice, what might they say?",
    "What’s one thing you’re avoiding, and what might happen if you faced it?",
    "If you could simplify this situation, what would you focus on first?"
]
