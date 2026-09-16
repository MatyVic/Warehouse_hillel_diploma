import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse_hillel_diploma.settings.development")

app = Celery("warehouse_hillel_diploma")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()