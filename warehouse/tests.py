import pytest
from django.db import IntegrityError

from warehouse.models import Stock, Warehouse


@pytest.mark.django_db
class TestWarehouseModel:
    def test_str_returns_name(self, warehouse):
        assert str(warehouse) == warehouse.name

    def test_name_must_be_unique(self, warehouse):
        with pytest.raises(IntegrityError):
            Warehouse.objects.create(name=warehouse.name)

    def test_is_active_defaults_to_true(self):
        wh = Warehouse.objects.create(name="New warehouse")
        assert wh.is_active is True


@pytest.mark.django_db
class TestBookModel:
    def test_str_returns_title(self, book):
        assert str(book) == book.title

    def test_book_can_exist_without_stock(self, book):
        assert book.stock.count() == 0


@pytest.mark.django_db
class TestStockModel:
    def test_str_representation(self, stock):
        expected = f"{stock.warehouse.name} — {stock.book.title} ({stock.quantity})"
        assert str(stock) == expected

    def test_same_book_twice_in_same_warehouse_raises(self, warehouse, book):
        Stock.objects.create(warehouse=warehouse, book=book, quantity=5)
        with pytest.raises(IntegrityError):
            Stock.objects.create(warehouse=warehouse, book=book, quantity=3)

    def test_same_book_in_different_warehouses_is_allowed(self, book):
        wh1 = Warehouse.objects.create(name="WH 1")
        wh2 = Warehouse.objects.create(name="WH 2")
        Stock.objects.create(warehouse=wh1, book=book, quantity=5)
        Stock.objects.create(warehouse=wh2, book=book, quantity=7)
        assert book.stock.count() == 2

    def test_total_quantity_across_warehouses(self, book):
        wh1 = Warehouse.objects.create(name="WH A")
        wh2 = Warehouse.objects.create(name="WH B")
        Stock.objects.create(warehouse=wh1, book=book, quantity=5)
        Stock.objects.create(warehouse=wh2, book=book, quantity=7)
        total = sum(book.stock.values_list("quantity", flat=True))
        assert total == 12
