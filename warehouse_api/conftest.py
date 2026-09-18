import os
import django
import factory
import pytest
from rest_framework.test import APIClient

from user_management.models import CustomUser
from warehouse.models import Book, Stock, Warehouse

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "warehouse_hillel_diploma.settings.development"
)


django.setup()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    work_id = factory.Sequence(lambda n: f"W-{n:04d}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123")
        user = model_class(*args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    name = factory.Sequence(lambda n: f"Warehouse {n}")
    address = "Kyiv, Test street 1"
    is_active = True


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f"Book {n}")
    authors = "Test Author"
    category = "Fiction"
    publisher = "Test Publisher"
    published_year = 2020


class StockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stock

    warehouse = factory.SubFactory(WarehouseFactory)
    book = factory.SubFactory(BookFactory)
    quantity = 10


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def warehouse(db):
    return WarehouseFactory()


@pytest.fixture
def book(db):
    return BookFactory()


@pytest.fixture
def stock(db, warehouse, book):
    return StockFactory(warehouse=warehouse, book=book)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client
