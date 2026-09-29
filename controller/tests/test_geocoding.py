"""Tests for Geoapify postcode lookup behavior."""

import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.geocoding import (
    GEOAPIFY_ENDPOINT,
    GEOAPIFY_TIMEOUT_SECONDS,
    GeocodingProviderError,
    PostcodeNotFoundError,
    lookup_us_postcode,
)
from app.main import app


class PostcodeLookupTests(unittest.IsolatedAsyncioTestCase):
    def _client(self, response: Mock | None = None) -> AsyncMock:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        if response is not None:
            client.get.return_value = response
        return client

    @patch("app.geocoding.get_geoapify_api_key", return_value="test-key")
    async def test_returns_matching_us_postcode(self, _mock_key: Mock) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "results": [
                {
                    "postcode": "16802",
                    "country_code": "us",
                    "lat": 40.7982,
                    "lon": -77.8599,
                    "city": "University Park",
                }
            ]
        }
        client = self._client(response)

        with patch("app.geocoding.httpx.AsyncClient", return_value=client) as client_type:
            location = await lookup_us_postcode("16802")

        self.assertEqual(location.postcode, "16802")
        self.assertEqual(location.country_code, "US")
        self.assertEqual(location.latitude, 40.7982)
        self.assertEqual(location.longitude, -77.8599)
        self.assertEqual(location.locality, "University Park")
        client_type.assert_called_once_with(timeout=GEOAPIFY_TIMEOUT_SECONDS)
        client.get.assert_awaited_once_with(
            GEOAPIFY_ENDPOINT,
            params={
                "postcode": "16802",
                "type": "postcode",
                "filter": "countrycode:us",
                "format": "json",
                "apiKey": "test-key",
            },
        )

    @patch("app.geocoding.get_geoapify_api_key", return_value="test-key")
    async def test_rejects_mismatched_location(self, _mock_key: Mock) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "results": [
                {
                    "postcode": "90210",
                    "country_code": "us",
                    "lat": 34.0901,
                    "lon": -118.4065,
                }
            ]
        }
        client = self._client(response)

        with patch("app.geocoding.httpx.AsyncClient", return_value=client):
            with self.assertRaises(PostcodeNotFoundError):
                await lookup_us_postcode("16802")

    @patch("app.geocoding.get_geoapify_api_key", return_value="test-key")
    async def test_sanitizes_provider_failure(self, _mock_key: Mock) -> None:
        client = self._client()
        client.get.side_effect = httpx.ConnectError("request failed")

        with patch("app.geocoding.httpx.AsyncClient", return_value=client):
            with self.assertRaisesRegex(
                GeocodingProviderError,
                "^Geoapify request failed\\.$",
            ):
                await lookup_us_postcode("16802")


class PostcodeRouteTests(unittest.IsolatedAsyncioTestCase):
    async def _get_demo(self) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get("/api/demo/zip-location")

    @patch("app.geocoding.lookup_us_postcode", new_callable=AsyncMock)
    async def test_demo_route_returns_location(self, mock_lookup: AsyncMock) -> None:
        mock_lookup.return_value = {
            "postcode": "16802",
            "country_code": "US",
            "latitude": 40.7982,
            "longitude": -77.8599,
            "locality": "University Park",
        }

        response = await self._get_demo()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["postcode"], "16802")
        mock_lookup.assert_awaited_once_with("16802")

    @patch("app.geocoding.lookup_us_postcode", new_callable=AsyncMock)
    async def test_demo_route_reports_unresolved_zip(
        self,
        mock_lookup: AsyncMock,
    ) -> None:
        mock_lookup.side_effect = PostcodeNotFoundError("No matching postcode.")

        response = await self._get_demo()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"]["code"], "postcode_not_found")

    @patch("app.geocoding.lookup_us_postcode", new_callable=AsyncMock)
    async def test_demo_route_sanitizes_provider_failure(
        self,
        mock_lookup: AsyncMock,
    ) -> None:
        mock_lookup.side_effect = GeocodingProviderError("sensitive detail")

        response = await self._get_demo()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {
                "detail": {
                    "code": "geocoding_provider_error",
                    "message": "The location provider is unavailable.",
                }
            },
        )

if __name__ == "__main__":
    unittest.main()
