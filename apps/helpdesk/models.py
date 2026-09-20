# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="help_conversations"
    )

    title = models.CharField(
        max_length=200,
        blank=True
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.started_at}"


class ConversationMessage(models.Model):

    USER = "user"
    ASSISTANT = "assistant"

    MESSAGE_TYPE_CHOICES = [
        (USER, "User"),
        (ASSISTANT, "AI Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES
    )

    message = models.TextField()

    helpful = models.BooleanField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.message_type} - {self.created_at}"


class HelpQuestionAnalysis(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="question_analysis"
    )

    question = models.TextField()

    category = models.CharField(
        max_length=100,
        blank=True
    )

    keywords = models.JSONField(
        default=list,
        blank=True
    )

    was_answered = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]