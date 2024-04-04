from django.db import models
from django.contrib.gis.db import models as geomodels
import uuid

# Create your models here.


class Flat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.IntegerField(unique=True)
    active = models.BooleanField(default=True)
    location = geomodels.PointField()
    address = models.CharField(max_length=256, null=True, blank=True)
    is_newbuilding = models.BooleanField(null=True, blank=True)
    external_url = models.CharField(max_length=256, null=True, blank=True)
    floor_number = models.IntegerField(null=True, blank=True)
    floors_count = models.IntegerField(null=True, blank=True)
    build_year = models.IntegerField(null=True, blank=True)
    total_area = models.FloatField(null=True, blank=True)
    rooms_count = models.IntegerField(null=True, blank=True)
    created_timestamp = models.DateTimeField(
        auto_now_add=True, editable=False, null=False, blank=False
    )
    update_timestamp = models.DateTimeField(
        auto_now=True, editable=False, null=False, blank=False
    )


class FlatPrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE)
    price_rub = models.DecimalField(max_digits=15, decimal_places=6)
    price_usd = models.DecimalField(max_digits=15, decimal_places=6)
    created_timestamp = models.DateTimeField(
        auto_now_add=True, editable=False, null=False, blank=False
    )
    update_timestamp = models.DateTimeField(
        auto_now=True, editable=False, null=False, blank=False
    )


class Offer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.IntegerField(unique=True)
    location = geomodels.PointField()
    flat = models.ForeignKey(Flat, on_delete=models.SET_NULL, null=True, blank=True)
    search_pending = models.BooleanField(default=False)
    last_search_timestamp = models.DateTimeField(null=True, blank=True)
    created_timestamp = models.DateTimeField(
        auto_now_add=True, editable=False, null=False, blank=False
    )
    update_timestamp = models.DateTimeField(
        auto_now=True, editable=False, null=False, blank=False
    )

    def reset_search_pending(self):
        self.search_pending = False
        self.save()

    def reset_last_search_timestamp(self):
        self.last_search_timestamp = None
        self.save()
