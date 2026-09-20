import json
from datetime import date, datetime, time
from decimal import Decimal

from django.conf import settings
from openai import OpenAI


def make_json_safe(data):
    """
    Convert Django/queryset values into JSON-safe Python values.
    """
    if isinstance(data, list):
        return [make_json_safe(item) for item in data]

    if isinstance(data, dict):
        return {
            key: make_json_safe(value)
            for key, value in data.items()
        }

    if isinstance(data, (date, datetime, time)):
        return data.isoformat()

    if isinstance(data, Decimal):
        return float(data)

    return data


def build_conversation_history(conversation, limit=10):
    """
    Get the most recent messages from the current conversation.
    """

    messages = conversation.messages.order_by("-created_at")[:limit]

    messages = reversed(list(messages))

    history = []

    for message in messages:
        role = "User" if message.message_type == "user" else "Assistant"

        history.append({
            "role": role,
            "message": message.message,
        })

    return history


def build_ai_prompt(
    user,
    question,
    intent,
    data,
    conversation=None,
):
    """
    Build a controlled prompt using authorised system data
    and recent conversation history.
    """

    role = getattr(
        getattr(user, "profile", None),
        "role",
        "Customer"
    )

    safe_data = make_json_safe(data)

    conversation_history = []

    if conversation:
        conversation_history = build_conversation_history(
            conversation,
            limit=10,
        )

    return f"""
You are the Smart Bus Management System Help Assistant.

User role:
{role}

Current user question:
{question}

Detected intent:
{intent}

Authorised Smart Bus System information for the current question:
{json.dumps(safe_data, indent=2)}

Recent conversation history:
{json.dumps(conversation_history, indent=2)}

Instructions:
- Answer the current question using the authorised system information.
- Use the conversation history to understand follow-up questions.
- Use the conversation history to understand follow-up questions.
- Resolve references such as:
  "it",
  "that",
  "that one",
  "the first one",
  "the second one",
  "the previous booking",
  "the next booking",
  "that payment",
  "that bus",
  "that vehicle",
  "that driver".
- When the user refers to a numbered record, use the order
  in which the authorised records are provided.
- Do not invent a record that is not present in the authorised data.
- If the reference is ambiguous, ask the user to clarify.
- If the current question requires information that is not
  included in the authorised data, clearly state that it is unavailable.
- If the current question depends on previous information,
  use the conversation history to understand what the user means.
- Do not invent information.
- Do not assume information that is not present in the authorised data
  or conversation history.
- Do not reveal information outside the user's permissions.
- Do not expose unnecessary database IDs.
- Use Malaysian English.
- Keep the answer clear and concise.
"""


def generate_response(
    user,
    question,
    intent,
    data,
    conversation=None,
):
    """
    Generate a natural-language answer using OpenAI.
    """

    api_key = getattr(settings, "OPENAI_API_KEY", None)

    if not api_key:
        return (
            "The AI service is not configured yet. "
            "Please contact the system administrator."
        )

    if data is None:
        data_for_ai = []
    else:
        data_for_ai = data

    try:
        client = OpenAI(api_key=api_key)

        prompt = build_ai_prompt(
            user=user,
            question=question,
            intent=intent,
            data=data_for_ai,
            conversation=conversation,
        )

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
        )

        return response.output_text.strip()

    except Exception as exc:
        print(f"OpenAI API error: {exc}")

        return (
            "I am currently unable to process your question. "
            "Please try again shortly."
        )