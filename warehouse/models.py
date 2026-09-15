from django.db import models
from django.utils.translation import gettext_lazy as _

class Book(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    authors = models.CharField(max_length=255, verbose_name=_("Authors"))
    category = models.CharField(max_length=100, verbose_name=_("Category"))
    publisher = models.CharField(max_length=100, verbose_name=_("Publisher")
    )
    published_year = models.IntegerField(verbose_name=_("Published year"))
    amount = models.IntegerField(verbose_name=_("Amount"))
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Price")
    )
    available = models.BooleanField(default=True, verbose_name=_("Available"))

class Warehouse(models.Model):
    pass



class WarehouseCells(models.Model):
    pass