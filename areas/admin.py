from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from areas.models import Area, Cell
from django.db import transaction

# Register your models here.


@admin.register(Area)
class AreaAdmin(GISModelAdmin):
    list_display = ["name", "update_timestamp"]

    @transaction.atomic
    @admin.action(description="Generate and save cells for selected areas")
    def generate_and_save_cells(modeladmin, request, areas: list[Area]):
        for area in areas:
            Cell.create_cells_from_area(area, max_tile_size=5000)

    actions = [generate_and_save_cells]


@admin.register(Cell)
class CellAdmin(GISModelAdmin):
    list_display = ["name", "update_timestamp"]

    @transaction.atomic
    @admin.action(description="Reset search pending")
    def reset_search_pending(modeladmin, request, items):
        for item in items:
            item.reset_search_pending()

    @transaction.atomic
    @admin.action(description="Reset last search timestamp")
    def reset_last_search_timestamp(modeladmin, request, items):
        for item in items:
            item.reset_last_search_timestamp()

    actions = [reset_search_pending, reset_last_search_timestamp]

    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False
