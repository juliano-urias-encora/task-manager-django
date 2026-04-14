import pytest
from unittest.mock import patch
from rest_framework import status

from ..models import Task


@pytest.mark.django_db
class TestAsyncTaskDeletion:
    """Tests for the async task deletion flow (soft delete + Celery)."""

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_soft_delete_marks_task_as_deleted(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests that soft delete marks task with deleted_at timestamp."""
        task = Task.objects.create(
            title="Task for Soft Delete",
            description="This will be soft deleted",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/tasks/{task.id}/")

        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Verify task is marked as deleted
        task.refresh_from_db()
        assert task.deleted_at is not None

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_soft_deleted_tasks_not_listed(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests that soft-deleted tasks don't appear in task listings."""
        # Create multiple tasks
        task1 = Task.objects.create(
            title="Active Task",
            description="This is active",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )
        
        task2 = Task.objects.create(
            title="Task to Delete",
            description="This will be deleted",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        # Delete task2
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        api_client.delete(f"/api/v1/tasks/{task2.id}/")

        # List tasks
        response = api_client.get("/api/v1/tasks/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Active Task"
        assert response.data[0]["id"] == task1.id

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_cannot_access_soft_deleted_task(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests that soft-deleted tasks cannot be accessed directly."""
        task = Task.objects.create(
            title="Task to Delete",
            description="Will be deleted",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )
        task_id = task.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        
        # Delete the task
        api_client.delete(f"/api/v1/tasks/{task_id}/")

        # Try to access it
        response = api_client.get(f"/api/v1/tasks/{task_id}/")

        # Should not be found since it's soft-deleted
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_celery_task_dispatched_on_delete(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests that Celery task is dispatched when task is deleted."""
        task = Task.objects.create(
            title="Task for Async Delete",
            description="Will be deleted asynchronously",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )
        task_id = task.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/tasks/{task_id}/")

        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Verify Celery task was called with correct task_id
        mock_celery_task.assert_called_once_with(task_id)

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_delete_returns_202_accepted(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests that delete returns 202 Accepted status code."""
        task = Task.objects.create(
            title="Task",
            description="Description",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/tasks/{task.id}/")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "detail" in response.data
        assert "shortly" in response.data["detail"].lower()

    def test_permanent_deletion_via_celery_task(self, api_key_user1, default_statuses):
        """Tests that the Celery task permanently deletes tasks."""
        from tasks.tasks_celery import delete_task_permanently
        
        task = Task.objects.create(
            title="Task to Permanently Delete",
            description="Will be deleted by Celery",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )
        task_id = task.id

        # Verify task exists
        assert Task.objects.filter(id=task_id).exists()

        # Call Celery task directly (in test environment, it runs synchronously)
        delete_task_permanently(task_id)

        # Verify task is permanently deleted
        assert not Task.objects.filter(id=task_id).exists()

    def test_permanent_deletion_handles_missing_task(self):
        """Tests that Celery task gracefully handles already-deleted tasks."""
        from tasks.tasks_celery import delete_task_permanently
        
        # Try to delete non-existent task - should not raise exception
        try:
            delete_task_permanently(999999)
        except Task.DoesNotExist:
            pytest.fail("Celery task should handle missing tasks gracefully")

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_update_soft_deleted_task_fails(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests that updating a soft-deleted task returns 404."""
        task = Task.objects.create(
            title="Task",
            description="Description",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )
        task_id = task.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        
        # Delete the task
        api_client.delete(f"/api/v1/tasks/{task_id}/")

        # Try to update it
        response = api_client.patch(
            f"/api/v1/tasks/{task_id}/",
            {"title": "Updated Title"},
            format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
