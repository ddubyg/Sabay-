from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Activity, Participation


def get_or_seed_activities():
    if Activity.objects.count() == 0:
        initial_activities = [
            {
                'title': 'Study at Library',
                'category': 'study',
                'location': 'CIT-U Library 3F',
                'time': 'Today, 3:00 PM',
                'description': 'Reviewing for Midterm Exam in Algorithms and Data Structures. Bring your notes and laptop!',
            },
            {
                'title': 'Pick-up Basketball Game',
                'category': 'sports',
                'location': 'Campus Gymnasium Court',
                'time': 'Tomorrow, 5:00 PM',
                'description': 'Casual 5v5 half-court or full-court games after class. All skill levels welcome!',
            },
            {
                'title': 'Valorant 5-Stack Ranked',
                'category': 'gaming',
                'location': 'Discord / Online',
                'time': 'Tonight, 8:00 PM',
                'description': 'Ranked competitive climb tonight. Need 2 friendly chill teammates. Comms required!',
            },
            {
                'title': 'Samgyup Lunch Treat',
                'category': 'food',
                'location': 'Korean BBQ Spot Near Campus',
                'time': 'Friday, 12:30 PM',
                'description': 'Unlimited samgyupsal buffet after our Friday classes. Splitting the bill evenly!',
            },
            {
                'title': 'Carpool to IT Park',
                'category': 'commute',
                'location': 'CIT-U Main Gate',
                'time': 'Daily, 5:30 PM',
                'description': 'Heading towards IT Park / Lahug after afternoon classes. Safe, comfortable ride.',
            },
            {
                'title': 'Coffee & Chill / Coding',
                'category': 'hangout',
                'location': 'Cafe Talk Lounge',
                'time': 'Thursday, 4:00 PM',
                'description': 'Quiet productive cafe session with iced lattes and chill beats. Working on personal coding tasks.',
            },
        ]
        for item in initial_activities:
            Activity.objects.create(**item)

    return Activity.objects.annotate(participant_total=Count('participations'))


@login_required
def home_view(request):
    activities = get_or_seed_activities()
    return render(request, 'home/home.html', {
        'activities': activities
    })


CATEGORY_EMOJIS = {
    'study': '📚',
    'sports': '🏀',
    'gaming': '🎮',
    'food': '🍜',
    'commute': '🚗',
    'hangout': '☕',
}


@login_required
def activity_detail_view(request, pk):
    activity = get_object_or_404(Activity.objects.select_related('creator'), pk=pk)
    participations = activity.participations.select_related('user', 'user__profile')

    return render(request, 'home/activity_detail.html', {
        'activity': activity,
        'participations': participations,
        'is_host': activity.is_host(request.user),
        'has_joined': any(p.user_id == request.user.id for p in participations),
        'emoji': CATEGORY_EMOJIS.get(activity.category.lower(), '🎯'),
    })


@login_required
@require_POST
def join_activity_view(request, pk):
    activity = get_object_or_404(Activity, pk=pk)

    if activity.is_host(request.user):
        messages.info(request, "You're hosting this activity, so you're already in.")
        return redirect('activity_detail', pk=pk)

    try:
        _, created = Participation.objects.get_or_create(activity=activity, user=request.user)
    except IntegrityError:
        # Double-submit race: the row already exists.
        created = False

    if created:
        messages.success(request, f'You joined "{activity.title}"! See you there 🎉')
    else:
        messages.info(request, "You've already joined this activity.")
    return redirect('activity_detail', pk=pk)


@login_required
@require_POST
def leave_activity_view(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    deleted, _ = Participation.objects.filter(activity=activity, user=request.user).delete()

    if deleted:
        messages.success(request, f'You left "{activity.title}".')
    return redirect('activity_detail', pk=pk)


@login_required
def create_activity_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', 'study').strip()
        location = request.POST.get('location', '').strip()
        time = request.POST.get('time', '').strip()
        description = request.POST.get('description', '').strip()

        if not title or not location or not time:
            return render(request, 'home/create_activity.html', {
                'error': 'Please fill in all required fields.',
                'title': title,
                'category': category,
                'location': location,
                'time': time,
                'description': description,
            })

        Activity.objects.create(
            title=title,
            category=category,
            location=location,
            time=time,
            description=description,
            creator=request.user,
        )

        messages.success(request, 'New Sabay activity posted successfully!')
        return redirect('home')

    return render(request, 'home/create_activity.html')
