"""Validation tests for the stateless hotel RAG data contracts."""

from datetime import date
import unittest

from pydantic import ValidationError

from app.models import (
    HotelRagAnswerDraft,
    HotelRagMatch,
    HotelRagNightEvidence,
    HotelRagQueryIntent,
    HotelRagQuestionRequest,
    HotelRagResponse,
    HotelRagRetrievedRecord,
    HotelRagSqlProposal,
)


class HotelRagModelTests(unittest.TestCase):
    def test_question_is_trimmed_and_bounded(self) -> None:
        request = HotelRagQuestionRequest(
            question="  Which saved hotel is cheapest?  ",
        )

        self.assertEqual(request.question, "Which saved hotel is cheapest?")
        with self.assertRaises(ValidationError):
            HotelRagQuestionRequest(question="   ")
        with self.assertRaises(ValidationError):
            HotelRagQuestionRequest(question="x" * 1_001)

    def test_sql_proposal_keeps_bound_parameters_and_valid_stay_intent(self) -> None:
        proposal = HotelRagSqlProposal(
            sql="SELECT hotel_id FROM saved_hotels WHERE hotel_id = ?",
            parameters=["geo-place-1"],
            intent=HotelRagQueryIntent(
                postcode="16802",
                check_in=date(2026, 10, 10),
                check_out=date(2026, 10, 12),
                requires_availability=True,
            ),
        )

        self.assertEqual(proposal.parameters, ["geo-place-1"])
        self.assertEqual(proposal.intent.check_out, date(2026, 10, 12))

    def test_query_intent_rejects_partial_or_reversed_stay_dates(self) -> None:
        with self.assertRaises(ValidationError):
            HotelRagQueryIntent(check_in=date(2026, 10, 10))

        with self.assertRaises(ValidationError):
            HotelRagQueryIntent(
                check_in=date(2026, 10, 12),
                check_out=date(2026, 10, 10),
            )

    def test_retrieved_record_can_represent_missing_nightly_data(self) -> None:
        record = HotelRagRetrievedRecord(
            hotel_id="geo-place-1",
            name="Saved Hotel",
            latitude=40.8,
            longitude=-77.86,
        )

        self.assertIsNone(record.stay_date)
        self.assertIsNone(record.nightly_rate_cents)
        self.assertIsNone(record.rooms_available)

    def test_retrieved_record_rejects_partial_related_fields(self) -> None:
        with self.assertRaises(ValidationError):
            HotelRagRetrievedRecord(
                hotel_id="geo-place-1",
                latitude=40.8,
                longitude=-77.86,
                locality="University Park",
            )
        with self.assertRaises(ValidationError):
            HotelRagRetrievedRecord(
                hotel_id="geo-place-1",
                latitude=40.8,
                longitude=-77.86,
                stay_date=date(2026, 10, 10),
                nightly_rate_cents=10_000,
            )

    def test_incomplete_stay_cannot_claim_availability_or_total(self) -> None:
        incomplete_match = {
            "hotel_id": "geo-place-1",
            "latitude": 40.8,
            "longitude": -77.86,
            "missing_nights": [date(2026, 10, 11)],
            "stay_complete": False,
        }

        with self.assertRaises(ValidationError):
            HotelRagMatch(
                **incomplete_match,
                available_for_entire_stay=True,
            )
        with self.assertRaises(ValidationError):
            HotelRagMatch(
                **incomplete_match,
                total_cost_cents=20_000,
            )

    def test_complete_stay_requires_availability_and_total(self) -> None:
        complete_match = {
            "hotel_id": "geo-place-1",
            "latitude": 40.8,
            "longitude": -77.86,
            "stay_complete": True,
        }

        with self.assertRaises(ValidationError):
            HotelRagMatch(**complete_match)
        with self.assertRaises(ValidationError):
            HotelRagMatch(
                **complete_match,
                available_for_entire_stay=True,
            )

    def test_match_rejects_an_invalid_postcode(self) -> None:
        with self.assertRaises(ValidationError):
            HotelRagMatch(
                hotel_id="geo-place-1",
                latitude=40.8,
                longitude=-77.86,
                postcodes=["ABCDE"],
            )

    def test_response_carries_actionable_evidence_and_course_data_notice(self) -> None:
        match = HotelRagMatch(
            hotel_id="geo-place-1",
            name="Saved Hotel",
            address="1 Course Way",
            latitude=40.8,
            longitude=-77.86,
            postcodes=["16802"],
            localities=["University Park"],
            nights=[
                HotelRagNightEvidence(
                    stay_date=date(2026, 10, 10),
                    nightly_rate_cents=10_000,
                    rooms_available=20,
                ),
                HotelRagNightEvidence(
                    stay_date=date(2026, 10, 11),
                    nightly_rate_cents=12_000,
                    rooms_available=5,
                ),
            ],
            stay_complete=True,
            available_for_entire_stay=True,
            total_cost_cents=22_000,
        )
        draft = HotelRagAnswerDraft(
            status="answered",
            answer="Saved Hotel has records for both requested nights.",
            cited_hotel_ids=["geo-place-1"],
            claims=[
                '{"hotel_id":"geo-place-1","missing_nights":[],'
                '"stay_complete":true,"available_for_entire_stay":true,'
                '"total_cost_cents":22000}'
            ],
        )
        response = HotelRagResponse(
            question="Where can I stay from October 10 to October 12?",
            status="answered",
            answer=draft.answer,
            requested_check_in=date(2026, 10, 10),
            requested_check_out=date(2026, 10, 12),
            matches=[match],
        )

        self.assertEqual(response.matches[0].total_cost_cents, 22_000)
        self.assertEqual(
            response.data_notice,
            "Rates and availability are simulated course data.",
        )


if __name__ == "__main__":
    unittest.main()
