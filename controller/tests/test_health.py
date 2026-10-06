"""Tests for backend configuration and health reporting."""

import os
import unittest
from unittest.mock import patch

import httpx

from app.config import is_geoapify_key_configured, is_liteapi_key_configured
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


class HealthCheckTests(unittest.IsolatedAsyncioTestCase):
    @patch.dict(
        os.environ,
        {"GEOAPIFY_API_KEY": "   ", "LITEAPI_API_KEY": "   "},
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
            },
        )

    @patch.dict(
        os.environ,
        {
            "GEOAPIFY_API_KEY": "configured-for-test",
            "LITEAPI_API_KEY": "configured-for-test",
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
            },
        )


if __name__ == "__main__":
    unittest.main()
