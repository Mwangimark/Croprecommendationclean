import os
# import json
from pathlib import Path
# from typing import Dict, Any, TypedDict
from dotenv import load_dotenv
# from transformers import pipeline
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain_community.llms import HuggingFacePipeline
# from langgraph.graph import StateGraph, END
from django.conf import settings
from .models import ConversationState
import openai

load_dotenv() 


openai.api_key = os.getenv("OPENAI_API_KEY")

  # Debugging line to check if key is loaded
# # --------- Configuration ----------
# MODEL_NAME = os.getenv("HF_MODEL", "google/flan-t5-large")  # default local model
# HF_API_TOKEN = os.getenv("HF_TOKEN")  # for Hugging Face Inference API (production)

# # For storing chat history in files
STATE_DIR = Path(getattr(settings, "CHATBOT_STATE_DIR", "chatbot_states"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

# --------- Rule-based FAQ ----------
FAQ = {
    "what is this system": "This is a crop recommendation system that suggests the best crops to grow based on soil and climate data.",
    "how does it work": "We use your soil data (N, P, K, pH, temperature, humidity, rainfall) and a trained ML model to recommend suitable crops.",
    "how do i enter my soil data": "Go to the 'Predict Crop' page and fill in all the soil and weather parameters, then click 'Submit'.",
    "who developed this system": "This system was developed by our team to help farmers make data-driven crop choices.",
    "what crops can it predict": "It can predict crops such as rice, maize, sugarcane, wheat, cotton, and more depending on your soil and weather data."
}

# --------- Load Hugging Face Model Once ----------
# print(f"Loading Hugging Face model '{MODEL_NAME}'...")

# # Local pipeline
# hf_pipeline = pipeline(
#     "text2text-generation",
#     model=MODEL_NAME,
#     device=0 if __import__("torch").cuda.is_available() else -1
# )

# Wrap in LangChain
# llm = HuggingFacePipeline(pipeline=hf_pipeline)
# print("Model loaded successfully!")

# Prompt template
# PROMPT_TEMPLATE = """You are an agricultural expert. Provide clear, practical, and somewhat detailed answers about farming and crops.

# Example:
# Q: Which crops grow best in acidic soil?
# A: Crops like potatoes, blueberries, sweet potatoes, and peanuts thrive in acidic soils (pH < 6.0). For each crop, briefly explain the reason and ideal pH range if known.

# Q: {question}
# A:"""

# prompt = PromptTemplate(input_variables=["question"], template=PROMPT_TEMPLATE)
# chain = LLMChain(llm=llm, prompt=prompt)
# openai.api_key = os.getenv("OPENAI_API_KEY")



# --------- State Helpers ----------
# def _state_file_path(session_id: str) -> Path:
#     return STATE_DIR / f"{session_id}.json"

# def write_state_file(session_id: str, state_obj: Dict[str, Any]):
#     with open(_state_file_path(session_id), "w", encoding="utf-8") as f:
#         json.dump(state_obj, f, indent=2, ensure_ascii=False)

# def load_or_create_state(session_id: str, user=None) -> ConversationState:
#     cs, created = ConversationState.objects.get_or_create(session_id=session_id, defaults={"user": user})
#     if created:
#         cs.history = []
#         cs.save()
#         write_state_file(session_id, {"session_id": session_id, "history": cs.history})
#     return cs


# # --------- Rule-based Response ----------
def get_rule_reply(user_message: str) -> str:
    message_lower = user_message.lower()
    for q, a in FAQ.items():
        if q in message_lower:
            return a
    return None


# --------- Hugging Face Response ----------
# def get_gpt_reply(user_message: str, max_tokens: int = 100) -> str:
#     system_message = """
#     You are an agricultural expert. Provide clear, practical, and somewhat detailed answers about farming and crops.

#     Example:
#     Q: Which crops grow best in acidic soil?
#     A: Crops like potatoes, blueberries, sweet potatoes, and peanuts thrive in acidic soils (pH < 6.0). For each crop, briefly explain the reason and ideal pH range if known.

#     IMPORTANT: Only answer questions related to agriculture, farming, crops, soil, climate, or related topics. 
#     If the question is unrelated to agriculture, politely respond: "I'm here to assist with agriculture-related questions. Could you please ask something about farming or crops?"
#     """

#     try:
#         chat_completion = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": system_message},
#                 {"role": "user", "content": user_message}
#             ],
#             max_tokens=max_tokens,
#             temperature=0.7,
#         )
#         answer = chat_completion.choices[0].message.content.strip()
#         return answer
#     except Exception as e:
#         return f"Sorry, I couldn't process your request due to: {str(e)}"



# --------- LangGraph Node ----------
# def chat_node(state):
#     session_id = state.get("session_id")
#     user_message = state.get("user_message", "").strip()
#     user = state.get("user", None)

#     cs = load_or_create_state(session_id, user)
#     cs.append("user", user_message)
#     cs.save()
#     write_state_file(session_id, {"session_id": session_id, "history": cs.history})

#     # Try rule-based first
#     rule_reply = get_rule_reply(user_message)
#     if rule_reply:
#         cs.append("bot", rule_reply)
#         cs.save()
#         write_state_file(session_id, {"session_id": session_id, "history": cs.history})
#         return {"reply": rule_reply}

#     # Fallback to GPT model
#     gpt_answer = get_gpt_reply(user_message)
#     cs.append("bot", gpt_answer)
#     cs.save()
#     write_state_file(session_id, {"session_id": session_id, "history": cs.history})
    # return {"reply": gpt_answer}



# --------- LangGraph Setup ----------


# Define the shape of the state
# class ChatState(TypedDict):
#     session_id: str
#     user_message: str
#     user: str | None
#     reply: str | None

# Build graph with state schema
# graph = StateGraph(ChatState)
# graph.add_node("chat", chat_node)
# graph.set_entry_point("chat")
# graph.add_edge("chat", END)
# compiled_graph = graph.compile()



# --------- Public API for Views ----------
def handl_message(session_id: str, user_message: str, user=None) -> str:
    # State dict
    state = {"session_id": session_id, "user_message": user_message, "user": user}

    # Rule-based first
    rule_reply = get_rule_reply(user_message)
    if rule_reply:
        return rule_reply

    # GPT fallback
    try:
        chat_completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an agricultural expert."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        gpt_answer = chat_completion.choices[0].message.content.strip()
        return gpt_answer
    except Exception as e:
        return f"Sorry, I couldn't process your request due to: {str(e)}"

# hugging face fallback
# service.py
# import os
# from huggingface_hub import InferenceClient

# # Initialize the client with your Hugging Face API key
# HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")  # store key in .env
# client = InferenceClient(api_key=HF_API_KEY)

# def handle_message(session_id: str, user_message: str, user=None) -> str:
#     """
#     Handle user message with Hugging Face model.
#     Replies in same language (English or Kiswahili).
#     """

#     try:
#         response = client.chat.completions.create(
#             model="mistralai/Mistral-7B-Instruct-v0.2",  # you can swap for another
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an agriculture assistant. "
#                         "Reply in the same language the user uses (English or Kiswahili). "
#                         "If user greets (like 'habari' or 'hello'), respond naturally and briefly. "
#                         "If user asks an agriculture question, give short, clear, practical answers "
#                         "(2–3 sentences max)."
#                     )
#                 },
#                 {"role": "user", "content": user_message}
#             ],
#             max_tokens=250,
#         )

#         reply = response.choices[0].message["content"].strip()
#         return reply

#     except Exception as e:
#         raise Exception(f"Hugging Face error: {str(e)}")

# service.py
import os
import re
from huggingface_hub import InferenceClient

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
client = InferenceClient(api_key=HF_API_KEY)

PRIMARY_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
FALLBACK_MODEL = "google/mt5-small"  # multilingual model, better Kiswahili handling

def is_mixed_language(user_message: str, reply: str) -> bool:
    """
    Detect if reply mixes English + Kiswahili.
    Simple check: if user wrote in Kiswahili but reply has too many English words.
    """
    # detect Kiswahili question (basic heuristic: swahili words like 'ya', 'ni', 'mazao')
    swahili_keywords = ["mazao", "mbegu", "udongo", "mvua", "kilimo", "mmea", "za", "ni"]
    asked_in_swahili = any(word in user_message.lower() for word in swahili_keywords)

    if asked_in_swahili:
        # if more than 30% of words in reply are English letters-only, assume it's broken
        words = reply.split()
        english_like = [w for w in words if re.match(r"^[a-zA-Z]+$", w)]
        if len(english_like) / max(len(words), 1) > 0.3:
            return True
    return False

def ask_model(model: str, system_prompt: str, user_message: str, max_tokens: int = 250) -> str:
    """Helper to query Hugging Face model"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"].strip()

def handle_message(session_id: str, user_message: str, user=None) -> str:
    """
    Handle user message with Hugging Face model.
    Replies in the same language (English or Kiswahili).
    Falls back to mt5 if Kiswahili reply is broken.
    """
    system_prompt = (
        "You are an agriculture assistant. "
        "Reply in the same language the user uses (English or Kiswahili). "
        "Do not mix languages. "
        "Give short, clear, practical answers about farming (2–3 sentences max). "
        "If asked greetings, reply briefly like a person. "
        "If the question is not about agriculture, answer: "
        "'Samahani, ninaweza kusaidia tu kuhusu masuala ya kilimo' "
        "or 'Sorry, I can only help with agriculture questions'."
    )

    try:
        # First attempt with Mistral
        reply = ask_model(PRIMARY_MODEL, system_prompt, user_message)

        # Check if reply is broken for Kiswahili
        if is_mixed_language(user_message, reply):
            # Retry with multilingual fallback model
            reply = ask_model(FALLBACK_MODEL, system_prompt, user_message)

        return reply

    except Exception as e:
        raise Exception(f"Hugging Face error: {str(e)}")
