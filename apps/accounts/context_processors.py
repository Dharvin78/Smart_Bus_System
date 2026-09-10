def user_role(request):

    role = None

    if request.user.is_authenticated:

        try:
            role = request.user.profile.role
        except Exception:
            role = None

    return {
        "user_role": role
    }