from django.urls import path
from . import views

app_name = "helpdesk"

urlpatterns = [
    path("", views.help_home, name="home"),
    path("chat/", views.chat_message, name="chat"),
    path("conversation/<int:conversation_id>/", views.load_conversation, name="load_conversation"),
    path("feedback/", views.message_feedback, name="feedback"),
]