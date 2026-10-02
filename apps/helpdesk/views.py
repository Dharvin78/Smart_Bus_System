# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from apps.helpdesk.services.router import get_data_for_question
from apps.helpdesk.services.ai_service import (generate_response,build_ai_prompt,)

from .models import Conversation, ConversationMessage, HelpQuestionAnalysis


@login_required
def help_home(request):

    profile = getattr(request.user, "profile", None)
    role = profile.role if profile else "Customer"

    conversations = Conversation.objects.filter(
        user=request.user
    ).order_by("-updated_at")

    return render(
        request,
        "helpdesk/help_home.html",
        {
            "role": role,
            "conversations": conversations,
        }
    )


@login_required
@require_POST
def chat_message(request):
    message = request.POST.get("message", "").strip()
    conversation_id = request.POST.get("conversation_id")

    if not message:
        return JsonResponse({
            "success": False,
            "error": "Please enter a message."
        }, status=400)

    # Find existing conversation
    conversation = None

    if conversation_id:
        conversation = Conversation.objects.filter(
            id=conversation_id,
            user=request.user
        ).first()

    # Create new conversation if needed
    if conversation is None:
        conversation = Conversation.objects.create(
            user=request.user,
            title=message[:80]
        )

    # Save user message
    ConversationMessage.objects.create(
        conversation=conversation,
        message_type=ConversationMessage.USER,
        message=message
    )

    # Route question through permission + data layer
    result = get_data_for_question(
        request.user,
        message,
        conversation=conversation,
    )

    # Generate response
    if not result["allowed"]:
        response_text = result["message"]

    elif result["intent"] == "general_help":
        response_text = (
            "I can help you with bookings, payments, vehicles, "
            "drivers, maintenance, fuel and other Smart Bus "
            "Management System information."
        )

    else:
        # Temporary response until an AI provider is connected
        response_text = generate_response(
                request.user,
                message,
                result["intent"],
                result["data"],
            )

    # Save assistant response
    assistant_message = ConversationMessage.objects.create(
        conversation=conversation,
        message_type=ConversationMessage.ASSISTANT,
        message=response_text
    )

    # Save question analysis
    HelpQuestionAnalysis.objects.create(
        conversation=conversation,
        question=message,
        category=result["intent"],
        keywords=[],
        was_answered=result["allowed"]
    )

    # Update conversation timestamp
    conversation.save(update_fields=["updated_at"])

    return JsonResponse({
        "success": True,
        "conversation_id": conversation.id,
        "response": response_text,
        "intent": result["intent"],
        "message_id": assistant_message.id,
    })

@login_required
def load_conversation(request, conversation_id):

    conversation = Conversation.objects.filter(
        id=conversation_id,
        user=request.user
    ).first()

    if conversation is None:
        return JsonResponse(
            {
                "success": False,
                "error": "Conversation not found."
            },
            status=404
        )

    messages = conversation.messages.all().order_by("created_at")

    message_list = []

    for message in messages:
        message_list.append({
            "id": message.id,
            "type": message.message_type,
            "message": message.message,
            "created_at": message.created_at.strftime(
                "%d %b %Y, %I:%M %p"
            ),
            "helpful": message.helpful,
        })

    return JsonResponse({
        "success": True,
        "conversation_id": conversation.id,
        "title": conversation.title,
        "messages": message_list,
    })

@login_required
@require_POST
def message_feedback(request):
    message_id = request.POST.get("message_id")
    helpful = request.POST.get("helpful")

    if not message_id:
        return JsonResponse({
            "success": False,
            "error": "Message ID is required."
        }, status=400)

    if helpful not in ["true", "false"]:
        return JsonResponse({
            "success": False,
            "error": "Invalid feedback value."
        }, status=400)

    message = ConversationMessage.objects.filter(
        id=message_id,
        conversation__user=request.user,
        message_type=ConversationMessage.ASSISTANT,
    ).first()

    if not message:
        return JsonResponse({
            "success": False,
            "error": "Message not found."
        }, status=404)

    message.helpful = helpful == "true"
    message.save(update_fields=["helpful"])

    return JsonResponse({
        "success": True,
        "helpful": message.helpful,
    })