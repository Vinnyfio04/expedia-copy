"""Tests for local saved-hotel routes and transactional persistence."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx

from app.database import get_database_controller
from app.main import app
from app.models import DemoHotelNight


def save_body(
    hotel_id: str = "geo-place-1",
    postcode: str = "16802",
) -> dict:
    return {
        "hotel": {
            "provider": "geoapify",
            "provider_place_id": hotel_id,
            "name": f"Hotel {hotel_id}",
            "formatted_address": "1 College Avenue",
            "latitude": 40.801,
            "longitude": -77.859,
            "distance_meters": 250.0,
        },
        "search_location": {
            "postcode": postcode,
            "country_code": "US",
            "latitude": 40.8,
            "longitude": -77.86,
            "locality": "State College",
        },
    }


class SavedHotelRouteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "saved-api.db"
        self.database_path_patcher = patch(
            "app.database.DATABASE_PATH",
            self.database_path,
        )
        self.database_path_patcher.start()

    def tearDown(self) -> None:
        self.database_path_patcher.stop()
        self.temporary_directory.cleanup()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
    ) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.request(method, path, json=json)

    async def test_save_is_idempotent_and_preserves_existing_demo_values(
        self,
    ) -> None:
        body = save_body()

        first = await self._request("POST", "/api/hotels/saved", json=body)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()["provider_place_id"], "geo-place-1")
        self.assertEqual(
            [night["stay_date"] for night in first.json()["demo_nights"]],
            [f"2026-10-{day:02d}" for day in range(10, 15)],
        )
        self.assertTrue(
            all(
                night["nightly_rate_cents"] == 10_000
                and night["rooms_available"] == 20
                for night in first.json()["demo_nights"]
            )
        )

        database = get_database_controller()
        database.update_demo_hotel_night(
            DemoHotelNight(
                hotel_id="geo-place-1",
                stay_date=date(2026, 10, 10),
                nightly_rate_cents=12_345,
                rooms_available=7,
            )
        )

        second = await self._request("POST", "/api/hotels/saved", json=body)
        local = await self._request(
            "GET",
            "/api/hotels/saved?postcode=16802",
        )

        self.assertEqual(second.status_code, 201)
        self.assertEqual(len(database.list_saved_hotels()), 1)
        self.assertEqual(len(database.list_demo_hotel_nights()), 5)
        self.assertEqual(local.status_code, 200)
        self.assertEqual(local.json()["count"], 1)
        self.assertEqual(local.json()["center"]["postcode"], "16802")
        self.assertEqual(local.json()["saved_hotel_ids"], ["geo-place-1"])
        self.assertEqual(
            local.json()["results"][0]["demo_nights"][0],
            {
                "hotel_id": "geo-place-1",
                "stay_date": "2026-10-10",
                "nightly_rate_cents": 12_345,
                "rooms_available": 7,
            },
        )
        self.assertEqual(database.check_references(), [])

        reopened = get_database_controller()
        reopened.initialize()
        self.assertEqual(len(reopened.list_saved_hotels()), 1)
        self.assertEqual(len(reopened.list_demo_hotel_nights()), 5)

    async def test_empty_zip_result_still_reports_global_saved_ids(self) -> None:
        await self._request("POST", "/api/hotels/saved", json=save_body())

        response = await self._request(
            "GET",
            "/api/hotels/saved?postcode=02108",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertIsNone(response.json()["center"])
        self.assertEqual(response.json()["results"], [])
        self.assertEqual(response.json()["saved_hotel_ids"], ["geo-place-1"])

    async def test_delete_removes_related_rows_and_preserves_other_hotels(
        self,
    ) -> None:
        await self._request("POST", "/api/hotels/saved", json=save_body())
        await self._request(
            "POST",
            "/api/hotels/saved",
            json=save_body("geo-place-2"),
        )

        deleted = await self._request(
            "DELETE",
            "/api/hotels/saved?hotel_id=geo-place-1",
        )
        local = await self._request(
            "GET",
            "/api/hotels/saved?postcode=16802",
        )
        missing = await self._request(
            "DELETE",
            "/api/hotels/saved?hotel_id=geo-place-1",
        )

        database = get_database_controller()
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            deleted.json(),
            {"hotel_id": "geo-place-1", "removed": True},
        )
        self.assertIsNone(database.get_saved_hotel("geo-place-1"))
        self.assertIsNotNone(database.get_saved_hotel("geo-place-2"))
        self.assertEqual(len(database.list_demo_hotel_nights()), 5)
        self.assertEqual(local.json()["count"], 1)
        self.assertEqual(
            local.json()["results"][0]["provider_place_id"],
            "geo-place-2",
        )
        self.assertEqual(database.check_references(), [])
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(
            missing.json()["detail"]["code"],
            "saved_hotel_not_found",
        )

    async def test_rejects_invalid_local_zip_without_provider_access(self) -> None:
        response = await self._request("GET", "/api/hotels/saved?postcode=1234")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "invalid_postcode")


if __name__ == "__main__":
    unittest.main()
