import pytest
from rest_framework import status

from ..models import Task


@pytest.mark.django_db
class TestTaskAPIWithoutAuthentication:
    """Tests for access without authentication."""

    def test_list_tasks_without_authentication(self, api_client):
        """Tests that listing without authentication returns 403."""
        response = api_client.get("/api/v1/tasks/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_without_authentication(self, api_client, default_statuses):
        """Tests that creation without authentication returns 403."""
        data = {"title": "New Task", "description": "Description", "status": default_statuses["pending"].id}
        response = api_client.post("/api/v1/tasks/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_task_without_authentication(self, api_client, task_user1):
        """Tests that retrieval without authentication returns 403."""
        response = api_client.get(f"/api/v1/tasks/{task_user1.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_task_without_authentication(self, api_client, task_user1, default_statuses):
        """Tests that update without authentication returns 403."""
        data = {"title": "Updated", "status": default_statuses["done"].id}
        response = api_client.put(
            f"/api/v1/tasks/{task_user1.id}/", data, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_task_without_authentication(self, api_client, task_user1):
        """Tests that deletion without authentication returns 403."""
        response = api_client.delete(f"/api/v1/tasks/{task_user1.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
