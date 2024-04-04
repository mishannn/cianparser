import requests
import shapely


class CianError(Exception):
    """Error while processing request"""


def get_clusters_from_bbox(query, geojson):
    minx, miny, maxx, maxy = shapely.from_geojson(geojson).bounds

    request_body = {
        "zoom": 15,
        "bbox": [
            {
                "topLeft": {"lat": maxy, "lng": minx},
                "bottomRight": {"lat": miny, "lng": maxx},
            }
        ],
        "jsonQuery": query,
    }

    response = requests.post(
        url="https://api.cian.ru/search-offers-index-map/v1/get-clusters-for-map/",
        json=request_body,
    )

    if response.status_code != 200:
        raise CianError(response.text)

    try:
        response_body = response.json()
    except requests.exceptions.JSONDecodeError:
        raise CianError(response.text)

    return response_body["filtered"]


def get_offers_details_by_ids(query, ids):
    request_body = {
        "cianOfferIds": ids,
        "jsonQuery": query,
    }

    response = requests.post(
        url="https://api.cian.ru/search-offers/v1/get-offers-by-ids-desktop/",
        json=request_body,
    )

    if response.status_code != 200:
        raise CianError(response.text)

    try:
        response_body = response.json()
    except requests.exceptions.JSONDecodeError:
        raise CianError(response.text)

    return response_body["offersSerialized"]
