from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
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
