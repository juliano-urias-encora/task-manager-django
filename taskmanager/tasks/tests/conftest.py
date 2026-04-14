import pytest
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from tasks.models import Task, TaskStatus, UserAPIKey


# Configure Celery to use eager mode for tests
@pytest.fixture(scope="session", autouse=True)
def celery_config():
    """Configure Celery to run tasks synchronously during tests."""
    from celery import current_app
    current_app.conf.CELERY_ALWAYS_EAGER = True
    current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    return current_app.conf


@pytest.fixture
def mock_celery_task(monkeypatch):
    """Mock the Celery task to avoid connecting to RabbitMQ."""
    mock_delete = patch('tasks.api_views.delete_task_permanently')
    return mock_delete.start()


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
