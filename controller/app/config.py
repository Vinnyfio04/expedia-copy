"""Application configuration loaded from the project-root environment file."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


def get_geoapify_api_key() -> str | None:
    """Return the configured Geoapify API key, or None when it is blank."""
    api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    return api_key or None


def is_geoapify_key_configured() -> bool:
    """Return whether a nonblank Geoapify API key is configured."""
    return get_geoapify_api_key() is not None
