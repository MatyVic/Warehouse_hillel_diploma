from django.urls import path
from .views import WarehouseListView, WarehouseStockView, WarehouseStockExportView

app_name = "warehouse"
urlpatterns = [
    path("/", WarehouseListView.as_view(), name="list"),
    path("<int:pk>/", WarehouseStockView.as_view(), name="stock"),
    path("<int:pk>/export/", WarehouseStockExportView.as_view(), name="stock_export"),
]