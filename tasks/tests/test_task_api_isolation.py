import pytest
from rest_framework import status

from ..models import Task


@pytest.mark.django_db
class TestTaskAPIIsolation:
    """Tests for user isolation."""

    def test_user1_cannot_list_user2_tasks(self, api_client, api_key_user1, task_user2):
        """Tests that user 1 cannot list tasks from user 2."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get("/api/v1/tasks/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0  # Should not return tasks from user 2

    def test_user1_cannot_retrieve_user2_task(
        self, api_client, api_key_user1, task_user2
    ):
        """Tests that user 1 cannot retrieve a task from user 2."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get(f"/api/v1/tasks/{task_user2.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user1_cannot_update_user2_task(
        self, api_client, api_key_user1, task_user2
    ):
        """Tests that user 1 cannot update a task from user 2."""
        data = {"title": "Hacked Title"}

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.put(
            f"/api/v1/tasks/{task_user2.id}/", data, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verifies that the task was not changed
        task_user2.refresh_from_db()
        assert task_user2.title == "Task User 2"

    def test_user1_cannot_delete_user2_task(
        self, api_client, api_key_user1, task_user2
    ):
        """Tests that user 1 cannot delete a task from user 2."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/tasks/{task_user2.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verifies that the task still exists
        assert Task.objects.filter(id=task_user2.id).exists()

    def test_api_key_user1_cannot_access_user2_api_key(
        self, api_client, api_key_user1, api_key_user2, task_user2
    ):
        """Tests that API key from user 1 does not work for tasks from user 2."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get(f"/api/v1/tasks/{task_user2.id}/")

        # Should return 404 because it cannot access another user's task
        assert response.status_code == status.HTTP_404_NOT_FOUND
