import datetime
from celery import shared_task
from django.db.models import Q
from django.core.serializers import serialize
from areas.models import Cell
from cian.offers import get_clusters_from_bbox, get_offers_details_by_ids
from django.db import transaction
from django.contrib.gis.geos import Point
from django.core.paginator import Paginator

from flats.models import Flat, FlatPrice, Offer

cian_query = {"_type": "flatsale", "engine_version": {"type": "term", "value": 2}}


@shared_task
def collect_offer_ids_for_all_cells():
    cells = Cell.objects.filter(
        Q(search_pending=False)
        & (
            Q(last_search_timestamp__lte=datetime.datetime.now(datetime.UTC).today())
            | Q(last_search_timestamp__isnull=True)
        ),
    )

    for cell in cells:
        collect_offer_ids_for_cell.delay(cell.id)
        cell.search_pending = True
        cell.save()


@shared_task(rate_limit="10/m")
@transaction.atomic
def collect_offer_ids_for_cell(cell_id):
    cell = Cell.objects.get(id=cell_id)

    geojson = serialize("geojson", [cell], geometry_field="geometry")
    clusters = get_clusters_from_bbox(cian_query, geojson)

    for cluster in clusters:
        location = Point(
            cluster["coordinates"]["lng"], cluster["coordinates"]["lat"], srid=4326
        )

        for offer_id in cluster["clusterOfferIds"]:
            Offer.objects.update_or_create(
                external_id=offer_id, defaults={"location": location}
            )

    cell.search_pending = False
    cell.last_search_timestamp = datetime.datetime.now(datetime.UTC)
    cell.save()


@shared_task
def collect_details_for_all_offers():
    offers = Offer.objects.filter(
        Q(search_pending=False)
        & (
            Q(last_search_timestamp__lte=datetime.datetime.now(datetime.UTC).today())
            | Q(last_search_timestamp__isnull=True)
        ),
    ).order_by("last_search_timestamp")

    paginator = Paginator(offers, 28)

    for page_number in paginator.page_range:
        page = paginator.page(page_number)

        offer_ids = list(page.object_list.values_list("id", flat=True))
        collect_details_for_offers_by_ids.delay(offer_ids)

        Offer.objects.filter(id__in=offer_ids).update(search_pending=True)


@shared_task(rate_limit="5/m")
def collect_details_for_offers_by_ids(offer_ids):
    cian_ids = Offer.objects.filter(id__in=offer_ids).values_list(
        "external_id", flat=True
    )

    offers_details = get_offers_details_by_ids(cian_query, list(cian_ids))
    for offer_details in offers_details:
        flat, created = Flat.objects.update_or_create(
            external_id=offer_details["id"],
            defaults={
                "location": Point(
                    offer_details["geo"]["coordinates"]["lng"],
                    offer_details["geo"]["coordinates"]["lat"],
                    srid=4326,
                ),
                "address": offer_details["geo"]["userInput"],
                "floor_number": offer_details["floorNumber"],
                "is_newbuilding": offer_details["category"] == "newBuildingFlatSale",
                "active": offer_details["status"] == "published",
                "external_url": offer_details["fullUrl"],
                "build_year": offer_details["building"]["buildYear"],
                "floors_count": offer_details["building"]["floorsCount"],
                "total_area": offer_details["totalArea"],
                "rooms_count": offer_details["roomsCount"],
            },
        )
        FlatPrice.objects.create(
            flat=flat,
            price_rub=offer_details["bargainTerms"]["priceRur"],
            price_usd=offer_details["bargainTerms"]["priceUsd"],
        )

    Offer.objects.filter(id__in=offer_ids).update(
        search_pending=False, last_search_timestamp=datetime.datetime.now(datetime.UTC)
    )
