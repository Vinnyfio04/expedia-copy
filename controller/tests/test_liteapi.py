"""Tests for LiteAPI normalization, matching, requests, and route fallback."""

from datetime import date, timedelta
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.liteapi import (
    LITEAPI_RATES_ENDPOINT,
    LITEAPI_RESULT_LIMIT,
    LITEAPI_TIMEOUT_SECONDS,
    LiteApiOffer,
    LiteApiProviderError,
    attach_liteapi_rates,
    normalize_liteapi_offers,
    request_liteapi_rates,
)
from app.main import app
from app.models import HotelRateQuote, NearbyHotel, PostcodeLocation


def liteapi_payload() -> dict:
    return {
        "hotels": [
            {
                "id": "lp-example",
                "name": "Example Hotel",
                "address": "1 Main Street",
                "location": {"latitude": 40.801, "longitude": -77.859},
            }
        ],
        "data": [
            {
                "hotelId": "lp-example",
                "roomTypes": [
                    {
                        "rates": [
                            {
                                "retailRate": {
                                    "total": [{"amount": 420, "currency": "usd"}],
                                    "taxesAndFees": [{"included": True}],
                                }
                            }
                        ]
                    }
                ],
            }
        ],
    }


class LiteApiNormalizationTests(unittest.TestCase):
    def test_normalizes_total_into_an_average_nightly_quote(self) -> None:
        offers = normalize_liteapi_offers(liteapi_payload(), nights=2)

        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].hotel_id, "lp-example")
        self.assertEqual(offers[0].quote.stay_total, 420)
        self.assertEqual(offers[0].quote.average_nightly_rate, 210)
        self.assertEqual(offers[0].quote.currency, "USD")
        self.assertTrue(offers[0].quote.taxes_included)

    def test_matches_normalized_name_and_preserves_geoapify_identity(self) -> None:
        hotel = NearbyHotel(
            provider="geoapify",
            provider_place_id="geo-place",
            name="Example-Hotel",
            formatted_address="1 Main Street, University Park, PA",
            latitude=40.8,
            longitude=-77.86,
        )
        rated = attach_liteapi_rates(
            [hotel],
            normalize_liteapi_offers(liteapi_payload(), nights=2),
        )

        self.assertEqual(rated[0].provider_place_id, "geo-place")
        self.assertEqual(rated[0].rate.provider_hotel_id, "lp-example")

    def test_does_not_guess_when_names_do_not_match(self) -> None:
        hotel = NearbyHotel(
            provider="geoapify",
            provider_place_id="geo-place",
            name="Different Hotel",
            latitude=40.8,
            longitude=-77.86,
        )
        rated = attach_liteapi_rates(
            [hotel],
            normalize_liteapi_offers(liteapi_payload(), nights=2),
        )

        self.assertIsNone(rated[0].rate)


class LiteApiRequestTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.liteapi.get_liteapi_api_key", return_value="test-key")
    async def test_sends_server_side_key_and_documented_rate_fields(
        self,
        _mock_key: Mock,
    ) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = liteapi_payload()
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = response
        center = PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.8,
            longitude=-77.86,
        )

        with patch("app.liteapi.httpx.AsyncClient", return_value=client) as client_type:
            offers = await request_liteapi_rates(
                center,
                date(2026, 11, 10),
                date(2026, 11, 12),
                2,
                5000,
            )

        self.assertEqual(len(offers), 1)
        client_type.assert_called_once_with(timeout=LITEAPI_TIMEOUT_SECONDS)
        client.post.assert_awaited_once_with(
            LITEAPI_RATES_ENDPOINT,
            headers={"X-API-Key": "test-key", "Content-Type": "application/json"},
            json={
                "occupancies": [{"adults": 2}],
                "currency": "USD",
                "guestNationality": "US",
                "checkin": "2026-11-10",
                "checkout": "2026-11-12",
                "latitude": 40.8,
                "longitude": -77.86,
                "radius": 5000,
                "limit": LITEAPI_RESULT_LIMIT,
                "maxRatesPerHotel": 1,
                "includeHotelData": True,
            },
        )

    @patch("app.liteapi.get_liteapi_api_key", return_value="test-key")
    async def test_treats_no_content_as_no_availability(
        self,
        _mock_key: Mock,
    ) -> None:
        response = Mock(status_code=204)
        response.raise_for_status.return_value = None
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = response
        center = PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.8,
            longitude=-77.86,
        )

        with patch("app.liteapi.httpx.AsyncClient", return_value=client):
            offers = await request_liteapi_rates(
                center,
                date(2026, 11, 10),
                date(2026, 11, 12),
                2,
                5000,
            )

        self.assertEqual(offers, [])


class RatedNearbyRouteTests(unittest.IsolatedAsyncioTestCase):
    async def _post(self, body: dict) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/api/hotels/nearby/rates", json=body)

    @patch("app.nearby_hotels.request_liteapi_rates", new_callable=AsyncMock)
    @patch("app.nearby_hotels.request_geoapify_hotels", new_callable=AsyncMock)
    @patch("app.nearby_hotels.lookup_us_postcode", new_callable=AsyncMock)
    async def test_returns_geoapify_hotels_when_liteapi_is_unavailable(
        self,
        mock_lookup: AsyncMock,
        mock_places: AsyncMock,
        mock_rates: AsyncMock,
    ) -> None:
        center = PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.8,
            longitude=-77.86,
        )
        mock_lookup.return_value = center
        mock_places.return_value = [
            NearbyHotel(
                provider="geoapify",
                provider_place_id="geo-place",
                name="Example Hotel",
                latitude=40.8,
                longitude=-77.86,
            )
        ]
        mock_rates.side_effect = LiteApiProviderError("sensitive provider error")
        check_in = date.today() + timedelta(days=1)

        response = await self._post(
            {
                "postcode": "16802",
                "check_in": check_in.isoformat(),
                "check_out": (check_in + timedelta(days=2)).isoformat(),
                "adults": 2,
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rates_status"], "provider_unavailable")
        self.assertIsNone(response.json()["results"][0]["rate"])
        self.assertNotIn("sensitive", response.text)

    async def test_rejects_invalid_dates_before_provider_calls(self) -> None:
        response = await self._post(
            {
                "postcode": "16802",
                "check_in": date.today().isoformat(),
                "check_out": date.today().isoformat(),
                "adults": 2,
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "invalid_stay_dates")


if __name__ == "__main__":
    unittest.main()
