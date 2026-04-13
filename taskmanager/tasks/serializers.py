from rest_framework import serializers
from django.db import models

from .models import Task, TaskStatus


class TaskSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField(
        queryset=TaskStatus.objects.all()
    )
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "description", "status", "status_name", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        
        # Filters the status options in the API to show only
        # those belonging to the user making the request + the default ones.
        if request:
            user = None
            if request.user and request.user.is_authenticated:
                user = request.user
            else:
                from .models import UserAPIKey
                key = request.META.get('HTTP_AUTHORIZATION', '').replace('Api-Key ', '')
                if key:
                    try:
                        api_key = UserAPIKey.objects.get_from_key(key)
                        user = api_key.user
                    except Exception:
                        pass
            
            if user:
                fields['status'].queryset = TaskStatus.objects.filter(
                    models.Q(is_default=True) | models.Q(user=user)
                )
        return fields


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id', 'name', 'is_default']
        read_only_fields = ['id', 'is_default']