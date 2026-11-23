"""Replace the free-text `time` column with a real `starts_at` datetime.

Existing rows get a best-effort date parsed from their old text
("Tomorrow, 5:00 PM", "Friday, 12:30 PM", "Saturday, 9:00 AM" ...),
counted from the day the migration runs, so the feed isn't empty
afterwards. Anything unparseable lands on tomorrow at 9:00 AM; hosts
can fix it with Edit.
"""
import re
from datetime import datetime, time, timedelta

from django.db import migrations, models
from django.utils import timezone

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def guess_start(text, today):
    text = (text or '').lower()

    clock = time(9, 0)
    m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text)
    if m:
        hour = int(m.group(1)) % 12 + (12 if m.group(3) == 'pm' else 0)
        clock = time(hour, int(m.group(2) or 0))

    day = today + timedelta(days=1)
    if 'today' in text or 'tonight' in text:
        day = today
    elif 'tomorrow' in text or 'daily' in text:
        day = today + timedelta(days=1)
    else:
        for i, name in enumerate(WEEKDAYS):
            if name in text:
                ahead = (i - today.weekday()) % 7 or 7
                day = today + timedelta(days=ahead)
                break

    start = timezone.make_aware(datetime.combine(day, clock))
    if start < timezone.now():
        start += timedelta(days=1)
    return start


def forwards(apps, schema_editor):
    Activity = apps.get_model('home', 'Activity')
    today = timezone.localdate()
    for activity in Activity.objects.all():
        activity.starts_at = guess_start(activity.time, today)
        activity.save(update_fields=['starts_at'])


def backwards(apps, schema_editor):
    Activity = apps.get_model('home', 'Activity')
    for activity in Activity.objects.all():
        local = timezone.localtime(activity.starts_at)
        activity.time = local.strftime('%A, %I:%M %p').replace(', 0', ', ')
        activity.save(update_fields=['time'])


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_participation'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='starts_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name='activity',
            name='time',
        ),
        migrations.AlterField(
            model_name='activity',
            name='starts_at',
            field=models.DateTimeField(),
        ),
    ]
