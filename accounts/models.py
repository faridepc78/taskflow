from django.contrib.auth.models import User
from django.db import models

from config.upload_paths import avatar_upload_path


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)

    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
