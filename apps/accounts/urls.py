from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('', views.login_view, name='login'),

    path('signup/', views.signup_view, name='signup'),

    path('logout/', views.logout_view, name='logout'),

    path("profile/",views.profile,name="profile"),

    path("profile/edit/",views.edit_profile,name="edit_profile"),

    path("change-password/",views.change_password,name="change_password"),

# USER MANAGEMENT URLS
    path("users/", views.user_list, name="user_list"),

    path("users/add/", views.user_create, name="user_create"),

    path("users/edit/<int:pk>/", views.user_update, name="user_update"),

    path("users/delete/<int:pk>/", views.user_delete, name="user_delete"),
]