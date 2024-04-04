from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from flats.models import Flat, FlatPrice, Offer
from django.db import transaction

# Register your models here.


@admin.register(Flat)
class FlatAdmin(GISModelAdmin):
    list_display = [
        "address",
        "rooms_count",
        "total_area",
        "floor_number",
        "update_timestamp",
    ]


@admin.register(FlatPrice)
class FlatPriceAdmin(admin.ModelAdmin):
    list_display = ["price_rub", "price_usd", "flat", "update_timestamp"]


@admin.register(Offer)
class OfferAdmin(GISModelAdmin):
    list_display = ["external_id", "update_timestamp"]

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
