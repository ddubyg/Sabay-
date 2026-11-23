from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import services


def _back(request):
    """Return to the page the button was on (same-site paths only), else Friends."""
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(target)
    return redirect('friends')


def _person(user, state):
    profile = getattr(user, 'profile', None)
    subtitle = ', '.join(filter(None, [getattr(profile, 'course', ''), getattr(profile, 'year_level', '')]))
    return {
        'id': user.id,
        'username': user.username,
        'initial': user.username[:1].upper(),
        'subtitle': subtitle or 'Sabay member',
        'state': state,
    }


@login_required
def friends_view(request):
    query = request.GET.get('q', '').strip()
    results = services.search_users(request.user, query)
    states = services.relationships(request.user, results)
    return render(request, 'friends/friends.html', {
        'query': query,
        'results': [_person(u, states[u.id]) for u in results],
        'received': [_person(r.from_user, services.RECEIVED) for r in services.pending_received(request.user)],
        'sent': [_person(r.to_user, services.SENT) for r in services.pending_sent(request.user)],
        'friends': [_person(u, services.FRIENDS) for u in services.friends_of(request.user)],
    })


@login_required
def search_json_view(request):
    results = services.search_users(request.user, request.GET.get('q', ''), limit=5)
    states = services.relationships(request.user, results)
    return JsonResponse({'results': [_person(u, states[u.id]) for u in results]})


@login_required
@require_POST
def add_view(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)
    state = services.send_request(request.user, other)
    if state == services.FRIENDS:
        messages.success(request, f'You and {other.username} are now friends! \U0001F389')
    elif state == services.SENT:
        messages.success(request, f'Friend request sent to {other.username}.')
    return _back(request)


@login_required
@require_POST
def accept_view(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    if services.accept_request(request.user, other) == services.FRIENDS:
        messages.success(request, f'You and {other.username} are now friends! \U0001F389')
    return _back(request)


@login_required
@require_POST
def remove_view(request, user_id):
    """Decline an incoming request, cancel a sent one, or unfriend."""
    other = get_object_or_404(User, pk=user_id)
    before = services.relationship(request.user, other)
    services.remove(request.user, other)
    text = {
        services.FRIENDS: f'Removed {other.username} from your friends.',
        services.SENT: f'Cancelled your request to {other.username}.',
        services.RECEIVED: f"Declined {other.username}'s request.",
    }.get(before)
    if text:
        messages.info(request, text)
    return _back(request)
