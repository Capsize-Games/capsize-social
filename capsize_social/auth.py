"""Service-to-service auth: a single shared API key, not a login flow.

No human authenticates against this service directly - every caller
(social-manager's dashboard backend, an AIRunner extension, ...) is
trusted equally and identified only by holding the key. Same
convention as capsize-persona and AIRunner's own fastsearch extension.

The constant-time comparison comes from `capsize-commons`. The dependency
still takes settings through FastAPI's `Depends`, rather than reading them
directly, so the test suite's `dependency_overrides` keep working.
"""

from __future__ import annotations

from capsize_commons.web import check_api_key
from fastapi import Header, HTTPException, status

from capsize_social.deps import SettingsDep


def require_api_key(
    settings: SettingsDep, x_api_key: str = Header(default="")
) -> None:
    """Reject the request unless `X-API-Key` matches the configured key."""
    if not check_api_key(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


__all__ = ["require_api_key"]
