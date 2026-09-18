import pytest
from django.urls import reverse

from warehouse.models import Book, Stock, Warehouse


@pytest.mark.django_db
class TestBookViewSet:
    def test_list_is_public(self, api_client, book):
        response = api_client.get(reverse("book-list"))
        assert response.status_code == 200

    def test_retrieve_is_public(self, api_client, book):
        response = api_client.get(reverse("book-detail", args=[book.id]))
        assert response.status_code == 200
        assert response.data["title"] == book.title

    def test_anonymous_cannot_create(self, api_client):
        response = api_client.post(
            reverse("book-list"),
            {
                "title": "New book",
                "authors": "Someone",
                "category": "Fiction",
                "publisher": "Pub",
                "published_year": 2024,
            },
        )
        assert response.status_code in (401, 403)

    def test_authenticated_non_admin_cannot_create(self, auth_client):
        response = auth_client.post(
            reverse("book-list"),
            {
                "title": "New book",
                "authors": "Someone",
                "category": "Fiction",
                "publisher": "Pub",
                "published_year": 2024,
            },
        )
        assert response.status_code == 403

    def test_admin_can_create(self, admin_client):
        response = admin_client.post(
            reverse("book-list"),
            {
                "title": "New book",
                "authors": "Someone",
                "category": "Fiction",
                "publisher": "Pub",
                "published_year": 2024,
            },
        )
        assert response.status_code == 201
        assert Book.objects.filter(title="New book").exists()

    def test_created_book_gets_isbn_auto_generated(self, admin_client):
        response = admin_client.post(
            reverse("book-list"),
            {
                "title": "Auto ISBN book",
                "authors": "Someone",
                "category": "Fiction",
                "publisher": "Pub",
                "published_year": 2024,
            },
        )
        assert response.status_code == 201
        assert response.data["isbn"]
        assert len(response.data["isbn"]) == 13

    def test_admin_can_delete(self, admin_client, book):
        response = admin_client.delete(reverse("book-detail", args=[book.id]))
        assert response.status_code == 204
        assert not Book.objects.filter(id=book.id).exists()

    def test_non_admin_cannot_delete(self, auth_client, book):
        response = auth_client.delete(reverse("book-detail", args=[book.id]))
        assert response.status_code == 403


@pytest.mark.django_db
class TestStockViewSet:
    def test_list_is_public(self, api_client, stock):
        response = api_client.get(reverse("stock-list"))
        assert response.status_code == 200

    def test_filter_by_isbn(self, api_client, warehouse, book):
        Stock.objects.create(warehouse=warehouse, book=book, quantity=5)
        other_book = Book.objects.create(
            title="Other",
            authors="X",
            category="Fiction",
            publisher="Pub",
            published_year=2020,
        )
        Stock.objects.create(warehouse=warehouse, book=other_book, quantity=9)

        response = api_client.get(reverse("stock-list"), {"book__isbn": book.isbn})
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["book"] == book.id

    def test_anonymous_cannot_create(self, api_client, warehouse, book):
        response = api_client.post(
            reverse("stock-list"),
            {
                "warehouse": warehouse.id,
                "book": book.id,
                "quantity": 5,
            },
        )
        assert response.status_code in (401, 403)

    def test_admin_can_create(self, admin_client, warehouse, book):
        response = admin_client.post(
            reverse("stock-list"),
            {
                "warehouse": warehouse.id,
                "book": book.id,
                "quantity": 5,
            },
        )
        assert response.status_code == 201

    def test_duplicate_book_per_warehouse_rejected(self, admin_client, stock):
        response = admin_client.post(
            reverse("stock-list"),
            {
                "warehouse": stock.warehouse.id,
                "book": stock.book.id,
                "quantity": 3,
            },
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestAvailabilityAction:
    def test_requires_isbn_param(self, api_client):
        response = api_client.get(reverse("stock-availability"))
        assert response.status_code == 400

    def test_returns_zero_for_unknown_isbn(self, api_client):
        response = api_client.get(
            reverse("stock-availability"), {"isbn": "0000000000000"}
        )
        assert response.status_code == 200
        assert response.data["total_quantity"] == 0

    def test_sums_quantity_across_warehouses(self, api_client, book):
        wh1 = Warehouse.objects.create(name="WH A")
        wh2 = Warehouse.objects.create(name="WH B")
        Stock.objects.create(warehouse=wh1, book=book, quantity=5)
        Stock.objects.create(warehouse=wh2, book=book, quantity=7)

        response = api_client.get(reverse("stock-availability"), {"isbn": book.isbn})
        assert response.status_code == 200
        assert response.data["total_quantity"] == 12

    def test_does_not_require_auth(self, api_client, stock):
        response = api_client.get(
            reverse("stock-availability"), {"isbn": stock.book.isbn}
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestDeductAction:
    def test_requires_isbn_and_quantity(self, api_client):
        response = api_client.post(reverse("stock-deduct"), {})
        assert response.status_code == 400

    def test_rejects_non_integer_quantity(self, api_client, stock):
        response = api_client.post(
            reverse("stock-deduct"),
            {
                "isbn": stock.book.isbn,
                "quantity": "abc",
            },
        )
        assert response.status_code == 400

    def test_rejects_zero_or_negative_quantity(self, api_client, stock):
        response = api_client.post(
            reverse("stock-deduct"),
            {
                "isbn": stock.book.isbn,
                "quantity": 0,
            },
        )
        assert response.status_code == 400

    def test_successful_deduction_reduces_quantity(self, api_client, warehouse, book):
        Stock.objects.create(warehouse=warehouse, book=book, quantity=10)

        response = api_client.post(
            reverse("stock-deduct"),
            {
                "isbn": book.isbn,
                "quantity": 3,
            },
        )
        assert response.status_code == 200
        assert response.data["remaining_total"] == 7

        stock_row = Stock.objects.get(warehouse=warehouse, book=book)
        assert stock_row.quantity == 7

    def test_deduction_across_multiple_warehouses(self, api_client, book):
        wh1 = Warehouse.objects.create(name="WH A")
        wh2 = Warehouse.objects.create(name="WH B")
        Stock.objects.create(warehouse=wh1, book=book, quantity=2)
        Stock.objects.create(warehouse=wh2, book=book, quantity=5)

        response = api_client.post(
            reverse("stock-deduct"),
            {
                "isbn": book.isbn,
                "quantity": 4,
            },
        )
        assert response.status_code == 200

        total_left = sum(
            Stock.objects.filter(book=book).values_list("quantity", flat=True)
        )
        assert total_left == 3

    def test_insufficient_stock_returns_409(self, api_client, warehouse, book):
        Stock.objects.create(warehouse=warehouse, book=book, quantity=2)

        response = api_client.post(
            reverse("stock-deduct"),
            {
                "isbn": book.isbn,
                "quantity": 5,
            },
        )
        assert response.status_code == 409
        assert response.data["available"] == 2

    def test_insufficient_stock_does_not_change_quantity(
        self, api_client, warehouse, book
    ):
        Stock.objects.create(warehouse=warehouse, book=book, quantity=2)

        api_client.post(reverse("stock-deduct"), {"isbn": book.isbn, "quantity": 5})

        stock_row = Stock.objects.get(warehouse=warehouse, book=book)
        assert stock_row.quantity == 2

    def test_unknown_isbn_returns_409(self, api_client):
        response = api_client.post(
            reverse("stock-deduct"),
            {
                "isbn": "0000000000000",
                "quantity": 1,
            },
        )
        assert response.status_code == 409
