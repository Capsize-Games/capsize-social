"""Runtime settings, read once from the environment.

The base class, the `.env` handling and the per-class cache all come from
`capsize-commons`; this module only declares what is specific to this
service. `get_settings` stays a no-argument function because FastAPI
dependency overrides in the test suite key on it.
"""

from __future__ import annotations

from capsize_commons.config import CapsizeSettings
from capsize_commons.config import get_settings as _cached_settings
from pydantic_settings import SettingsConfigDict


class Settings(CapsizeSettings):
    """All configuration this service reads from the environment."""

    model_config = SettingsConfigDict(
        env_prefix="SOCIAL_", env_file=".env", extra="ignore"
    )

    database_url: str = "sqlite:///./capsize_social.db"

    # Checked against the caller's X-API-Key header on every request.
    # Empty by default so the module can be imported with no environment
    # configured; every request is rejected until this is set.
    api_key: str = ""

    # Fernet key (44-char urlsafe-base64) encrypting stored credentials.
    # Empty by default; encrypting/decrypting with an empty key fails
    # loudly at first use instead of at import time. Generate with:
    #   python -c "from cryptography.fernet import Fernet; \
    #     print(Fernet.generate_key().decode())"
    secret_key: str = ""


def get_settings() -> Settings:
    """Build Settings from the environment, once per process."""
    return _cached_settings(Settings)


__all__ = ["Settings", "get_settings"]
