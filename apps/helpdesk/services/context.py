from apps.helpdesk.models import Conversation


def get_recent_conversation(conversation, limit=10):
    """
    Return recent conversation messages in chronological order.
    """

    if not conversation:
        return []

    messages = conversation.messages.order_by("-created_at")[:limit]

    return list(reversed(messages))


def get_recent_user_questions(conversation, limit=5):
    """
    Return recent questions asked by the user.
    """

    messages = get_recent_conversation(
        conversation,
        limit=limit * 2,
    )

    questions = [
        message.message
        for message in messages
        if message.message_type == "user"
    ]

    return questions[-limit:]


def has_conversation_context(conversation):
    """
    Check whether this conversation already contains messages.
    """

    if not conversation:
        return False

    return conversation.messages.exists()


def is_follow_up_question(message):
    """
    Detect questions that commonly depend on previous
    conversation context.
    """

    text = message.lower().strip()

    follow_up_phrases = [
        "what about",
        "how about",
        "which one",
        "which is",
        "what is the second",
        "what is the first",
        "what about the second",
        "what about the first",
        "the second one",
        "the first one",
        "the next one",
        "the previous one",
        "that one",
        "that booking",
        "that payment",
        "that bus",
        "that vehicle",
        "that driver",
        "is it paid",
        "when is it",
        "where is it",
        "who is the driver",
        "who is driving",
    ]

    return any(
        phrase in text
        for phrase in follow_up_phrases
    )


def get_previous_context(conversation):
    """
    Return the most recent meaningful question and category.
    """

    if not conversation:
        return {
            "question": None,
            "category": None,
        }

    analysis = (
        conversation.question_analysis
        .order_by("-created_at")
        .first()
    )

    if not analysis:
        return {
            "question": None,
            "category": None,
        }

    return {
        "question": analysis.question,
        "category": analysis.category,
    }


def get_follow_up_intent(conversation):
    """
    Return the previous question category.
    """

    previous_context = get_previous_context(conversation)

    return previous_context["category"]

def get_previous_data_context(conversation):
    """
    Get the most recent question analysis and its category.
    """

    if not conversation:
        return None

    analysis = (
        conversation.question_analysis
        .order_by("-created_at")
        .first()
    )

    if not analysis:
        return None

    return {
        "question": analysis.question,
        "category": analysis.category,
        "keywords": analysis.keywords,
    }