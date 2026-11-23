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

    # Meta.ordering is ignored on GROUP BY queries, so order explicitly.
    return Activity.objects.annotate(participant_total=Count('participations')).order_by('-created_at')


@login_required
def home_view(request):
    activities = get_or_seed_activities().select_related('creator')
    joined_ids = set(
        Participation.objects.filter(user=request.user).values_list('activity_id', flat=True)
    )
    return render(request, 'home/home.html', {
        'activities': activities,
        'joined_ids': joined_ids,
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


def _read_activity_form(request):
    """Pull and validate the activity fields. Returns (data, error)."""
    data = {
        'title': request.POST.get('title', '').strip(),
        'category': request.POST.get('category', 'study').strip().lower(),
        'location': request.POST.get('location', '').strip(),
        'time': request.POST.get('time', '').strip(),
        'description': request.POST.get('description', '').strip(),
    }
    if not data['title'] or not data['location'] or not data['time']:
        return data, 'Please fill in all required fields.'
    if data['category'] not in CATEGORY_EMOJIS:
        return data, 'Please pick one of the listed categories.'
    return data, None


@login_required
def create_activity_view(request):
    if request.method == 'POST':
        data, error = _read_activity_form(request)
        if error:
            return render(request, 'home/create_activity.html', {'error': error, **data})

        Activity.objects.create(creator=request.user, **data)
        messages.success(request, 'New Sabay activity posted successfully!')
        return redirect('home')

    return render(request, 'home/create_activity.html')


def _get_own_activity(request, pk):
    """The activity, or None (with an error message) if the user isn't its host."""
    activity = get_object_or_404(Activity, pk=pk)
    if not activity.is_host(request.user):
        messages.error(request, 'Only the host can change this activity.')
        return None
    return activity


@login_required
def edit_activity_view(request, pk):
    activity = _get_own_activity(request, pk)
    if activity is None:
        return redirect('activity_detail', pk=pk)

    context = {'editing': True, 'activity': activity}

    if request.method == 'POST':
        data, error = _read_activity_form(request)
        if error:
            return render(request, 'home/create_activity.html', {**context, 'error': error, **data})

        for field, value in data.items():
            setattr(activity, field, value)
        activity.save()
        messages.success(request, 'Activity updated.')
        return redirect('activity_detail', pk=pk)

    return render(request, 'home/create_activity.html', {
        **context,
        'title': activity.title,
        'category': activity.category,
        'location': activity.location,
        'time': activity.time,
        'description': activity.description,
    })


@login_required
@require_POST
def delete_activity_view(request, pk):
    activity = _get_own_activity(request, pk)
    if activity is None:
        return redirect('activity_detail', pk=pk)

    title = activity.title
    activity.delete()
    messages.success(request, f'"{title}" was deleted.')
    return redirect('home')
