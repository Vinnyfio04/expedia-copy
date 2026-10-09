"""Route tests for the stateless saved-hotel RAG endpoint."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.database import HotelRagQueryError, get_database_controller
from app.gemini import GeminiProviderError
from app.hotel_rag import HotelRagGroundingError
from app.main import app
from app.models import (
    HotelRagAnswerDraft,
    HotelRagQueryIntent,
    HotelRagResponse,
    HotelRagSqlProposal,
    NearbyHotel,
    PostcodeLocation,
    SaveNearbyHotelRequest,
)


class HotelChatRouteTests(unittest.IsolatedAsyncioTestCase):
    async def _post(self, body: dict) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.post("/api/hotels/chat", json=body)

    async def test_returns_typed_grounded_response(self) -> None:
        grounded_response = HotelRagResponse(
            question="Which saved hotels are nearby?",
            status="no_matches",
            answer="No saved hotels matched the question.",
            matches=[],
        )
        with patch(
            "app.hotel_rag.answer_hotel_rag_question",
            new=AsyncMock(return_value=grounded_response),
        ) as answer_question:
            response = await self._post(
                {"question": "  Which saved hotels are nearby?  "}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), grounded_response.model_dump(mode="json"))
        answer_question.assert_awaited_once_with("Which saved hotels are nearby?")

    async def test_rejects_invalid_question_before_orchestration(self) -> None:
        with patch(
            "app.hotel_rag.answer_hotel_rag_question",
            new=AsyncMock(),
        ) as answer_question:
            response = await self._post({"question": "   "})

        self.assertEqual(response.status_code, 422)
        answer_question.assert_not_awaited()

    async def test_maps_provider_failures_without_leaking_details(self) -> None:
        scenarios = (
            ("not_configured", 503, "llm_not_configured"),
            ("provider_rate_limited", 429, "llm_rate_limited"),
            ("provider_unavailable", 502, "llm_unavailable"),
            ("invalid_provider_response", 502, "llm_unavailable"),
        )
        for provider_code, status_code, response_code in scenarios:
            with self.subTest(provider_code=provider_code), patch(
                "app.hotel_rag.answer_hotel_rag_question",
                new=AsyncMock(
                    side_effect=GeminiProviderError(
                        "sensitive provider body GEMINI_API_KEY=secret",
                        code=provider_code,
                    )
                ),
            ):
                response = await self._post({"question": "Which hotel is best?"})

            self.assertEqual(response.status_code, status_code)
            self.assertEqual(response.json()["detail"]["code"], response_code)
            self.assertNotIn("secret", response.text)
            self.assertNotIn("GEMINI_API_KEY", response.text)

    async def test_maps_rejected_model_query_to_sanitized_failure(self) -> None:
        with patch(
            "app.hotel_rag.answer_hotel_rag_question",
            new=AsyncMock(
                side_effect=HotelRagQueryError(
                    "sensitive rejected SQL",
                    code="query_not_allowed_or_invalid",
                )
            ),
        ):
            response = await self._post({"question": "Find an available hotel."})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"]["code"],
            "invalid_model_query",
        )
        self.assertNotIn("SQL", response.text)

    async def test_maps_invalid_grounding_to_sanitized_failure(self) -> None:
        with patch(
            "app.hotel_rag.answer_hotel_rag_question",
            new=AsyncMock(
                side_effect=HotelRagGroundingError(
                    "sensitive uncited provider output"
                )
            ),
        ):
            response = await self._post({"question": "Compare saved hotels."})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"]["code"],
            "invalid_grounded_answer",
        )
        self.assertNotIn("uncited", response.text)


class HotelChatEndToEndTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "chat-route.db"
        self.database_path_patcher = patch(
            "app.database.DATABASE_PATH",
            self.database_path,
        )
        self.database_path_patcher.start()
        self.database = get_database_controller()
        self.database.initialize()
        self.database.save_nearby_hotel(
            SaveNearbyHotelRequest(
                hotel=NearbyHotel(
                    provider="geoapify",
                    provider_place_id="saved-hotel-1",
                    name="Course Demo Hotel",
                    formatted_address="1 Learning Lane",
                    latitude=40.801,
                    longitude=-77.859,
                    distance_meters=250,
                ),
                search_location=PostcodeLocation(
                    postcode="16802",
                    country_code="US",
                    latitude=40.8,
                    longitude=-77.86,
                    locality="State College",
                ),
            ),
            tuple(date(2026, 10, day) for day in range(10, 15)),
        )

    def tearDown(self) -> None:
        self.database_path_patcher.stop()
        self.temporary_directory.cleanup()

    async def _post(self, body: dict) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.post("/api/hotels/chat", json=body)

    async def test_full_route_reads_saved_nights_and_returns_grounded_total(
        self,
    ) -> None:
        question = "Which saved hotel is available October 10 through October 12?"
        sql_proposal = HotelRagSqlProposal(
            sql=(
                "SELECT h.hotel_id AS hotel_id, h.name AS name, "
                "h.address AS address, h.latitude AS latitude, "
                "h.longitude AS longitude, l.postcode AS postcode, "
                "l.locality AS locality, l.distance_meters AS distance_meters, "
                "n.stay_date AS stay_date, "
                "n.nightly_rate_cents AS nightly_rate_cents, "
                "n.rooms_available AS rooms_available "
                "FROM saved_hotels AS h "
                "JOIN saved_hotel_locations AS l ON l.hotel_id = h.hotel_id "
                "JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id "
                "WHERE n.stay_date >= ? AND n.stay_date < ? "
                "ORDER BY h.hotel_id, n.stay_date"
            ),
            parameters=["2026-10-10", "2026-10-12"],
            intent=HotelRagQueryIntent(
                check_in=date(2026, 10, 10),
                check_out=date(2026, 10, 12),
                requires_availability=True,
            ),
        )
        answer_draft = HotelRagAnswerDraft(
            status="answered",
            answer=(
                "Course Demo Hotel has complete simulated course data for both "
                "requested nights, 20 rooms each night, and a $200 total."
            ),
            cited_hotel_ids=["saved-hotel-1"],
            claims=[
                '{"hotel_id":"saved-hotel-1","missing_nights":[],'
                '"stay_complete":true,"available_for_entire_stay":true,'
                '"total_cost_cents":20000}'
            ],
        )
        model_outputs = [sql_proposal, answer_draft]

        async def mock_model_request(*_args, **_kwargs):
            return model_outputs.pop(0)

        before = self.database.get_saved_hotel_search("16802")
        with patch(
            "app.hotel_rag.request_gemini_structured_output",
            new=AsyncMock(side_effect=mock_model_request),
        ) as model_request:
            response = await self._post({"question": question})
        after = self.database.get_saved_hotel_search("16802")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "answered")
        self.assertEqual(body["requested_check_in"], "2026-10-10")
        self.assertEqual(body["requested_check_out"], "2026-10-12")
        self.assertEqual(len(body["matches"]), 1)
        match = body["matches"][0]
        self.assertEqual(match["hotel_id"], "saved-hotel-1")
        self.assertEqual(match["total_cost_cents"], 20_000)
        self.assertTrue(match["stay_complete"])
        self.assertTrue(match["available_for_entire_stay"])
        self.assertEqual(
            [night["stay_date"] for night in match["nights"]],
            ["2026-10-10", "2026-10-11"],
        )
        self.assertEqual(body["data_notice"], "Rates and availability are simulated course data.")
        self.assertEqual(model_request.await_count, 2)
        self.assertEqual(before, after)
        self.assertEqual(model_outputs, [])

    async def test_unsaved_seed_hotel_uses_no_provider_and_writes_nothing(
        self,
    ) -> None:
        question = (
            "What is the availability and total cost for Harbor Lantern Hotel "
            "from October 10 through October 12, 2026?"
        )
        sql_proposal = HotelRagSqlProposal(
            sql=(
                "SELECT h.hotel_id AS hotel_id, h.name AS name, "
                "h.address AS address, h.latitude AS latitude, "
                "h.longitude AS longitude, l.postcode AS postcode, "
                "l.locality AS locality, l.distance_meters AS distance_meters, "
                "n.stay_date AS stay_date, "
                "n.nightly_rate_cents AS nightly_rate_cents, "
                "n.rooms_available AS rooms_available "
                "FROM saved_hotels AS h "
                "LEFT JOIN saved_hotel_locations AS l ON l.hotel_id = h.hotel_id "
                "LEFT JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id "
                "WHERE lower(h.name) = lower(?) "
                "AND n.stay_date >= ? AND n.stay_date < ? "
                "ORDER BY h.hotel_id, n.stay_date"
            ),
            parameters=[
                "Harbor Lantern Hotel",
                "2026-10-10",
                "2026-10-12",
            ],
            intent=HotelRagQueryIntent(
                check_in=date(2026, 10, 10),
                check_out=date(2026, 10, 12),
                requires_availability=True,
            ),
        )
        answer_draft = HotelRagAnswerDraft(
            status="no_matches",
            answer=(
                "Harbor Lantern Hotel is not among your locally saved hotels. "
                "Use ZIP search and Add to Local before asking about its "
                "simulated rates or availability."
            ),
            cited_hotel_ids=[],
            claims=[],
        )
        model_outputs = [sql_proposal, answer_draft]

        async def mock_model_request(*_args, **_kwargs):
            return model_outputs.pop(0)

        before_saved = self.database.get_saved_hotel_search("16802")
        before_bookings = self.database.list_bookings()
        with (
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                new=AsyncMock(side_effect=mock_model_request),
            ) as model_request,
            patch(
                "app.nearby_hotels.lookup_us_postcode",
                new=AsyncMock(side_effect=AssertionError("geocoder called")),
            ) as geocoder,
            patch(
                "app.nearby_hotels.request_geoapify_hotels",
                new=AsyncMock(side_effect=AssertionError("Geoapify called")),
            ) as geoapify,
            patch(
                "app.nearby_hotels.request_liteapi_rates",
                new=AsyncMock(side_effect=AssertionError("LiteAPI called")),
            ) as liteapi,
        ):
            response = await self._post({"question": question})

        after_saved = self.database.get_saved_hotel_search("16802")
        after_bookings = self.database.list_bookings()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "no_matches")
        self.assertEqual(body["matches"], [])
        self.assertIn("not among your locally saved hotels", body["answer"])
        self.assertNotIn("No locally saved hotels match this request", body["answer"])
        self.assertEqual(model_request.await_count, 2)
        self.assertIn(
            '"status":"no_matches"',
            model_request.await_args_list[1].args[0],
        )
        geocoder.assert_not_awaited()
        geoapify.assert_not_awaited()
        liteapi.assert_not_awaited()
        self.assertEqual(before_saved, after_saved)
        self.assertEqual(before_bookings, after_bookings)
        self.assertEqual(model_outputs, [])


if __name__ == "__main__":
    unittest.main()
