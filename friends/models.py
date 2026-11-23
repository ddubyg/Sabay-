from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


class FriendRequest(models.Model):
    """One row per pair of users. Pending until the receiver accepts.

    Declining, cancelling and unfriending all delete the row, so the
    pair can start over later.
    """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friend_request'),
            models.CheckConstraint(condition=~Q(from_user=models.F('to_user')), name='no_self_friend_request'),
        ]

    def __str__(self):
        state = 'friends' if self.accepted else 'pending'
        return f'{self.from_user} -> {self.to_user} ({state})'
