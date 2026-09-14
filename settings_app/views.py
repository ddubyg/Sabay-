from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import UserSettings


@login_required
def settings_view(request):

    settings, created = UserSettings.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        settings.notifications = (
            request.POST.get('notifications') == 'on'
        )

        settings.dark_mode = (
            request.POST.get('dark_mode') == 'on'
        )

        settings.save()

    return render(request, 'settings_app/settings.html', {
        'settings': settings
    })