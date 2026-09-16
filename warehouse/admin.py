from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Warehouse, Book, Cell


class CellInline(admin.TabularInline):
    model = Cell
    extra = 0
    fields = ("book", "code", "aisle", "shelf", "bin", "quantity", "capacity")
    autocomplete_fields = ("book",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "is_active", "cell_count")
    list_filter = ("is_active",)
    search_fields = ("name", "address")
    inlines = [CellInline]

    @admin.display(description=_("Cells"))
    def cell_count(self, obj):
        return obj.cells.count()


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "authors", "category", "publisher", "published_year", "total_quantity")
    list_filter = ("category", "publisher", "published_year")
    search_fields = ("title", "authors", "publisher")
    ordering = ("title",)


@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "code", "book", "quantity", "capacity")
    list_filter = ("warehouse",)
    search_fields = ("code", "book__title")
    autocomplete_fields = ("warehouse", "book")