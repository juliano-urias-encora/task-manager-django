from django.db import migrations


def migrate_status_data(apps, schema_editor):
    Task = apps.get_model("tasks", "Task")
    TaskStatus = apps.get_model("tasks", "TaskStatus")

    pending_status = TaskStatus.objects.get(name="Pending")
    in_progress_status = TaskStatus.objects.get(name="In Progress")
    done_status = TaskStatus.objects.get(name="Done")

    for task in Task.objects.all():
        if task.status == "pending":
            task.status_fk = pending_status
        elif task.status == "in_progress":
            task.status_fk = in_progress_status
        elif task.status == "done":
            task.status_fk = done_status

        task.save()


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0005_task_status_fk"),
    ]

    operations = [
        migrations.RunPython(migrate_status_data),
    ]
