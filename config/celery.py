import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.brocker_url='redis://redis:6379/0'
app.conf.result_backend='redis://redis:6379/0'

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'deactivate-inactive-users-daily': {
        'task': 'materials.tasks.deactivate_inactive_users',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'check-course-updates': {
        'task': 'materials.tasks.check_and_notify_course_updates',
        'schedule': crontab(minute=0),  # Every hour
    },
}
app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')