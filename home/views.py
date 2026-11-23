from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .demo_data import seed_starter_activities
from .models import Activity, Participation

# Format used by <input type="datetime-local">.
DATETIME_INPUT_FORMAT = '%Y-%m-%dT%H:%M'


def get_or_seed_activities():
    if not Activity.objects.exists():
        seed_starter_activities()

    # Upcoming only, soonest first (Activity.upcoming orders explicitly, which
    # matters because Meta.ordering is ignored on GROUP BY queries).
    return Activity.upcoming().annotate(participant_total=Count('participations'))


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

    if activity.is_past:
        messages.error(request, 'This activity has already ended.')
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


def _parse_starts_at(raw):
    """datetime-local string -> aware datetime in the site timezone, or None."""
    try:
        naive = datetime.strptime(raw, DATETIME_INPUT_FORMAT)
    except (TypeError, ValueError):
        return None
    return timezone.make_aware(naive)


def _read_activity_form(request):
    """Pull and validate the activity fields.

    Returns (fields, form_values, error). `fields` is ready for the model;
    `form_values` is what to put back into the form if there's an error.
    """
    form_values = {
        'title': request.POST.get('title', '').strip(),
        'category': request.POST.get('category', 'study').strip().lower(),
        'location': request.POST.get('location', '').strip(),
        'starts_at': request.POST.get('starts_at', '').strip(),
        'description': request.POST.get('description', '').strip(),
    }
    if not form_values['title'] or not form_values['location'] or not form_values['starts_at']:
        return None, form_values, 'Please fill in all required fields.'
    if form_values['category'] not in CATEGORY_EMOJIS:
        return None, form_values, 'Please pick one of the listed categories.'

    starts_at = _parse_starts_at(form_values['starts_at'])
    if starts_at is None:
        return None, form_values, 'Please pick a valid date and time.'
    if starts_at < timezone.now() - timedelta(minutes=5):
        return None, form_values, "That time has already passed. Pick a time that's coming up."

    return {**form_values, 'starts_at': starts_at}, form_values, None


def _form_context(**extra):
    """Shared context for the post/edit form: the earliest pickable time."""
    return {'min_starts_at': timezone.localtime().strftime(DATETIME_INPUT_FORMAT), **extra}


@login_required
def create_activity_view(request):
    if request.method == 'POST':
        fields, form_values, error = _read_activity_form(request)
        if error:
            return render(request, 'home/create_activity.html', _form_context(error=error, **form_values))

        Activity.objects.create(creator=request.user, **fields)
        messages.success(request, 'New Sabay activity posted successfully!')
        return redirect('home')

    return render(request, 'home/create_activity.html', _form_context())


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
        fields, form_values, error = _read_activity_form(request)
        if error:
            return render(request, 'home/create_activity.html', _form_context(**context, error=error, **form_values))

        for field, value in fields.items():
            setattr(activity, field, value)
        activity.save()
        messages.success(request, 'Activity updated.')
        return redirect('activity_detail', pk=pk)

    return render(request, 'home/create_activity.html', _form_context(
        **context,
        title=activity.title,
        category=activity.category,
        location=activity.location,
        starts_at=timezone.localtime(activity.starts_at).strftime(DATETIME_INPUT_FORMAT),
        description=activity.description,
    ))


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
