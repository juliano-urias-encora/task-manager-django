import pytest
from rest_framework import status

from ..models import TaskStatus


@pytest.mark.django_db
class TestTaskStatusAPI:
    """Tests for task status API."""

    def test_list_default_statuses(self, api_client, api_key_user1, default_statuses):
        """Tests that users can see default statuses."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get("/api/v1/statuses/")

        assert response.status_code == status.HTTP_200_OK
        # Check that default statuses are present
        status_names = {item["name"] for item in response.data}
        assert "Pending" in status_names
        assert "In Progress" in status_names
        assert "Done" in status_names
        # All returned should be default or belong to user
        for status_item in response.data:
            assert status_item["is_default"] == True or status_item.get("_user_created", False)

    def test_create_custom_status_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests creating a custom status for a user."""
        data = {"name": "On Hold"}

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.post("/api/v1/statuses/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "On Hold"
        assert response.data["is_default"] == False

        # Verify it was created in database
        custom_status = TaskStatus.objects.get(name="On Hold")
        assert custom_status.user == api_key_user1.user
        assert custom_status.is_default == False

    def test_user_sees_only_their_custom_statuses(self, api_client, api_key_user1, api_key_user2, default_statuses):
        """Tests that user 1 only sees their own custom statuses and defaults."""
        # Create custom status for user 1
        custom_status_user1 = TaskStatus.objects.create(
            name="Urgent", user=api_key_user1.user, is_default=False
        )

        # Create custom status for user 2
        custom_status_user2 = TaskStatus.objects.create(
            name="Blocked", user=api_key_user2.user, is_default=False
        )

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.get("/api/v1/statuses/")

        assert response.status_code == status.HTTP_200_OK
        status_names = {item["name"] for item in response.data}
        # Should see: defaults + 1 custom (Urgent)
        assert "Urgent" in status_names
        assert "Blocked" not in status_names
        assert "Pending" in status_names

    def test_cannot_update_default_status(self, api_client, api_key_user1, default_statuses):
        """Tests that default statuses cannot be updated."""
        pending_status = default_statuses["pending"]
        data = {"name": "Changed"}

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.patch(f"/api/v1/statuses/{pending_status.id}/", data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_can_update_custom_status(self, api_client, api_key_user1):
        """Tests that custom statuses can be updated."""
        custom_status = TaskStatus.objects.create(
            name="Old Name", user=api_key_user1.user, is_default=False
        )

        data = {"name": "New Name"}

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.patch(f"/api/v1/statuses/{custom_status.id}/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "New Name"

        custom_status.refresh_from_db()
        assert custom_status.name == "New Name"

    def test_cannot_delete_default_status(self, api_client, api_key_user1, default_statuses):
        """Tests that default statuses cannot be deleted."""
        pending_status = default_statuses["pending"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/statuses/{pending_status.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify it still exists
        assert TaskStatus.objects.filter(id=pending_status.id).exists()

    def test_can_delete_custom_status(self, api_client, api_key_user1):
        """Tests that custom statuses can be deleted."""
        custom_status = TaskStatus.objects.create(
            name="To Delete", user=api_key_user1.user, is_default=False
        )
        status_id = custom_status.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/statuses/{status_id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it was deleted
        assert not TaskStatus.objects.filter(id=status_id).exists()

    def test_default_statuses_are_read_only(self, api_client, api_key_user1, default_statuses):
        """Tests that default statuses cannot be modified or deleted."""
        pending_status = default_statuses["pending"]
        
        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        
        # Try to update
        response = api_client.patch(f"/api/v1/statuses/{pending_status.id}/", {"name": "Modified"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try to delete
        response = api_client.delete(f"/api/v1/statuses/{pending_status.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
