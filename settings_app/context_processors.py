from .models import UserSettings


def user_settings_context(request):
    if request.user.is_authenticated:
        user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
        return {'user_settings': user_settings}
    return {'user_settings': None}
