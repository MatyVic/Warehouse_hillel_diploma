from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Warehouse, Book, Stock


class StockInline(admin.TabularInline):
    model = Stock
    extra = 0
    fields = ("book", "quantity")
    autocomplete_fields = ("book",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "is_active", "total_books")
    list_filter = ("is_active",)
    search_fields = ("name", "address")
    inlines = [StockInline]

    @admin.display(description=_("Books in stock"))
    def total_books(self, obj):
        return obj.stock.count()


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "authors",
        "category",
        "publisher",
        "published_year",
        "total_quantity",
    )
    list_filter = ("category", "publisher", "published_year")
    search_fields = ("title", "authors", "publisher")
    ordering = ("title",)

    @admin.display(description=_("Total quantity"))
    def total_quantity(self, obj):
        return sum(obj.stock.values_list("quantity", flat=True))


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "book", "quantity")
    list_filter = ("warehouse",)
    search_fields = ("book__title", "warehouse__name")
    autocomplete_fields = ("warehouse", "book")
