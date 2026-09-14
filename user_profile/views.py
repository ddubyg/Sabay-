from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Profile


@login_required
def profile_view(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        profile.course = request.POST.get('course')
        profile.year_level = request.POST.get('year_level')
        profile.bio = request.POST.get('bio')

        profile.save()

    return render(request, 'user_profile/profile.html', {
        'profile': profile
    })