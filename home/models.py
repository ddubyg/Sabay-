from django.db import models
from django.contrib.auth.models import User


class Activity(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default='study')
    location = models.CharField(max_length=200)
    time = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

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
