import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse_hillel_diploma.settings.development")
app = Celery("warehouse_hillel_diploma")
