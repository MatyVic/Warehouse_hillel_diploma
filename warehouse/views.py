import csv
from multiprocessing import context

from django.http import HttpResponse
from django.views.generic import ListView, DetailView

from .models import Warehouse, Stock

from warehouse.models import Warehouse


class WarehouseListView(ListView):
    model = Warehouse
    template_name = "warehouse/warehouse_list.html"
    context_object_name = "warehouses"


class WarehouseStockView(DetailView):
    model = Warehouse
    template_name = "warehouse/warehouse_stock.html"
    context_object_name = "warehouse"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stock"] = (
            Stock.objects.filter(warehouse=self.object)
            .select_related("book")
            .order_by("book__title")
        )
        return context


class WarehouseStockExportView(WarehouseStockView):

    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{context["warehouse"].name}_stock.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(["Title", "Authors", "Category", "Quantity"])
        for item in context["stock"]:
            writer.writerow(
                [item.book.title, item.book.authors, item.book.category, item.quantity]
            )
        return response
