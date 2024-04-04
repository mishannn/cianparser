import uuid
from django.db import models, transaction
from django.core.serializers import serialize
from django.contrib.gis.db import models as geomodels
from cian.geo import get_boxes_by_geojson

# Create your models here.


class Area(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    geometry = geomodels.GeometryCollectionField()
    created_timestamp = models.DateTimeField(
        auto_now_add=True, editable=False, null=False, blank=False
    )
    update_timestamp = models.DateTimeField(
        auto_now=True, editable=False, null=False, blank=False
    )


class Cell(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    geometry = geomodels.PolygonField()
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

    @staticmethod
    @transaction.atomic
    def create_cells_from_area(area, max_tile_size):
        area_geojson = serialize("geojson", [area], geometry_field="geometry")
        boxes = get_boxes_by_geojson(area_geojson, max_tile_size)

        Cell.objects.filter(area=area).delete()

        for num, box in enumerate(boxes, 1):
            Cell.objects.create(name=f"{area.name}-{num}", area=area, geometry=box)
