from django.db import models
from django.db.models import Sum
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

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    def __str__(self):
        return self.title

    @property
    def total_quantity(self):
        return self.cells.aggregate(total=Sum("quantity"))["total"] or 0


class Cell(models.Model):
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="cells",
        verbose_name=_("Warehouse"),
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cells",
        verbose_name=_("Book"),
    )
    code = models.CharField(max_length=20, verbose_name=_("Code"))
    aisle = models.CharField(max_length=10, blank=True, verbose_name=_("Aisle"))
    shelf = models.CharField(max_length=10, blank=True, verbose_name=_("Shelf"))
    bin = models.CharField(max_length=10, blank=True, verbose_name=_("Bin"))
    capacity = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Capacity")
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name=_("Quantity"))

    class Meta:
        verbose_name = _("Cell")
        verbose_name_plural = _("Cells")
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"], name="unique_cell_code_per_warehouse"
            )
        ]

    def __str__(self):
        return f"{self.warehouse.name} / {self.code}"
