from django.db.models import Count, Q

from apps.helpdesk.models import (
    Conversation,
    ConversationMessage,
    HelpQuestionAnalysis,
)


def get_helpdesk_analytics():
    """
    Returns analytics for the Smart Bus AI Help Assistant.
    Used by the existing Reports module.
    """

    # -----------------------------------------
    # BASIC COUNTS
    # -----------------------------------------

    total_conversations = Conversation.objects.count()

    total_questions = HelpQuestionAnalysis.objects.count()

    total_messages = ConversationMessage.objects.count()

    total_user_messages = ConversationMessage.objects.filter(
        message_type=ConversationMessage.USER
    ).count()

    total_assistant_messages = ConversationMessage.objects.filter(
        message_type=ConversationMessage.ASSISTANT
    ).count()


    # -----------------------------------------
    # FEEDBACK
    # -----------------------------------------

    helpful_count = ConversationMessage.objects.filter(
        message_type=ConversationMessage.ASSISTANT,
        helpful=True
    ).count()

    not_helpful_count = ConversationMessage.objects.filter(
        message_type=ConversationMessage.ASSISTANT,
        helpful=False
    ).count()

    feedback_count = helpful_count + not_helpful_count


    # -----------------------------------------
    # ANSWERED QUESTIONS
    # -----------------------------------------

    answered_questions = HelpQuestionAnalysis.objects.filter(
        was_answered=True
    ).count()

    unanswered_questions = HelpQuestionAnalysis.objects.filter(
        was_answered=False
    ).count()


    # -----------------------------------------
    # MOST ASKED CATEGORIES
    # -----------------------------------------

    categories = (
        HelpQuestionAnalysis.objects
        .exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


    # -----------------------------------------
    # MOST ASKED QUESTIONS
    # -----------------------------------------

    most_asked_questions = (
        HelpQuestionAnalysis.objects
        .values("question")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )


    # -----------------------------------------
    # FEEDBACK RATE
    # -----------------------------------------

    if feedback_count > 0:
        helpful_percentage = round(
            (helpful_count / feedback_count) * 100,
            1
        )
    else:
        helpful_percentage = 0


    # -----------------------------------------
    # ANSWER RATE
    # -----------------------------------------

    if total_questions > 0:
        answer_rate = round(
            (answered_questions / total_questions) * 100,
            1
        )
    else:
        answer_rate = 0


    return {
        "total_conversations": total_conversations,
        "total_questions": total_questions,
        "total_messages": total_messages,
        "total_user_messages": total_user_messages,
        "total_assistant_messages": total_assistant_messages,

        "helpful_count": helpful_count,
        "not_helpful_count": not_helpful_count,
        "feedback_count": feedback_count,
        "helpful_percentage": helpful_percentage,

        "answered_questions": answered_questions,
        "unanswered_questions": unanswered_questions,
        "answer_rate": answer_rate,

        "categories": list(categories),
        "most_asked_questions": list(most_asked_questions),
    }