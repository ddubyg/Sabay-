from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.dateformat import format as date_format

# An activity still counts as "happening" (visible, joinable) this long after it starts.
HAPPENING_WINDOW = timedelta(hours=1)


class Activity(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default='study')
    location = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @classmethod
    def upcoming(cls):
        """Activities that haven't ended yet, soonest first."""
        return cls.objects.filter(starts_at__gte=timezone.now() - HAPPENING_WINDOW).order_by('starts_at')

    @property
    def is_past(self):
        return self.starts_at < timezone.now() - HAPPENING_WINDOW

    @property
    def is_happening(self):
        return not self.is_past and self.starts_at <= timezone.now()

    @property
    def when_label(self):
        """Human label in local time: 'Today, 3:00 PM', 'Friday, 12:30 PM', 'Dec 12, 9:00 AM'."""
        if self.is_happening:
            return 'Happening now'
        local = timezone.localtime(self.starts_at)
        today = timezone.localdate()
        days = (local.date() - today).days
        clock = date_format(local, 'g:i A')
        if days == 0:
            day = 'Tonight' if local.hour >= 18 else 'Today'
        elif days == 1:
            day = 'Tomorrow'
        elif 1 < days < 7:
            day = date_format(local, 'l')
        elif local.year == today.year:
            day = date_format(local, 'M j')
        else:
            day = date_format(local, 'M j, Y')
        return f'{day}, {clock}'

    @property
    def full_when_label(self):
        """Unambiguous date for the detail page: 'Friday, November 27, 2026 · 12:30 PM'."""
        return date_format(timezone.localtime(self.starts_at), 'l, F j, Y · g:i A')

    @property
    def going_count(self):
        """Host (if any) plus everyone who joined.

        Views can annotate `participant_total` to avoid one query per card.
        """
        joined = getattr(self, 'participant_total', None)
        if joined is None:
            joined = self.participations.count()
        return joined + (1 if self.creator_id else 0)

    def is_host(self, user):
        return user.is_authenticated and self.creator_id == user.id

    def has_joined(self, user):
        return user.is_authenticated and self.participations.filter(user=user).exists()


class Participation(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='participations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participations')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['joined_at']
        constraints = [
            models.UniqueConstraint(fields=['activity', 'user'], name='unique_participation'),
        ]

    def __str__(self):
        return f'{self.user.username} → {self.activity.title}'
