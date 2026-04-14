from django.contrib.auth.models import User
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

STATUS_CHOICES = [
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("done", "Done"),
]


class TaskStatus(models.Model):
    name = models.CharField(max_length=50)
    # user can be null for default statuses, or set to a specific user for custom statuses
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='statuses')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Task(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField()
    status = models.ForeignKey(TaskStatus, on_delete=models.PROTECT, null=True, related_name='tasks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")

    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class UserAPIKey(AbstractAPIKey):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")

    class Meta(AbstractAPIKey.Meta):
        verbose_name = "User API Key"
        verbose_name_plural = "User API Keys"
