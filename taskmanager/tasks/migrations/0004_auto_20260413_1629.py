from django.db import migrations

def create_default_statuses(apps, schema_editor):
    TaskStatus = apps.get_model('tasks', 'TaskStatus')
    
    default_statuses = ['Pending', 'In Progress', 'Done']
    
    for status_name in default_statuses:
        TaskStatus.objects.create(name=status_name, is_default=True, user=None)

class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_taskstatus'), 
    ]

    operations = [
        migrations.RunPython(create_default_statuses),
    ]