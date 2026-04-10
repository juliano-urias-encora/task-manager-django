from rest_framework.viewsets import ModelViewSet
from .models import Task, UserAPIKey
from .serializers import TaskSerializer
from rest_framework.permissions import BasePermission
from .models import UserAPIKey


class HasUserAPIKey(BasePermission):
    def has_permission(self, request, view):
        # allow session authenticated users (browsable API)
        if request.user and request.user.is_authenticated:
            return True
        # otherwise check API key
        key = request.META.get('HTTP_AUTHORIZATION', '').replace('Api-Key ', '')
        if not key:
            return False
        return UserAPIKey.objects.is_valid(key)


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [HasUserAPIKey]

    def get_queryset(self):
        # if authenticated via session (browsable API)
        if self.request.user and self.request.user.is_authenticated:
            return Task.objects.filter(user=self.request.user)
        
        # if authenticated via API key
        key = self.request.META.get('HTTP_AUTHORIZATION', '').replace('Api-Key ', '')
        api_key = UserAPIKey.objects.get_from_key(key)
        return Task.objects.filter(user=api_key.user)
    
    def perform_create(self, serializer):
        # if authenticated via session
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
            return

        # if authenticated via API key
        key = self.request.META.get('HTTP_AUTHORIZATION', '').replace('Api-Key ', '')
        api_key = UserAPIKey.objects.get_from_key(key)
        serializer.save(user=api_key.user)