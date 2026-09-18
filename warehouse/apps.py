from django.apps import AppConfig
from django.db.models import Model


class WarehouseConfig(AppConfig):
    name = "warehouse"

    def ready(self):
        import warehouse.signals  # noqa: F401