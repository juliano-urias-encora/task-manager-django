import pytest
from unittest.mock import patch
from rest_framework import status

from ..models import Task, TaskStatus


@pytest.mark.django_db
class TestTaskAPIWithAPIKey:
    """Tests for task API with API Key authentication."""

    def test_list_tasks_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests task listing with API Key."""
        # Creates tasks for the user
        Task.objects.create(
            title="Task 1", description="Description 1", status=default_statuses["pending"], user=api_key_user1.user
        )
        Task.objects.create(
            title="Task 2", description="Description 2", status=default_statuses["pending"], user=api_key_user1.user
        )

        # Makes request with API Key
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get("/api/v1/tasks/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]["title"] == "Task 1"
        assert response.data[1]["title"] == "Task 2"

    def test_create_task_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests task creation with API Key."""
        data = {
            "title": "New Task",
            "description": "New task description",
            "status": default_statuses["pending"].id,
        }

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.post("/api/v1/tasks/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Task"
        assert response.data["description"] == "New task description"
        assert response.data["status_name"] == "Pending"

        # Checks if task was created in database
        assert Task.objects.filter(title="New Task", user=api_key_user1.user).exists()

    def test_retrieve_task_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests retrieving a specific task with API Key."""
        task = Task.objects.create(
            title="Specific Task",
            description="Task for retrieval",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get(f"/api/v1/tasks/{task.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Specific Task"
        assert response.data["id"] == task.id
        assert response.data["status_name"] == "Pending"

    def test_update_task_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests updating a task with API Key."""
        task = Task.objects.create(
            title="Original Title",
            description="Original description",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "status": default_statuses["done"].id,
        }

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.put(f"/api/v1/tasks/{task.id}/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"
        assert response.data["status_name"] == "Done"

        # Checks if task was updated in database
        task.refresh_from_db()
        assert task.title == "Updated Title"
        assert task.status.name == "Done"

    def test_partial_update_task_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests partial update of task with API Key."""
        task = Task.objects.create(
            title="Original Title",
            description="Original description",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        data = {"status": default_statuses["in_progress"].id}

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.patch(f"/api/v1/tasks/{task.id}/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status_name"] == "In Progress"
        assert response.data["title"] == "Original Title"  # Not changed

    @patch('tasks.api_views.delete_task_permanently.delay')
    def test_delete_task_with_api_key(self, mock_celery_task, api_client, api_key_user1, default_statuses):
        """Tests soft delete of a task with API Key (returns 202 Accepted)."""
        task = Task.objects.create(
            title="Task to Delete",
            description="This will be deleted",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        task_id = task.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/tasks/{task_id}/")

        # Should return 202 Accepted (async operation)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "deletion" in response.data["detail"].lower()

        # Task should still exist in database but marked as deleted
        task = Task.objects.get(id=task_id)
        assert task.deleted_at is not None

        # Celery task should have been called
        mock_celery_task.assert_called_once_with(task_id)
