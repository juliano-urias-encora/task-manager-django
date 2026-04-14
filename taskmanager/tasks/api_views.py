from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from .tasks_celery import delete_task_permanently
from .models import Task, TaskStatus, UserAPIKey
from .serializers import TaskSerializer, TaskStatusSerializer


class HasUserAPIKey(BasePermission):
    def has_permission(self, request, view):
        # allow session authenticated users (browsable API)
        if request.user and request.user.is_authenticated:
            return True
        # otherwise check API key
        key = request.META.get("HTTP_AUTHORIZATION", "").replace("Api-Key ", "")
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
        key = self.request.META.get("HTTP_AUTHORIZATION", "").replace("Api-Key ", "")
        api_key = UserAPIKey.objects.get_from_key(key)
        return Task.objects.filter(user=api_key.user, deleted_at__isnull=True)

    def perform_create(self, serializer):
        # if authenticated via session
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
            return

        # if authenticated via API key
        key = self.request.META.get("HTTP_AUTHORIZATION", "").replace("Api-Key ", "")
        api_key = UserAPIKey.objects.get_from_key(key)
        serializer.save(user=api_key.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 1. Perform Soft Delete: mark the timestamp and save
        instance.deleted_at = timezone.now()
        instance.save()
        
        # 2. Dispatch the background task to Celery via RabbitMQ
        # The .delay() method sends the message to the broker asynchronously
        delete_task_permanently.delay(instance.id)
        
        # 3. Return immediate response to the client (202 Accepted)
        return Response(
            {"detail": "Task marked for deletion. It will be removed shortly."},
            status=status.HTTP_202_ACCEPTED
        )


class TaskStatusViewSet(ModelViewSet):
    serializer_class = TaskStatusSerializer
    permission_classes = [HasUserAPIKey]

    def get_user_from_request(self):
        """Helper to get the user either via session or API Key"""
        if self.request.user and self.request.user.is_authenticated:
            return self.request.user
        key = self.request.META.get('HTTP_AUTHORIZATION', '').replace('Api-Key ', '')
        api_key = UserAPIKey.objects.get_from_key(key)
        return api_key.user

    def get_queryset(self):
        user = self.get_user_from_request()
        # User sees their own statuses and the default system statuses
        return TaskStatus.objects.filter(Q(is_default=True) | Q(user=user))

    def perform_create(self, serializer):
        user = self.get_user_from_request()
        # Force is_default=False for any status created via API
        serializer.save(user=user, is_default=False)

    def perform_update(self, serializer):
        # Prevents editing of a default status
        if serializer.instance.is_default:
            raise PermissionDenied("You cannot edit a default system status.")
        serializer.save()

    def perform_destroy(self, instance):
        # Prevents deletion of a default status
        if instance.is_default:
            raise PermissionDenied("You cannot delete a default system status.")
        instance.delete()