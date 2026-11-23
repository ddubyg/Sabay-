from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.timesince import timesince
from home.models import Activity, Participation
from .models import Profile

ALL_INTERESTS = [
    ('study', '📚 Study'),
    ('sports', '🏀 Sports'),
    ('gaming', '🎮 Gaming'),
    ('food', '🍜 Food Trips'),
    ('coffee', '☕ Coffee Hangout'),
    ('coding', '💻 Coding'),
    ('gym', '🏋️ Gym / Fitness'),
    ('commute', '🚗 Commute / Carpool'),
    ('movies', '🎬 Movie Night'),
]


RECENT_LIMIT = 5


def activity_stats(user):
    """Real numbers for the profile header."""
    hosted_ids = set(Activity.objects.filter(creator=user).values_list('id', flat=True))
    joined_ids = set(Participation.objects.filter(user=user).values_list('activity_id', flat=True))
    shared_ids = hosted_ids | joined_ids

    # Anyone who hosted or joined an activity you were part of, except you.
    companions = (
        User.objects
        .filter(Q(activities__id__in=shared_ids) | Q(participations__activity_id__in=shared_ids))
        .exclude(pk=user.pk)
        .distinct()
        .count()
    ) if shared_ids else 0

    return {
        'joined': len(joined_ids),
        'hosted': len(hosted_ids),
        'companions': companions,
    }


def recent_activity(user, limit=RECENT_LIMIT):
    """Latest things you hosted or joined, newest first."""
    hosted = [
        {'kind': 'hosted', 'activity': a, 'when': a.created_at}
        for a in Activity.objects.filter(creator=user).order_by('-created_at')[:limit]
    ]
    joined = [
        {'kind': 'joined', 'activity': p.activity, 'when': p.joined_at}
        for p in Participation.objects.filter(user=user).select_related('activity').order_by('-joined_at')[:limit]
    ]
    items = sorted(hosted + joined, key=lambda item: item['when'], reverse=True)[:limit]
    now = timezone.now()
    for item in items:
        item['ago'] = 'just now' if (now - item['when']).total_seconds() < 60 else f"{timesince(item['when'], now)} ago"
    return items


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    saved_interests = profile.interests or []
    interest_chips = [
        {'key': key, 'label': label, 'active': key in saved_interests}
        for key, label in ALL_INTERESTS
    ]
    return render(request, 'user_profile/profile.html', {
        'profile': profile,
        'interest_chips': interest_chips,
        'stats': activity_stats(request.user),
        'recent': recent_activity(request.user),
    })


@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        course = request.POST.get('course', '').strip()
        year_level = request.POST.get('year_level', '').strip()
        bio = request.POST.get('bio', '').strip()
        email = request.POST.get('email', '').strip()
        selected_interests = request.POST.getlist('interests')

        profile.course = course
        profile.year_level = year_level
        profile.bio = bio
        profile.interests = selected_interests
        profile.save()

        if email:
            request.user.email = email
            request.user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    saved_interests = profile.interests or []
    interest_options = [
        {'key': key, 'label': label, 'checked': key in saved_interests}
        for key, label in ALL_INTERESTS
    ]

    return render(request, 'user_profile/edit_profile.html', {
        'profile': profile,
        'interest_options': interest_options,
    })
