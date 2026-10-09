"""Application configuration loaded from the project-root environment file."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

load_dotenv(dotenv_path=ENV_FILE)


def get_geoapify_api_key() -> str | None:
    """Return the configured Geoapify API key, or None when it is blank."""
    api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    return api_key or None


def is_geoapify_key_configured() -> bool:
    """Return whether a nonblank Geoapify API key is configured."""
    return get_geoapify_api_key() is not None


def get_liteapi_api_key() -> str | None:
    """Return the configured LiteAPI key, or None when it is blank."""
    api_key = os.getenv("LITEAPI_API_KEY", "").strip()
    return api_key or None


def is_liteapi_key_configured() -> bool:
    """Return whether a nonblank LiteAPI key is configured."""
    return get_liteapi_api_key() is not None


def get_gemini_api_key() -> str | None:
    """Return the configured Gemini API key, or None when it is blank."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return api_key or None


def is_gemini_key_configured() -> bool:
    """Return whether a nonblank Gemini API key is configured."""
    return get_gemini_api_key() is not None


def get_gemini_model() -> str:
    """Return the configured Gemini model or the stable Flash default."""
    model = os.getenv("GEMINI_MODEL", "").strip()
    return model or DEFAULT_GEMINI_MODEL
