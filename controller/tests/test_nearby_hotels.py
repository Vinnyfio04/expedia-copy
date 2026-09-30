"""Tests for the live nearby-hotel response contracts and normalization."""

import math
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from pydantic import ValidationError

from app.geocoding import (
    PROVIDER_RATE_LIMITED,
    PROVIDER_UNAVAILABLE,
    GeocodingProviderError,
    PostcodeNotFoundError,
)
from app.main import app
from app.models import NearbyHotel, NearbyHotelSearchResponse, PostcodeLocation
from app.nearby_hotels import (
    GEOAPIFY_PLACES_ENDPOINT,
    HOTEL_CATEGORY,
    NEARBY_HOTEL_LIMIT,
    NEARBY_RADIUS_METERS,
    normalize_geoapify_hotels,
    request_geoapify_hotels,
)


class NearbyHotelModelTests(unittest.TestCase):
    def test_response_uses_the_external_place_contract(self) -> None:
        hotel = NearbyHotel(
            provider="geoapify",
            provider_place_id=" place-1 ",
            name="Example Hotel",
            formatted_address="1 Example Street",
            latitude=40.8,
            longitude=-77.86,
            distance_meters=125.5,
        )
        response = NearbyHotelSearchResponse(
            requested_postcode="16802",
            center=PostcodeLocation(
                postcode="16802",
                country_code="US",
                latitude=40.8,
                longitude=-77.86,
                locality="University Park",
            ),
            count=1,
            results=[hotel],
        )

        self.assertEqual(hotel.provider_place_id, "place-1")
        self.assertEqual(response.radius_meters, 5000)
        self.assertEqual(response.count, len(response.results))
        self.assertEqual(
            set(hotel.model_dump()),
            {
                "provider",
                "provider_place_id",
                "name",
                "formatted_address",
                "latitude",
                "longitude",
                "distance_meters",
            },
        )

    def test_rejects_blank_provider_place_id(self) -> None:
        with self.assertRaises(ValidationError):
            NearbyHotel(
                provider="geoapify",
                provider_place_id="   ",
                latitude=40.8,
                longitude=-77.86,
            )

    def test_rejects_invalid_coordinates_and_distances(self) -> None:
        invalid_fields = (
            {"latitude": math.inf, "longitude": -77.86},
            {"latitude": 91.0, "longitude": -77.86},
            {"latitude": 40.8, "longitude": math.nan},
            {"latitude": 40.8, "longitude": -181.0},
            {
                "latitude": 40.8,
                "longitude": -77.86,
                "distance_meters": -1,
            },
            {
                "latitude": 40.8,
                "longitude": -77.86,
                "distance_meters": math.inf,
            },
        )

        for fields in invalid_fields:
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                NearbyHotel(
                    provider="geoapify",
                    provider_place_id="place-1",
                    **fields,
                )


class GeoapifyHotelNormalizationTests(unittest.TestCase):
    def test_normalizes_valid_features_and_preserves_provider_order(self) -> None:
        payload = {
            "features": [
                {
                    "properties": {
                        "place_id": " first ",
                        "name": " First Hotel ",
                        "formatted": " 1 Main Street ",
                        "lat": 40.81,
                        "lon": -77.85,
                        "distance": 120,
                    }
                },
                {
                    "properties": {
                        "place_id": "second",
                        "lat": 40.82,
                        "lon": -77.84,
                    }
                },
            ]
        }

        hotels = normalize_geoapify_hotels(payload)

        self.assertEqual(
            [hotel.provider_place_id for hotel in hotels],
            ["first", "second"],
        )
        self.assertEqual(hotels[0].name, "First Hotel")
        self.assertEqual(hotels[0].formatted_address, "1 Main Street")
        self.assertEqual(hotels[0].distance_meters, 120.0)
        self.assertIsNone(hotels[1].name)
        self.assertIsNone(hotels[1].formatted_address)
        self.assertIsNone(hotels[1].distance_meters)

    def test_skips_malformed_features_and_stable_deduplicates(self) -> None:
        payload = {
            "features": [
                None,
                {"properties": None},
                {"properties": {"place_id": "", "lat": 40.8, "lon": -77.8}},
                {"properties": {"place_id": "bad-lat", "lat": True, "lon": -77.8}},
                {"properties": {"place_id": "bad-lon", "lat": 40.8, "lon": 181}},
                {
                    "properties": {
                        "place_id": "kept",
                        "name": "Original",
                        "lat": 40.8,
                        "lon": -77.8,
                        "distance": -5,
                    }
                },
                {
                    "properties": {
                        "place_id": "kept",
                        "name": "Duplicate",
                        "lat": 40.9,
                        "lon": -77.9,
                    }
                },
            ]
        }

        hotels = normalize_geoapify_hotels(payload)

        self.assertEqual(len(hotels), 1)
        self.assertEqual(hotels[0].provider_place_id, "kept")
        self.assertEqual(hotels[0].name, "Original")
        self.assertIsNone(hotels[0].distance_meters)

    def test_accepts_successful_zero_results(self) -> None:
        self.assertEqual(normalize_geoapify_hotels({"features": []}), [])

    def test_rejects_invalid_top_level_provider_response(self) -> None:
        for payload in (None, {}, {"features": None}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                normalize_geoapify_hotels(payload)


class GeoapifyPlacesRequestTests(unittest.IsolatedAsyncioTestCase):
    def _center(self) -> PostcodeLocation:
        return PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.8,
            longitude=-77.86,
            locality="University Park",
        )

    def _client(self, response: Mock | None = None) -> AsyncMock:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        if response is not None:
            client.get.return_value = response
        return client

    @patch("app.nearby_hotels.get_geoapify_api_key", return_value="test-key")
    async def test_uses_required_circle_category_bias_and_limit(
        self,
        _mock_key: Mock,
    ) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "place_id": "place-1",
                        "name": "Example Hotel",
                        "lat": 40.81,
                        "lon": -77.85,
                        "distance": 150,
                    }
                }
            ]
        }
        client = self._client(response)

        with patch("app.nearby_hotels.httpx.AsyncClient", return_value=client):
            hotels = await request_geoapify_hotels(self._center())

        self.assertEqual(len(hotels), 1)
        client.get.assert_awaited_once_with(
            GEOAPIFY_PLACES_ENDPOINT,
            params={
                "categories": HOTEL_CATEGORY,
                "filter": f"circle:-77.86,40.8,{NEARBY_RADIUS_METERS}",
                "bias": "proximity:-77.86,40.8",
                "limit": NEARBY_HOTEL_LIMIT,
                "apiKey": "test-key",
            },
        )

    @patch("app.nearby_hotels.get_geoapify_api_key", return_value="test-key")
    async def test_preserves_places_rate_limit_code(self, _mock_key: Mock) -> None:
        request = httpx.Request("GET", GEOAPIFY_PLACES_ENDPOINT)
        provider_response = httpx.Response(429, request=request)
        response = Mock()
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "sensitive provider detail",
            request=request,
            response=provider_response,
        )
        client = self._client(response)

        with patch("app.nearby_hotels.httpx.AsyncClient", return_value=client):
            with self.assertRaises(GeocodingProviderError) as raised:
                await request_geoapify_hotels(self._center())

        self.assertEqual(raised.exception.code, PROVIDER_RATE_LIMITED)

    @patch("app.nearby_hotels.get_geoapify_api_key", return_value="test-key")
    async def test_collapses_connection_and_invalid_response_failures(
        self,
        _mock_key: Mock,
    ) -> None:
        connection_client = self._client()
        connection_client.get.side_effect = httpx.ConnectError("sensitive detail")

        with patch(
            "app.nearby_hotels.httpx.AsyncClient",
            return_value=connection_client,
        ):
            with self.assertRaises(GeocodingProviderError) as connection_error:
                await request_geoapify_hotels(self._center())

        invalid_response = Mock()
        invalid_response.raise_for_status.return_value = None
        invalid_response.json.return_value = {"unexpected": []}
        invalid_client = self._client(invalid_response)
        with patch(
            "app.nearby_hotels.httpx.AsyncClient",
            return_value=invalid_client,
        ):
            with self.assertRaises(GeocodingProviderError) as response_error:
                await request_geoapify_hotels(self._center())

        self.assertEqual(connection_error.exception.code, PROVIDER_UNAVAILABLE)
        self.assertEqual(response_error.exception.code, PROVIDER_UNAVAILABLE)


class NearbyHotelRouteTests(unittest.IsolatedAsyncioTestCase):
    async def _get(self, query: str = "") -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get(f"/api/hotels/nearby{query}")

    @patch("app.nearby_hotels.request_geoapify_hotels", new_callable=AsyncMock)
    @patch("app.nearby_hotels.lookup_us_postcode", new_callable=AsyncMock)
    async def test_invalid_postcodes_return_400_without_provider_calls(
        self,
        mock_lookup: AsyncMock,
        mock_places: AsyncMock,
    ) -> None:
        for query in ("", "?postcode=1234", "?postcode=12345%20", "?postcode=１２３４５"):
            with self.subTest(query=query):
                response = await self._get(query)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["detail"]["code"],
                    "invalid_postcode",
                )

        mock_lookup.assert_not_awaited()
        mock_places.assert_not_awaited()

    @patch("app.nearby_hotels.request_geoapify_hotels", new_callable=AsyncMock)
    @patch("app.nearby_hotels.lookup_us_postcode", new_callable=AsyncMock)
    async def test_leading_zero_zip_returns_explicit_response_contract(
        self,
        mock_lookup: AsyncMock,
        mock_places: AsyncMock,
    ) -> None:
        center = PostcodeLocation(
            postcode="02108",
            country_code="US",
            latitude=42.357,
            longitude=-71.0637,
            locality="Boston",
        )
        mock_lookup.return_value = center
        mock_places.return_value = [
            NearbyHotel(
                provider="geoapify",
                provider_place_id="place-1",
                name="Example Hotel",
                latitude=42.358,
                longitude=-71.064,
            )
        ]

        response = await self._get("?postcode=02108")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "requested_postcode": "02108",
                "center": {
                    "postcode": "02108",
                    "country_code": "US",
                    "latitude": 42.357,
                    "longitude": -71.0637,
                    "locality": "Boston",
                },
                "radius_meters": 5000,
                "count": 1,
                "results": [
                    {
                        "provider": "geoapify",
                        "provider_place_id": "place-1",
                        "name": "Example Hotel",
                        "formatted_address": None,
                        "latitude": 42.358,
                        "longitude": -71.064,
                        "distance_meters": None,
                    }
                ],
            },
        )
        mock_lookup.assert_awaited_once_with("02108")
        mock_places.assert_awaited_once_with(center)

    @patch("app.nearby_hotels.request_geoapify_hotels", new_callable=AsyncMock)
    @patch("app.nearby_hotels.lookup_us_postcode", new_callable=AsyncMock)
    async def test_unresolved_zip_does_not_request_places(
        self,
        mock_lookup: AsyncMock,
        mock_places: AsyncMock,
    ) -> None:
        mock_lookup.side_effect = PostcodeNotFoundError("No matching postcode.")

        response = await self._get("?postcode=16802")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"]["code"], "postcode_not_found")
        mock_places.assert_not_awaited()

    @patch("app.nearby_hotels.request_geoapify_hotels", new_callable=AsyncMock)
    @patch("app.nearby_hotels.lookup_us_postcode", new_callable=AsyncMock)
    async def test_successful_zero_results_remain_a_success(
        self,
        mock_lookup: AsyncMock,
        mock_places: AsyncMock,
    ) -> None:
        mock_lookup.return_value = PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.8,
            longitude=-77.86,
        )
        mock_places.return_value = []

        response = await self._get("?postcode=16802")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertEqual(response.json()["results"], [])

    @patch("app.nearby_hotels.request_geoapify_hotels", new_callable=AsyncMock)
    @patch("app.nearby_hotels.lookup_us_postcode", new_callable=AsyncMock)
    async def test_provider_failures_are_distinct_and_sanitized(
        self,
        mock_lookup: AsyncMock,
        mock_places: AsyncMock,
    ) -> None:
        mock_lookup.return_value = PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.8,
            longitude=-77.86,
        )
        scenarios = (
            (PROVIDER_RATE_LIMITED, 429, "provider_rate_limited"),
            (PROVIDER_UNAVAILABLE, 502, "provider_unavailable"),
        )

        for code, status_code, response_code in scenarios:
            with self.subTest(code=code):
                mock_places.side_effect = GeocodingProviderError(
                    "sensitive apiKey=secret provider body",
                    code=code,
                )
                response = await self._get("?postcode=16802")
                body = response.json()
                self.assertEqual(response.status_code, status_code)
                self.assertEqual(body["detail"]["code"], response_code)
                self.assertNotIn("secret", response.text)
                self.assertNotIn("apiKey", response.text)


if __name__ == "__main__":
    unittest.main()
