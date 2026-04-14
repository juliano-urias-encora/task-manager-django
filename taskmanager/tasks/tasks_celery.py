import logging
import time

from celery import shared_task

from .models import Task

logger = logging.getLogger("taskmanager")


@shared_task
def delete_task_permanently(task_id):
    """
    Async task to physically remove the task from the database.
    Simulates a long-running process with time.sleep().
    """
    try:
        task = Task.objects.get(id=task_id)

        # Simulate a heavy operation (e.g., cascading deletes, cleaning up files)
        time.sleep(5)

        task.delete()
        logger.info(f"Task {task_id} successfully deleted from the database.")
    except Task.DoesNotExist:
        # Task might have been already deleted
        logger.warning(f"Task {task_id} not found.")
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
