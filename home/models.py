from django.db import models
from django.contrib.auth.models import User


class Activity(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default='study')
    location = models.CharField(max_length=200)
    time = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    participants_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
