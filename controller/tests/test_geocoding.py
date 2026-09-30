"""Tests for Geoapify postcode lookup behavior."""

import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.geocoding import (
    GEOAPIFY_ENDPOINT,
    GEOAPIFY_TIMEOUT_SECONDS,
    PROVIDER_RATE_LIMITED,
    GeocodingProviderError,
    PostcodeNotFoundError,
    lookup_us_postcode,
)
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
    async def test_preserves_a_leading_zero_postcode(self, _mock_key: Mock) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "results": [
                {
                    "postcode": "02108",
                    "country_code": "us",
                    "lat": 42.357,
                    "lon": -71.0637,
                }
            ]
        }
        client = self._client(response)

        with patch("app.geocoding.httpx.AsyncClient", return_value=client):
            location = await lookup_us_postcode("02108")

        self.assertEqual(location.postcode, "02108")

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

    @patch("app.geocoding.get_geoapify_api_key", return_value="test-key")
    async def test_preserves_provider_rate_limit_code(self, _mock_key: Mock) -> None:
        request = httpx.Request("GET", GEOAPIFY_ENDPOINT)
        provider_response = httpx.Response(429, request=request)
        response = Mock()
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "rate limited",
            request=request,
            response=provider_response,
        )
        client = self._client(response)

        with patch("app.geocoding.httpx.AsyncClient", return_value=client):
            with self.assertRaises(GeocodingProviderError) as raised:
                await lookup_us_postcode("16802")

        self.assertEqual(raised.exception.code, PROVIDER_RATE_LIMITED)
if __name__ == "__main__":
    unittest.main()
