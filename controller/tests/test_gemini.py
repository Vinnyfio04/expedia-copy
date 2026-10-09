"""Tests for backend-only Gemini structured-output requests."""

from datetime import date
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.gemini import (
    GEMINI_INTERACTIONS_ENDPOINT,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_TIMEOUT_SECONDS,
    GeminiProviderError,
    request_gemini_structured_output,
)
from app.models import HotelRagAnswerDraft, HotelRagSqlProposal


def interaction_response(output_text: str) -> httpx.Response:
    return httpx.Response(
        200,
        request=httpx.Request("POST", GEMINI_INTERACTIONS_ENDPOINT),
        json={
            "status": "completed",
            "steps": [
                {
                    "type": "model_output",
                    "content": [{"type": "text", "text": output_text}],
                }
            ],
        },
    )


class GeminiRequestTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.gemini.get_gemini_model", return_value="gemini-3.8-flash")
    @patch("app.gemini.get_gemini_api_key", return_value="secret-test-key")
    async def test_requests_stateless_structured_output_and_validates_it(
        self,
        _mock_key: Mock,
        _mock_model: Mock,
    ) -> None:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = interaction_response(
            """{
                "sql": "SELECT hotel_id FROM saved_hotels WHERE hotel_id = ?",
                "parameters": ["geo-place-1"],
                "intent": {
                    "postcode": "16802",
                    "check_in": "2026-10-10",
                    "check_out": "2026-10-12",
                    "requires_availability": true
                }
            }"""
        )

        with patch("app.gemini.httpx.AsyncClient", return_value=client) as client_type:
            proposal = await request_gemini_structured_output(
                "Create a safe query.",
                HotelRagSqlProposal,
                system_instruction="Return only grounded SQL planning data.",
            )

        self.assertEqual(proposal.intent.check_in, date(2026, 10, 10))
        client_type.assert_called_once_with(timeout=GEMINI_TIMEOUT_SECONDS)
        request = client.post.await_args
        self.assertEqual(request.args[0], GEMINI_INTERACTIONS_ENDPOINT)
        self.assertEqual(request.kwargs["headers"]["x-goog-api-key"], "secret-test-key")
        self.assertNotIn("secret-test-key", request.args[0])
        self.assertNotIn("secret-test-key", str(request.kwargs["json"]))
        self.assertEqual(request.kwargs["json"]["model"], "gemini-3.8-flash")
        self.assertFalse(request.kwargs["json"]["store"])
        self.assertFalse(request.kwargs["json"]["background"])
        self.assertEqual(
            request.kwargs["json"]["response_format"][0]["mime_type"],
            "application/json",
        )
        self.assertEqual(
            request.kwargs["json"]["generation_config"]["max_output_tokens"],
            GEMINI_MAX_OUTPUT_TOKENS,
        )
        self.assertEqual(
            request.kwargs["json"]["generation_config"]["thinking_level"],
            "minimal",
        )

    @patch("app.gemini.get_gemini_api_key", return_value="secret-test-key")
    async def test_parses_grounded_answer_contract(self, _mock_key: Mock) -> None:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = interaction_response(
            json.dumps(
                {
                    "status": "answered",
                    "answer": "The saved records support this hotel.",
                    "cited_hotel_ids": ["geo-place-1"],
                    "claims": [
                        json.dumps(
                            {
                                "hotel_id": "geo-place-1",
                                "missing_nights": [],
                                "stay_complete": True,
                                "available_for_entire_stay": True,
                                "total_cost_cents": 20_000,
                            },
                            separators=(",", ":"),
                        )
                    ],
                }
            )
        )

        with patch("app.gemini.httpx.AsyncClient", return_value=client):
            answer = await request_gemini_structured_output(
                "Explain these retrieved records.",
                HotelRagAnswerDraft,
            )

        self.assertEqual(answer.status, "answered")
        self.assertEqual(answer.cited_hotel_ids, ["geo-place-1"])
        self.assertIn('"total_cost_cents":20000', answer.claims[0])

    @patch("app.gemini.get_gemini_api_key", return_value=None)
    async def test_missing_key_fails_before_network_access(self, _mock_key: Mock) -> None:
        with patch("app.gemini.httpx.AsyncClient") as client_type:
            with self.assertRaises(GeminiProviderError) as raised:
                await request_gemini_structured_output(
                    "Create a safe query.",
                    HotelRagSqlProposal,
                )

        self.assertEqual(raised.exception.code, "not_configured")
        client_type.assert_not_called()

    @patch("app.gemini.get_gemini_api_key", return_value="secret-test-key")
    async def test_rate_limit_is_preserved_without_response_details(
        self,
        _mock_key: Mock,
    ) -> None:
        response = httpx.Response(
            429,
            request=httpx.Request("POST", GEMINI_INTERACTIONS_ENDPOINT),
            text="sensitive provider details",
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = response

        with patch("app.gemini.httpx.AsyncClient", return_value=client):
            with self.assertRaises(GeminiProviderError) as raised:
                await request_gemini_structured_output(
                    "Create a safe query.",
                    HotelRagSqlProposal,
                )

        self.assertEqual(raised.exception.code, "provider_rate_limited")
        self.assertNotIn("sensitive", str(raised.exception))

    @patch("app.gemini.get_gemini_api_key", return_value="secret-test-key")
    async def test_invalid_json_contract_is_sanitized(self, _mock_key: Mock) -> None:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = interaction_response(
            '{"sql": "DELETE FROM saved_hotels"}'
        )

        with patch("app.gemini.httpx.AsyncClient", return_value=client):
            with self.assertRaises(GeminiProviderError) as raised:
                await request_gemini_structured_output(
                    "Create a safe query.",
                    HotelRagSqlProposal,
                )

        self.assertEqual(raised.exception.code, "invalid_provider_response")
        self.assertNotIn("DELETE", str(raised.exception))

    @patch("app.gemini.get_gemini_api_key", return_value="secret-test-key")
    async def test_connection_failure_is_sanitized(self, _mock_key: Mock) -> None:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.side_effect = httpx.ConnectError("sensitive network detail")

        with patch("app.gemini.httpx.AsyncClient", return_value=client):
            with self.assertRaises(GeminiProviderError) as raised:
                await request_gemini_structured_output(
                    "Create a safe query.",
                    HotelRagSqlProposal,
                )

        self.assertEqual(raised.exception.code, "provider_unavailable")
        self.assertNotIn("sensitive", str(raised.exception))

    async def test_rejects_invalid_local_request_limits(self) -> None:
        with self.assertRaises(ValueError):
            await request_gemini_structured_output("   ", HotelRagSqlProposal)
        with self.assertRaises(ValueError):
            await request_gemini_structured_output(
                "Create a safe query.",
                HotelRagSqlProposal,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS + 1,
            )


if __name__ == "__main__":
    unittest.main()
