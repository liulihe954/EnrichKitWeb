# time_tasks/celery/__init__.py
from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# You can use rabbitmq instead here.
BASE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EnrichKitWeb.settings')

app = Celery('EnrichKitWeb')

app.loader.override_backends['django-db'] = 'django_celery_results.backends.database:DatabaseBackend'

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# app.conf.broker_url = BASE_REDIS_URL
app.conf.update(
    broker_url=BASE_REDIS_URL,
    result_backend=BASE_REDIS_URL
)

# this allows you to schedule items in the Django admin.
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'


