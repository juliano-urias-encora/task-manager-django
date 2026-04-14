# Task Manager Django

A task management application built with Django REST Framework, featuring API Key authentication, custom task statuses, and asynchronous processing with Celery.

## Overview

This application provides:
- Create, read, update, and delete tasks via REST API
- Manage task statuses (Pending, In Progress, Done, etc.)
- Create custom task statuses
- API Key authentication
- Web interface for task management
- Complete user data isolation (multi-tenancy)

## Technology Stack

- Django 6.0.4
- Django REST Framework 3.17.1
- Celery 5.6.3
- RabbitMQ
- MySQL 8
- Docker & Docker Compose
- Pytest 9.0.3 with pytest-django and pytest-env

## Quick Start with Docker

```bash
cd taskmanager
cp .env.example .env
docker-compose up --build
```

Application will be available at `http://localhost:8000`

## Local Setup

### Prerequisites

- Python 3.10+
- MySQL 8 (SQLite for testing)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r taskmanager/requirements.txt

# Configure environment
cd taskmanager
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

## Testing

Tests run without external dependencies (MySQL, RabbitMQ, etc.) using SQLite in-memory database.

```bash
cd taskmanager

# Run all tests
pytest

# Run specific test file
pytest tasks/tests/test_task_api_with_api_key.py -v

# Run specific test class
pytest tasks/tests/test_task_api_with_api_key.py::TestTaskAPIWithAPIKey -v

# Run specific test
pytest tasks/tests/test_task_api_with_api_key.py::TestTaskAPIWithAPIKey::test_list_tasks_with_api_key -v

# Coverage report
pytest --cov=tasks --cov-report=html
```

Total: 32 tests across 5 test modules.

## Project Structure

```
task-manager-django/
├── taskmanager/              # Django configuration
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
├── tasks/                    # Main app
│   ├── models.py             # Task, TaskStatus, UserAPIKey
│   ├── serializers.py
│   ├── api_views.py
│   ├── api_urls.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks_celery.py
│   ├── admin.py
│   ├── migrations/
│   └── tests/
│       ├── conftest.py
│       ├── test_task_api_with_api_key.py
│       ├── test_task_api_without_authentication.py
│       ├── test_task_api_isolation.py
│       ├── test_task_status_api.py
│       └── test_async_task_deletion.py
├── templates/
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── manage.py
```

## API Key Authentication

Create an API Key through Django admin:

1. Go to `http://localhost:8000/admin`
2. Navigate to "User API Keys"
3. Create and copy your key

Use in requests:

```bash
curl -H "Authorization: Api-Key your-key-here" \
     http://localhost:8000/api/v1/tasks/
```

## API Endpoints

### Tasks

```
GET    /api/v1/tasks/          - List user's tasks
POST   /api/v1/tasks/          - Create task
GET    /api/v1/tasks/{id}/     - Retrieve task
PUT    /api/v1/tasks/{id}/     - Update task (full)
PATCH  /api/v1/tasks/{id}/     - Update task (partial)
DELETE /api/v1/tasks/{id}/     - Delete task (soft delete)
```

### Statuses

```
GET    /api/v1/statuses/       - List statuses
POST   /api/v1/statuses/       - Create status
PATCH  /api/v1/statuses/{id}/  - Update status (custom only)
DELETE /api/v1/statuses/{id}/  - Delete status (custom only)
```

### Example Requests

```bash
# List tasks
curl -H "Authorization: Api-Key xyz123" \
     http://localhost:8000/api/v1/tasks/

# Create task
curl -X POST -H "Authorization: Api-Key xyz123" \
     -H "Content-Type: application/json" \
     -d '{"title": "Task title", "description": "Description", "status": 1}' \
     http://localhost:8000/api/v1/tasks/

# Update task
curl -X PATCH -H "Authorization: Api-Key xyz123" \
     -H "Content-Type: application/json" \
     -d '{"status": 2}' \
     http://localhost:8000/api/v1/tasks/1/

# Delete task
curl -X DELETE -H "Authorization: Api-Key xyz123" \
     http://localhost:8000/api/v1/tasks/1/
```

## Environment Variables

Create `.env` in `taskmanager/` directory:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=taskmanager
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=3306

# RabbitMQ
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest

# Celery
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
```

## Celery & RabbitMQ

Run Celery worker:

```bash
# With Docker Compose
docker-compose up celery_worker

# Locally (requires RabbitMQ running)
celery -A taskmanager worker --loglevel=info
```

Monitor with Flower:

```bash
docker-compose up flower
# Visit http://localhost:5555
```

## Data Models

### Task
- title: CharField
- description: TextField
- status: ForeignKey(TaskStatus)
- user: ForeignKey(User)
- created_at: DateTimeField
- updated_at: DateTimeField
- deleted_at: DateTimeField (soft delete)

### TaskStatus
- name: CharField
- user: ForeignKey(User, nullable) - null for default statuses
- is_default: BooleanField
- created_at: DateTimeField

### UserAPIKey
- user: ForeignKey(User)
- key: CharField (unique)
- name: CharField
- created_at: DateTimeField

## Docker Compose Services

- db: MySQL 8
- web: Django application
- rabbitmq: Message broker
- celery_worker: Celery worker
- flower: Celery monitoring UI

## Web Interface

```
/                               - Home
/tasks/                         - Task list
/tasks/create/                  - Create task
/tasks/<id>/update/             - Edit task
/tasks/<id>/delete/             - Delete task
/accounts/register/             - Register
/accounts/login/                - Login
/admin/                         - Django admin
```

## License

Educational project.
