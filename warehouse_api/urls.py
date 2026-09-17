from django.urls import path
from .views import StockViewSet,BookViewSet

app_name = "warehouse_api"
urlpatterns = [
    path("stock", StockViewSet.as_view(), name="stocks"),
    path("book", BookViewSet.as_view(), name="books"),
]