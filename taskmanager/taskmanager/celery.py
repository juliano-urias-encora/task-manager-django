import os
from celery import Celery

# Define the default settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')

# Creates the Celery application instance
app = Celery('taskmanager')

# Reads Django configuration (everything starting with CELERY_ goes to Celery)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically searches for tasks.py files in your apps (ex: tasks/tasks.py)
app.autodiscover_tasks()