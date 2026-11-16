from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    course = models.CharField(max_length=100, blank=True)
    year_level = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    interests = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.user.username
