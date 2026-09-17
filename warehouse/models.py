import random
import string

from django.db import models
from django.utils.translation import gettext_lazy as _


class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    address = models.CharField(max_length=255, blank=True, verbose_name=_("Address"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))

    class Meta:
        verbose_name = _("Warehouse")
        verbose_name_plural = _("Warehouses")

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    authors = models.CharField(max_length=255, verbose_name=_("Authors"))
    category = models.CharField(max_length=100, verbose_name=_("Category"))
    publisher = models.CharField(max_length=100, verbose_name=_("Publisher"))
    published_year = models.IntegerField(verbose_name=_("Published year"))
    isbn = models.CharField(
        max_length=20, unique=True, blank=True, null=True, verbose_name=_("ISBN")
    )

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    def __str__(self):
        return self.title

    @staticmethod
    def generate_isbn():
        prefix = "978"
        body = "".join(str(random.randint(0, 9)) for _ in range(9))
        digits = prefix + body
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
        check_digit = (10 - (total % 10)) % 10

        return digits + str(check_digit)

    def save(self, *args, **kwargs):
        if not self.isbn:
            new_sbn = self.generate_isbn()
            while Book.objects.filter(isbn=new_sbn).exists():
                new_sbn = self.generate_isbn()
            self.isbn = new_sbn
        super().save(*args, **kwargs)


class Stock(models.Model):
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock",
        verbose_name=_("Warehouse"),
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="stock",
        verbose_name=_("Book"),
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name=_("Quantity"))

    class Meta:
        verbose_name = _("Stock item")
        verbose_name_plural = _("Stock items")
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "book"], name="unique_book_per_warehouse"
            )
        ]

    def __str__(self):
        return f"{self.warehouse.name} — {self.book.title} ({self.quantity})"
