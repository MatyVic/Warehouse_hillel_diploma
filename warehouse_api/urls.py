from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StockViewSet,BookViewSet

router = DefaultRouter()
router.register("books", BookViewSet)
router.register("stock", StockViewSet)

urlpatterns = router.urls