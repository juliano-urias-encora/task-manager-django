import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from .models import Task, TaskStatus, UserAPIKey


@pytest.fixture
def api_client():
    """Provides an API client for testing."""
    return APIClient()


@pytest.fixture
def user1():
    """Creates a test user."""
    return User.objects.create_user(username="user1", password="testpass123")


@pytest.fixture
def user2():
    """Creates a second test user."""
    return User.objects.create_user(username="user2", password="testpass123")


@pytest.fixture
def default_statuses():
    """Creates default task statuses."""
    pending = TaskStatus.objects.create(name="Pending", is_default=True)
    in_progress = TaskStatus.objects.create(name="In Progress", is_default=True)
    done = TaskStatus.objects.create(name="Done", is_default=True)
    return {"pending": pending, "in_progress": in_progress, "done": done}


@pytest.fixture
def api_key_user1(user1):
    """Creates an API key for user 1."""
    api_key, key = UserAPIKey.objects.create_key(name="user1_key", user=user1)
    api_key._key = key  # Stores the key for use in tests
    return api_key


@pytest.fixture
def api_key_user2(user2):
    """Creates an API key for user 2."""
    api_key, key = UserAPIKey.objects.create_key(name="user2_key", user=user2)
    api_key._key = key
    return api_key


@pytest.fixture
def task_user1(user1, default_statuses):
    """Creates a task for user 1."""
    return Task.objects.create(
        title="Task User 1",
        description="Description for user 1 task",
        status=default_statuses["pending"],
        user=user1,
    )


@pytest.fixture
def task_user2(user2, default_statuses):
    """Creates a task for user 2."""
    return Task.objects.create(
        title="Task User 2",
        description="Description for user 2 task",
        status=default_statuses["pending"],
        user=user2,
    )


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

    def test_delete_task_with_api_key(self, api_client, api_key_user1, default_statuses):
        """Tests deleting a task with API Key."""
        task = Task.objects.create(
            title="Task to Delete",
            description="This will be deleted",
            status=default_statuses["pending"],
            user=api_key_user1.user,
        )

        task_id = task.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_user1._key}")
        response = api_client.delete(f"/api/v1/tasks/{task_id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Checks if task was deleted
        assert not Task.objects.filter(id=task_id).exists()


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

