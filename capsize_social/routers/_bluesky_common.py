"""Shared helpers for the Bluesky account routers.

Split out so `bluesky_accounts.py` (CRUD + stats) and
`bluesky_content.py` (posts/reposts/context/delete) - both operating
on the same `BlueskyAccount` row - don't duplicate the lookup and
authenticated-client logic.
"""

from capsize_bluesky import (
    BlueskyAccountClient,
    BlueskyAPIError,
    BlueskyAuthError,
)
from fastapi import HTTPException, status

from capsize_social.deps import BoxDep, SessionDep
from capsize_social.models import BlueskyAccount


def get_or_404(session: SessionDep, account_id: int) -> BlueskyAccount:
    """Fetch `account_id`, or raise a 404."""
    account = session.get(BlueskyAccount, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


def authenticated_client(
    account: BlueskyAccount, box: BoxDep
) -> BlueskyAccountClient:
    """Log in as `account`, or raise a 502 if Bluesky rejects it."""
    app_password = box.decrypt(account.encrypted_app_password)
    client = BlueskyAccountClient(service=account.pds_host)
    try:
        client.login(account.handle, app_password)
    except BlueskyAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Bluesky rejected the stored app password",
        ) from exc
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky login failed: {exc}",
        ) from exc
    return client
