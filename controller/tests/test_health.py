"""Tests for backend configuration and health reporting."""

import os
import unittest
from unittest.mock import patch

import httpx

from app.config import (
    DEFAULT_GEMINI_MODEL,
    get_gemini_model,
    is_gemini_key_configured,
    is_geoapify_key_configured,
    is_liteapi_key_configured,
)
from app.main import app


class ConfigurationTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_absent_key_is_not_configured(self) -> None:
        self.assertFalse(is_geoapify_key_configured())

    @patch.dict(os.environ, {"GEOAPIFY_API_KEY": ""})
    def test_empty_key_is_not_configured(self) -> None:
        self.assertFalse(is_geoapify_key_configured())

    @patch.dict(os.environ, {"GEOAPIFY_API_KEY": "   "})
    def test_whitespace_only_key_is_not_configured(self) -> None:
        self.assertFalse(is_geoapify_key_configured())

    @patch.dict(os.environ, {"GEOAPIFY_API_KEY": "configured-for-test"})
    def test_nonblank_key_is_configured(self) -> None:
        self.assertTrue(is_geoapify_key_configured())

    @patch.dict(os.environ, {"LITEAPI_API_KEY": "   "})
    def test_blank_liteapi_key_is_not_configured(self) -> None:
        self.assertFalse(is_liteapi_key_configured())

    @patch.dict(os.environ, {"LITEAPI_API_KEY": "configured-for-test"})
    def test_nonblank_liteapi_key_is_configured(self) -> None:
        self.assertTrue(is_liteapi_key_configured())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "   "})
    def test_blank_gemini_key_is_not_configured(self) -> None:
        self.assertFalse(is_gemini_key_configured())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "configured-for-test"})
    def test_nonblank_gemini_key_is_configured(self) -> None:
        self.assertTrue(is_gemini_key_configured())

    @patch.dict(os.environ, {"GEMINI_MODEL": "   "})
    def test_blank_gemini_model_uses_stable_flash_default(self) -> None:
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-3.1-flash-lite")
        self.assertEqual(get_gemini_model(), DEFAULT_GEMINI_MODEL)

    @patch.dict(os.environ, {"GEMINI_MODEL": "gemini-test-model"})
    def test_configured_gemini_model_is_preserved(self) -> None:
        self.assertEqual(get_gemini_model(), "gemini-test-model")


class HealthCheckTests(unittest.IsolatedAsyncioTestCase):
    @patch.dict(
        os.environ,
        {
            "GEOAPIFY_API_KEY": "   ",
            "LITEAPI_API_KEY": "   ",
            "GEMINI_API_KEY": "   ",
        },
    )
    async def test_health_preserves_status_and_reports_configuration(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "geoapify_api_key": "key is not configured",
                "liteapi_api_key": "key is not configured",
                "gemini_api_key": "key is not configured",
            },
        )

    @patch.dict(
        os.environ,
        {
            "GEOAPIFY_API_KEY": "configured-for-test",
            "LITEAPI_API_KEY": "configured-for-test",
            "GEMINI_API_KEY": "configured-for-test",
        },
    )
    async def test_health_reports_configured_without_returning_value(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "geoapify_api_key": "key is configured",
                "liteapi_api_key": "key is configured",
                "gemini_api_key": "key is configured",
            },
        )


if __name__ == "__main__":
    unittest.main()
