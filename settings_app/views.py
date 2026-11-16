import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .models import UserSettings


@login_required
def settings_view(request):
    settings, created = UserSettings.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        settings.notifications = (request.POST.get('notifications') == 'on')
        settings.dark_mode = (request.POST.get('dark_mode') == 'on')
        settings.save()
        messages.success(request, 'Settings saved successfully!')
        return redirect('settings')

    return render(request, 'settings_app/settings.html', {
        'settings': settings
    })


@login_required
@require_POST
def toggle_theme_view(request):
    settings, _ = UserSettings.objects.get_or_create(user=request.user)

    try:
        data = json.loads(request.body.decode('utf-8'))
        dark_mode = bool(data.get('dark_mode'))
    except Exception:
        dark_mode = (request.POST.get('dark_mode') in ['true', 'on', '1'])

    settings.dark_mode = dark_mode
    settings.save()
    return JsonResponse({'status': 'ok', 'dark_mode': settings.dark_mode})


@login_required
@require_POST
def toggle_notifications_view(request):
    settings, _ = UserSettings.objects.get_or_create(user=request.user)

    try:
        data = json.loads(request.body.decode('utf-8'))
        notifications = bool(data.get('notifications'))
    except Exception:
        notifications = (request.POST.get('notifications') in ['true', 'on', '1'])

    settings.notifications = notifications
    settings.save()
    return JsonResponse({'status': 'ok', 'notifications': settings.notifications})
