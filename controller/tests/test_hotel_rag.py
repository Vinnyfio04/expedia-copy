"""Tests for guarded hotel RAG SQL planning and local retrieval."""

from datetime import date
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.database import (
    HOTEL_RAG_CONTEXT_BYTES_LIMIT,
    HOTEL_RAG_RESULT_LIMIT,
    DatabaseController,
    HotelRagQueryError,
)
from app.hotel_rag import (
    HOTEL_RAG_ANSWER_SYSTEM_INSTRUCTION,
    HOTEL_RAG_MAX_ATTEMPTS,
    HOTEL_RAG_SQL_SYSTEM_INSTRUCTION,
    HotelRagGroundingError,
    HotelRagRetrieval,
    answer_hotel_rag_question,
    derive_hotel_rag_matches,
    retrieve_hotel_rag_records,
)
from app.models import (
    DemoHotelNight,
    HotelRagAnswerDraft,
    HotelRagQueryIntent,
    HotelRagRetrievedRecord,
    HotelRagSqlProposal,
    NearbyHotel,
    PostcodeLocation,
    SaveNearbyHotelRequest,
)


DEMO_DATES = tuple(date(2026, 10, day) for day in range(10, 15))


def evidence_query(where_clause: str = "") -> str:
    return (
        "SELECT "
        "h.hotel_id AS hotel_id, h.name AS name, h.address AS address, "
        "h.latitude AS latitude, h.longitude AS longitude, "
        "l.postcode AS postcode, l.locality AS locality, "
        "l.distance_meters AS distance_meters, n.stay_date AS stay_date, "
        "n.nightly_rate_cents AS nightly_rate_cents, "
        "n.rooms_available AS rooms_available "
        "FROM saved_hotels AS h "
        "LEFT JOIN saved_hotel_locations AS l ON l.hotel_id = h.hotel_id "
        "LEFT JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id "
        f"{where_clause} "
        "ORDER BY h.hotel_id, n.stay_date"
    ).strip()


def proposal(
    sql: str,
    parameters: list[str | int | float | bool | None] | None = None,
) -> HotelRagSqlProposal:
    return HotelRagSqlProposal(
        sql=sql,
        parameters=parameters or [],
        intent=HotelRagQueryIntent(),
    )


class GuardedHotelRagDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "rag.db"
        self.database = DatabaseController(self.database_path, seed_path=None)
        self.database.initialize()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def save_hotel(
        self,
        index: int,
        postcode: str = "16802",
        name: str | None = None,
    ) -> None:
        self.database.save_nearby_hotel(
            SaveNearbyHotelRequest(
                hotel=NearbyHotel(
                    provider="geoapify",
                    provider_place_id=f"geo-place-{index}",
                    name=name or f"Saved Hotel {index}",
                    formatted_address=f"{index} Course Way",
                    latitude=40.80 + index / 1000,
                    longitude=-77.86,
                    distance_meters=float(index * 100),
                ),
                search_location=PostcodeLocation(
                    postcode=postcode,
                    country_code="US",
                    latitude=40.8,
                    longitude=-77.86,
                    locality="University Park",
                ),
            ),
            DEMO_DATES,
        )

    def test_executes_parameterized_evidence_query_on_read_only_connection(self) -> None:
        self.save_hotel(1)
        query = proposal(
            evidence_query(
                "WHERE l.postcode = ? AND n.stay_date >= ? AND n.stay_date < ?"
            ),
            ["16802", "2026-10-10", "2026-10-12"],
        )

        records = self.database.execute_hotel_rag_query(query)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].hotel_id, "geo-place-1")
        self.assertEqual(records[0].postcode, "16802")
        self.assertEqual(records[0].stay_date, date(2026, 10, 10))
        self.assertEqual(records[1].stay_date, date(2026, 10, 11))

    def test_allows_focused_cte_with_approved_aggregate(self) -> None:
        self.save_hotel(1)
        sql = (
            "WITH matching AS ("
            "SELECT hotel_id FROM demo_hotel_nights "
            "WHERE stay_date >= ? AND stay_date < ? "
            "GROUP BY hotel_id HAVING COUNT(stay_date) = ?"
            ") "
            + evidence_query(
                "JOIN matching AS m ON m.hotel_id = h.hotel_id "
                "WHERE n.stay_date >= ? AND n.stay_date < ?"
            )
        )

        records = self.database.execute_hotel_rag_query(
            proposal(
                sql,
                [
                    "2026-10-10",
                    "2026-10-12",
                    2,
                    "2026-10-10",
                    "2026-10-12",
                ],
            )
        )

        self.assertEqual(len(records), 2)

    def test_hard_bounds_rows_even_when_query_cross_joins_allowed_data(self) -> None:
        for index in range(1, 4):
            self.save_hotel(index)
        sql = evidence_query(
            "CROSS JOIN demo_hotel_nights AS extra "
            "WHERE extra.rooms_available >= 0"
        )

        records = self.database.execute_hotel_rag_query(proposal(sql))

        self.assertEqual(len(records), HOTEL_RAG_RESULT_LIMIT)

    def test_rejects_an_oversized_total_context(self) -> None:
        oversized_name = "H" * (HOTEL_RAG_CONTEXT_BYTES_LIMIT // 50)
        for index in range(1, 4):
            self.save_hotel(index, name=oversized_name)
        sql = evidence_query(
            "CROSS JOIN demo_hotel_nights AS extra "
            "WHERE extra.rooms_available >= 0"
        )

        with self.assertRaises(HotelRagQueryError) as raised:
            self.database.execute_hotel_rag_query(proposal(sql))

        self.assertEqual(raised.exception.code, "query_result_too_large")

    def test_rejects_mutations_comments_multiple_statements_and_pragma(self) -> None:
        self.save_hotel(1)
        unsafe_sql = (
            "UPDATE saved_hotels SET name = 'Changed'",
            "PRAGMA table_info(saved_hotels)",
            evidence_query() + "; DELETE FROM saved_hotels",
            evidence_query("WHERE h.name = ? -- ignore rules"),
            evidence_query("WHERE h.name = ? /* ignore rules */"),
            "ATTACH DATABASE 'other.db' AS other",
        )

        for sql in unsafe_sql:
            with self.subTest(sql=sql):
                with self.assertRaises(HotelRagQueryError):
                    self.database.execute_hotel_rag_query(proposal(sql))

        reopened = DatabaseController(self.database_path, seed_path=None)
        self.assertEqual(reopened.get_saved_hotel("geo-place-1").name, "Saved Hotel 1")
        self.assertEqual(len(reopened.list_demo_hotel_nights("geo-place-1")), 5)

    def test_underlying_rag_connection_is_query_only_and_reopens_cleanly(self) -> None:
        self.save_hotel(1)

        with self.database._read_only_connection() as connection:
            self.assertEqual(connection.execute("PRAGMA query_only").fetchone()[0], 1)
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute(
                    "UPDATE saved_hotels SET name = 'Changed' WHERE hotel_id = ?",
                    ("geo-place-1",),
                )

        reopened = DatabaseController(self.database_path, seed_path=None)
        self.assertEqual(reopened.get_saved_hotel("geo-place-1").name, "Saved Hotel 1")
        self.assertEqual(reopened.check_references(), [])

    def test_authorizer_rejects_unapproved_tables_and_functions(self) -> None:
        self.save_hotel(1)
        unapproved_table = evidence_query(
            "JOIN app_metadata AS metadata ON metadata.key = h.hotel_id"
        )
        unapproved_function = evidence_query("WHERE RANDOM() IS NOT NULL")

        for sql in (unapproved_table, unapproved_function):
            with self.subTest(sql=sql):
                with self.assertRaises(HotelRagQueryError) as raised:
                    self.database.execute_hotel_rag_query(proposal(sql))
                self.assertEqual(
                    raised.exception.code,
                    "query_not_allowed_or_invalid",
                )

    def test_rejects_cross_hotel_nightly_relationships(self) -> None:
        self.save_hotel(1)
        self.save_hotel(2)
        self.database.update_demo_hotel_night(
            DemoHotelNight(
                hotel_id="geo-place-2",
                stay_date=date(2026, 10, 10),
                nightly_rate_cents=25_000,
                rooms_available=3,
            )
        )
        sql = (
            "SELECT "
            "h.hotel_id AS hotel_id, h.name AS name, h.address AS address, "
            "h.latitude AS latitude, h.longitude AS longitude, "
            "l.postcode AS postcode, l.locality AS locality, "
            "l.distance_meters AS distance_meters, n.stay_date AS stay_date, "
            "n.nightly_rate_cents AS nightly_rate_cents, "
            "n.rooms_available AS rooms_available "
            "FROM saved_hotels AS h "
            "JOIN saved_hotel_locations AS l ON l.hotel_id = h.hotel_id "
            "CROSS JOIN demo_hotel_nights AS n "
            "WHERE h.hotel_id = ? AND n.hotel_id = ?"
        )

        with self.assertRaises(HotelRagQueryError) as raised:
            self.database.execute_hotel_rag_query(
                proposal(sql, ["geo-place-1", "geo-place-2"])
            )

        self.assertEqual(raised.exception.code, "invalid_result_relationships")

    def test_rejects_results_without_the_fixed_evidence_shape(self) -> None:
        self.save_hotel(1)

        with self.assertRaises(HotelRagQueryError) as raised:
            self.database.execute_hotel_rag_query(
                proposal("SELECT hotel_id FROM saved_hotels")
            )

        self.assertEqual(raised.exception.code, "invalid_result_shape")


class HotelRagPlanningTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.invalid_proposal = proposal("UPDATE saved_hotels SET name = ?", ["x"])
        self.valid_proposal = proposal(evidence_query())
        self.record = HotelRagRetrievedRecord(
            hotel_id="geo-place-1",
            name="Saved Hotel 1",
            latitude=40.8,
            longitude=-77.86,
            postcode="16802",
            stay_date=date(2026, 10, 10),
            nightly_rate_cents=10_000,
            rooms_available=20,
        )

    def test_dated_query_rules_preserve_saved_hotel_identity(self) -> None:
        self.assertIn(
            "preserve every otherwise-matching saved hotel",
            HOTEL_RAG_SQL_SYSTEM_INSTRUCTION,
        )
        self.assertIn(
            "LEFT JOIN demo_hotel_nights",
            HOTEL_RAG_SQL_SYSTEM_INSTRUCTION,
        )
        self.assertIn(
            "Return null nightly fields",
            HOTEL_RAG_SQL_SYSTEM_INSTRUCTION,
        )

    async def test_retries_one_rejected_proposal_with_safe_feedback(self) -> None:
        database = Mock(spec=DatabaseController)
        database.execute_hotel_rag_query.side_effect = [
            HotelRagQueryError(
                "internal validation detail",
                code="query_not_read_only",
            ),
            [self.record],
        ]
        model_request = AsyncMock(
            side_effect=[self.invalid_proposal, self.valid_proposal]
        )

        with patch(
            "app.hotel_rag.request_gemini_structured_output",
            model_request,
        ):
            retrieval = await retrieve_hotel_rag_records(
                "Show saved hotels.",
                database=database,
            )

        self.assertEqual(retrieval.proposal, self.valid_proposal)
        self.assertEqual(retrieval.records, [self.record])
        self.assertEqual(model_request.await_count, 2)
        second_prompt = model_request.await_args_list[1].args[0]
        self.assertIn("query_not_read_only", second_prompt)
        self.assertNotIn("internal validation detail", second_prompt)
        self.assertEqual(
            model_request.await_args_list[0].kwargs["system_instruction"],
            HOTEL_RAG_SQL_SYSTEM_INSTRUCTION,
        )

    async def test_stops_after_one_repair_attempt(self) -> None:
        database = Mock(spec=DatabaseController)
        database.execute_hotel_rag_query.side_effect = HotelRagQueryError(
            "rejected",
            code="invalid_result_shape",
        )
        model_request = AsyncMock(return_value=self.invalid_proposal)

        with patch(
            "app.hotel_rag.request_gemini_structured_output",
            model_request,
        ):
            with self.assertRaises(HotelRagQueryError):
                await retrieve_hotel_rag_records(
                    "Show saved hotels.",
                    database=database,
                )

        self.assertEqual(model_request.await_count, HOTEL_RAG_MAX_ATTEMPTS)


def retrieved_record(
    stay_date: date,
    nightly_rate_cents: int,
    rooms_available: int,
    *,
    postcode: str = "16802",
    locality: str = "University Park",
    distance_meters: float = 500.0,
) -> HotelRagRetrievedRecord:
    return HotelRagRetrievedRecord(
        hotel_id="geo-place-1",
        name="Saved Hotel 1",
        address="1 Course Way",
        latitude=40.8,
        longitude=-77.86,
        postcode=postcode,
        locality=locality,
        distance_meters=distance_meters,
        stay_date=stay_date,
        nightly_rate_cents=nightly_rate_cents,
        rooms_available=rooms_available,
    )


class HotelRagGroundingTests(unittest.IsolatedAsyncioTestCase):
    def stay_intent(self) -> HotelRagQueryIntent:
        return HotelRagQueryIntent(
            check_in=date(2026, 10, 10),
            check_out=date(2026, 10, 12),
            requires_availability=True,
        )

    def test_derives_checkout_exclusive_total_and_availability(self) -> None:
        records = [
            retrieved_record(date(2026, 10, 10), 10_000, 4),
            retrieved_record(date(2026, 10, 11), 12_000, 2),
            retrieved_record(date(2026, 10, 12), 99_000, 0),
        ]

        match = derive_hotel_rag_matches(records, self.stay_intent())[0]

        self.assertEqual(
            [night.stay_date for night in match.nights],
            [date(2026, 10, 10), date(2026, 10, 11)],
        )
        self.assertEqual(match.total_cost_cents, 22_000)
        self.assertTrue(match.stay_complete)
        self.assertTrue(match.available_for_entire_stay)

    def test_missing_night_never_becomes_available_or_gets_total(self) -> None:
        match = derive_hotel_rag_matches(
            [retrieved_record(date(2026, 10, 10), 10_000, 20)],
            self.stay_intent(),
        )[0]

        self.assertFalse(match.stay_complete)
        self.assertFalse(match.available_for_entire_stay)
        self.assertEqual(match.missing_nights, [date(2026, 10, 11)])
        self.assertIsNone(match.total_cost_cents)

    def test_zero_room_night_makes_complete_stay_unavailable(self) -> None:
        match = derive_hotel_rag_matches(
            [
                retrieved_record(date(2026, 10, 10), 10_000, 20),
                retrieved_record(date(2026, 10, 11), 10_000, 0),
            ],
            self.stay_intent(),
        )[0]

        self.assertTrue(match.stay_complete)
        self.assertFalse(match.available_for_entire_stay)
        self.assertEqual(match.total_cost_cents, 20_000)

    def test_deduplicates_nights_and_preserves_distinct_zip_context(self) -> None:
        stay_date = date(2026, 10, 10)
        matches = derive_hotel_rag_matches(
            [
                retrieved_record(stay_date, 10_000, 20),
                retrieved_record(
                    stay_date,
                    10_000,
                    20,
                    postcode="16801",
                    locality="State College",
                    distance_meters=250.0,
                ),
            ],
            HotelRagQueryIntent(),
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(len(matches[0].nights), 1)
        self.assertEqual(matches[0].postcodes, ["16801", "16802"])
        self.assertEqual(matches[0].distance_meters, 250.0)

    async def test_second_request_receives_question_records_and_derived_facts(
        self,
    ) -> None:
        intent = self.stay_intent()
        records = [
            retrieved_record(date(2026, 10, 10), 10_000, 20),
            retrieved_record(date(2026, 10, 11), 12_000, 5),
        ]
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=intent,
            ),
            records=records,
        )
        model_request = AsyncMock(
            return_value=HotelRagAnswerDraft(
                status="answered",
                answer=(
                    "Saved Hotel 1 has both simulated course-data nights and "
                    "costs $220 total."
                ),
                cited_hotel_ids=["geo-place-1"],
                claims=[
                    '{"hotel_id":"geo-place-1","missing_nights":[],'
                    '"stay_complete":true,"available_for_entire_stay":true,'
                    '"total_cost_cents":22000}'
                ],
            )
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                model_request,
            ),
        ):
            response = await answer_hotel_rag_question(
                "Where can I stay October 10 through October 12?"
            )

        self.assertEqual(response.status, "answered")
        self.assertEqual(response.matches[0].total_cost_cents, 22_000)
        prompt = model_request.await_args.args[0]
        self.assertIn("Where can I stay", prompt)
        self.assertIn("retrieved_records", prompt)
        self.assertIn("total_cost_cents", prompt)
        self.assertIn("22000", prompt)
        self.assertEqual(
            model_request.await_args.kwargs["system_instruction"],
            HOTEL_RAG_ANSWER_SYSTEM_INSTRUCTION,
        )

    async def test_empty_out_of_range_retrieval_reports_insufficient_data(self) -> None:
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=HotelRagQueryIntent(
                    check_in=date(2026, 11, 1),
                    check_out=date(2026, 11, 3),
                    requires_availability=True,
                ),
            ),
            records=[],
        )
        model_request = AsyncMock(
            return_value=HotelRagAnswerDraft(
                status="insufficient_data",
                answer="There is insufficient simulated course data for those dates.",
                cited_hotel_ids=[],
                claims=[],
            )
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                model_request,
            ),
        ):
            response = await answer_hotel_rag_question("What is available in November?")

        self.assertEqual(response.status, "insufficient_data")
        self.assertEqual(response.matches, [])
        self.assertTrue(
            response.answer.startswith(
                "The requested stay does not have sufficient saved nightly data."
            )
        )

    async def test_empty_in_range_retrieval_reports_no_saved_matches(self) -> None:
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=self.stay_intent(),
            ),
            records=[],
        )
        model_request = AsyncMock(
            return_value=HotelRagAnswerDraft(
                status="no_matches",
                answer="There is insufficient data for that hotel.",
                cited_hotel_ids=[],
                claims=[],
            )
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                model_request,
            ),
        ):
            response = await answer_hotel_rag_question(
                "Is an unsaved hotel available October 10 through October 12?"
            )

        self.assertEqual(response.status, "no_matches")
        self.assertEqual(response.matches, [])
        self.assertTrue(
            response.answer.startswith(
                "No locally saved hotels match this request."
            )
        )
        self.assertIn('"status":"no_matches"', model_request.await_args.args[0])
        self.assertIn(
            '"required_conclusion":"No locally saved hotels match this request.',
            model_request.await_args.args[0],
        )

    async def test_saved_hotel_with_no_requested_nights_is_insufficient(self) -> None:
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=self.stay_intent(),
            ),
            records=[
                HotelRagRetrievedRecord(
                    hotel_id="geo-place-1",
                    name="Saved Hotel 1",
                    address="1 Course Way",
                    latitude=40.8,
                    longitude=-77.86,
                    postcode="16802",
                    locality="University Park",
                    distance_meters=500,
                )
            ],
        )
        model_request = AsyncMock(
            return_value=HotelRagAnswerDraft(
                status="insufficient_data",
                answer=(
                    "Saved Hotel 1 is saved locally, but it has insufficient "
                    "nightly data for the requested stay."
                ),
                cited_hotel_ids=["geo-place-1"],
                claims=[
                    '{"hotel_id":"geo-place-1",'
                    '"missing_nights":["2026-10-10","2026-10-11"],'
                    '"stay_complete":false,'
                    '"available_for_entire_stay":false,'
                    '"total_cost_cents":null}'
                ],
            )
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                model_request,
            ),
        ):
            response = await answer_hotel_rag_question(
                "Can I stay at Saved Hotel 1 October 10 through October 12?"
            )

        self.assertEqual(response.status, "insufficient_data")
        self.assertEqual(len(response.matches), 1)
        match = response.matches[0]
        self.assertFalse(match.stay_complete)
        self.assertFalse(match.available_for_entire_stay)
        self.assertEqual(
            match.missing_nights,
            [date(2026, 10, 10), date(2026, 10, 11)],
        )
        self.assertIsNone(match.total_cost_cents)
        self.assertIn("is saved locally", response.answer)
        self.assertIn("insufficient nightly data", response.answer)
        self.assertIn(
            '"status":"insufficient_data"',
            model_request.await_args.args[0],
        )

    async def test_rejects_answer_that_changes_verified_status(self) -> None:
        intent = self.stay_intent()
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=intent,
            ),
            records=[
                retrieved_record(date(2026, 10, 10), 10_000, 20),
                retrieved_record(date(2026, 10, 11), 10_000, 20),
            ],
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                new=AsyncMock(
                    return_value=HotelRagAnswerDraft(
                        status="no_matches",
                        answer="No saved hotels matched.",
                        cited_hotel_ids=[],
                        claims=[],
                    )
                ),
            ),
        ):
            with self.assertRaises(HotelRagGroundingError) as raised:
                await answer_hotel_rag_question(
                    "Which saved hotel is available October 10 through October 12?"
                )

        self.assertEqual(raised.exception.code, "invalid_grounded_status")

    async def test_rejects_answer_that_changes_verified_stay_facts(self) -> None:
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=self.stay_intent(),
            ),
            records=[
                retrieved_record(date(2026, 10, 10), 10_000, 20),
                retrieved_record(date(2026, 10, 11), 12_000, 5),
            ],
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                new=AsyncMock(
                    return_value=HotelRagAnswerDraft(
                        status="answered",
                        answer="Saved Hotel 1 costs $999 total.",
                        cited_hotel_ids=["geo-place-1"],
                        claims=[
                            '{"hotel_id":"geo-place-1","missing_nights":[],'
                            '"stay_complete":true,'
                            '"available_for_entire_stay":true,'
                            '"total_cost_cents":99900}'
                        ],
                    )
                ),
            ),
        ):
            with self.assertRaises(HotelRagGroundingError) as raised:
                await answer_hotel_rag_question(
                    "Which saved hotel is available October 10 through October 12?"
                )

        self.assertEqual(raised.exception.code, "invalid_grounded_claims")

    async def test_rejects_answer_that_cites_an_unretrieved_hotel(self) -> None:
        retrieval = HotelRagRetrieval(
            proposal=HotelRagSqlProposal(
                sql=evidence_query(),
                intent=HotelRagQueryIntent(),
            ),
            records=[retrieved_record(date(2026, 10, 10), 10_000, 20)],
        )

        with (
            patch(
                "app.hotel_rag.retrieve_hotel_rag_records",
                new=AsyncMock(return_value=retrieval),
            ),
            patch(
                "app.hotel_rag.request_gemini_structured_output",
                new=AsyncMock(
                    return_value=HotelRagAnswerDraft(
                        status="answered",
                        answer="An unrelated hotel is best.",
                        cited_hotel_ids=["not-retrieved"],
                        claims=[
                            '{"hotel_id":"not-retrieved","missing_nights":[],'
                            '"stay_complete":null,'
                            '"available_for_entire_stay":null,'
                            '"total_cost_cents":null}'
                        ],
                    )
                ),
            ),
        ):
            with self.assertRaises(HotelRagGroundingError):
                await answer_hotel_rag_question("Which hotel is best?")


if __name__ == "__main__":
    unittest.main()
