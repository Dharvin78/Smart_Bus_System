from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('', views.login_view, name='login'),

    path('signup/', views.signup_view, name='signup'),

    path('logout/', views.logout_view, name='logout'),

    path("profile/",views.profile,name="profile"),

    path(
        "profile/edit/",
        views.edit_profile,
        name="edit_profile"
    ),
]