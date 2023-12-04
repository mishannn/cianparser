import requests
import logging
from concurrent.futures import ThreadPoolExecutor

import cian.geo
import cian.helpers


class CianError(Exception):
    """Error while processing request"""


class Parser:
    def __init__(
        self,
        geojson,
        query,
        max_tile_size,
        max_workers_collect_ids,
        max_workers_collect_offers,
        headers,
    ):
        self.geojson = geojson
        self.query = query
        self.max_tile_size = max_tile_size
        self.max_workers_collect_ids = max_workers_collect_ids
        self.max_workers_collect_offers = max_workers_collect_offers
        self.headers = headers

    def _get_clusters_raw(self, bbox, index, total):
        logging.info("Get clusters for bbox %d of %d" % (index + 1, total))

        request_body = {
            "zoom": 15,
            "bbox": [bbox],
            "jsonQuery": self.query,
        }

        response = requests.post(
            url="https://api.cian.ru/search-offers-index-map/v1/get-clusters-for-map/",
            json=request_body,
            headers=self.headers,
        )

        if response.status_code != 200:
            raise CianError(response.text)

        try:
            response_body = response.json()
        except requests.exceptions.JSONDecodeError:
            raise CianError(response.text)

        return response_body["filtered"]

    def _get_offers_by_ids_raw(self, ids, index, total):
        logging.info("Get offers for page %d of %d" % (index + 1, total))

        request_body = {
            "cianOfferIds": ids,
            "jsonQuery": self.query,
        }

        response = requests.post(
            url="https://api.cian.ru/search-offers/v1/get-offers-by-ids-desktop/",
            json=request_body,
            headers=self.headers,
        )

        if response.status_code != 200:
            raise CianError(response.text)

        try:
            response_body = response.json()
        except requests.exceptions.JSONDecodeError:
            raise CianError(response.text)

        return response_body["offersSerialized"]

    def get_offer_ids(self):
        logging.info("Get bboxes by geojson")
        bboxes = cian.geo.get_cian_bboxes_for_geojson(self.geojson, self.max_tile_size)

        thread_args = []
        for index, bbox in enumerate(bboxes):
            thread_args.append((bbox, index, len(bboxes)))

        clusters = []
        logging.info(
            "Start %d workers for getting clusters by bbox"
            % self.max_workers_collect_ids
        )
        with ThreadPoolExecutor(max_workers=self.max_workers_collect_ids) as pool:
            clusters = cian.helpers.flatten(
                pool.map(lambda args: self._get_clusters_raw(*args), thread_args)
            )

        logging.info("Collect offer ids")
        offer_ids = []
        for cluster in clusters:
            offer_ids = [*offer_ids, *cluster["clusterOfferIds"]]

        logging.info("Remove duplicated offer ids")
        unique_offer_ids = list(set(offer_ids))

        return unique_offer_ids

    def get_offers_by_ids(self, ids):
        offers = []

        logging.info("Split ids on chunks")
        ids_chunks = list(cian.helpers.chunks(ids, 28))

        thread_args = []
        for index, chunk in enumerate(ids_chunks):
            thread_args.append((chunk, index, len(ids_chunks)))

        logging.info(
            "Start %d workers for getting offers by ids"
            % self.max_workers_collect_offers
        )
        with ThreadPoolExecutor(max_workers=self.max_workers_collect_offers) as pool:
            offers = cian.helpers.flatten(
                pool.map(lambda args: self._get_offers_by_ids_raw(*args), thread_args)
            )

        return offers

    def parse(self):
        logging.info("Collect offer ids")
        offer_ids = self.get_offer_ids()
        logging.info("Collected %d offer ids" % len(offer_ids))

        logging.info("Collect offers")
        offers = self.get_offers_by_ids(offer_ids)
        logging.info("Collected %d offers" % len(offers))

        return offers
