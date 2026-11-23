"""The starter activities shown on a fresh install and restored by `reseed_demo`.

Times are relative (days from today + local clock time) so the feed is
always full of upcoming activities, whenever it's seeded.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Activity

STARTER_ACTIVITIES = [
    {
        'title': 'Study at Library',
        'category': 'study',
        'location': 'CIT-U Library 3F',
        'when': (1, 15, 0),
        'description': 'Reviewing for Midterm Exam in Algorithms and Data Structures. Bring your notes and laptop!',
    },
    {
        'title': 'Pick-up Basketball Game',
        'category': 'sports',
        'location': 'Campus Gymnasium Court',
        'when': (1, 17, 0),
        'description': 'Casual 5v5 half-court or full-court games after class. All skill levels welcome!',
    },
    {
        'title': 'Valorant 5-Stack Ranked',
        'category': 'gaming',
        'location': 'Discord / Online',
        'when': (1, 20, 0),
        'description': 'Ranked competitive climb tonight. Need 2 friendly chill teammates. Comms required!',
    },
    {
        'title': 'Samgyup Lunch Treat',
        'category': 'food',
        'location': 'Korean BBQ Spot Near Campus',
        'when': (3, 12, 30),
        'description': 'Unlimited samgyupsal buffet after our Friday classes. Splitting the bill evenly!',
    },
    {
        'title': 'Carpool to IT Park',
        'category': 'commute',
        'location': 'CIT-U Main Gate',
        'when': (2, 17, 30),
        'description': 'Heading towards IT Park / Lahug after afternoon classes. Safe, comfortable ride.',
    },
    {
        'title': 'Coffee & Chill / Coding',
        'category': 'hangout',
        'location': 'Cafe Talk Lounge',
        'when': (4, 16, 0),
        'description': 'Quiet productive cafe session with iced lattes and chill beats. Working on personal coding tasks.',
    },
]


def local_at(days_from_today, hour, minute=0):
    day = timezone.localdate() + timedelta(days=days_from_today)
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


def starter_fields(item):
    """Model fields for one starter activity, with its time computed from today."""
    fields = {k: v for k, v in item.items() if k != 'when'}
    fields['starts_at'] = local_at(*item['when'])
    return fields


def seed_starter_activities():
    for item in STARTER_ACTIVITIES:
        Activity.objects.create(**starter_fields(item))


def reseed_starter_activities(clear_joins=False):
    """Bring the starter activities back to upcoming dates.

    Only touches host-less activities with a starter title; anything a user
    posted is left alone. Missing starters are recreated.
    Returns (updated, created, joins_removed).
    """
    updated = created = joins_removed = 0
    for item in STARTER_ACTIVITIES:
        fields = starter_fields(item)
        existing = Activity.objects.filter(title=item['title'], creator__isnull=True)
        if existing.exists():
            existing.update(**fields)
            updated += existing.count()
            if clear_joins:
                for activity in existing:
                    joins_removed += activity.participations.all().delete()[0]
        else:
            Activity.objects.create(**fields)
            created += 1
    return updated, created, joins_removed
