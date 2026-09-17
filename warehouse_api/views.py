import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum
from rest_framework.throttling import UserRateThrottle

from warehouse.models import Book, Stock

logger = logging.getLogger(__name__)


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class BooksLimitOffsetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 50


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = "__all__"


class StockLimitOffsetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 50


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = BooksLimitOffsetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    class Meta:
        model = Book
        fields = "__all__"

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [permissions.AllowAny()]


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["book", "warehouse", "book__isbn"]
    pagination_class = StockLimitOffsetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    class Meta:
        model = Stock
        fields = "__all__"

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def availability(self, request):
        isbn = request.query_params.get("isbn")
        if not isbn:
            return Response({"detail": "isbn parameter required"}, status=400)

        total = (
            Stock.objects.filter(book__isbn=isbn).aggregate(total=Sum("quantity"))[
                "total"
            ]
            or 0
        )

        return Response({"isbn": isbn, "total_quantity": total})

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def deduct(self, request):
        isbn = request.data.get("isbn")
        quantity = request.data.get("quantity")

        if not isbn or quantity is None:
            return Response({"detail": "isbn and quantity are required"}, status=400)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response({"detail": "quantity must be an integer"}, status=400)

        if quantity <= 0:
            return Response({"detail": "quantity must be positive"}, status=400)

        with transaction.atomic():
            stock_rows = (
                Stock.objects.select_for_update().filter(book__isbn=isbn).order_by("id")
            )

            total_available = sum(row.quantity for row in stock_rows)
            if total_available < quantity:
                logger.warning(
                    "Deduct rejected for isbn=%s: requested %s, available %s",
                    isbn,
                    quantity,
                    total_available,
                )
                return Response(
                    {
                        "detail": "Not enough stock",
                        "requested": quantity,
                        "available": total_available,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            remaining = quantity
            for row in stock_rows:
                if remaining <= 0:
                    break
                take = min(row.quantity, remaining)
                row.quantity -= take
                row.save(update_fields=["quantity"])
                remaining -= take

        logger.info("Deducted %s units of isbn=%s from stock", quantity, isbn)
        return Response(
            {
                "isbn": isbn,
                "deducted": quantity,
                "remaining_total": total_available - quantity,
            }
        )
