"""CRUD, stats, and one-shot posting for Bluesky accounts."""

import base64
import datetime

from capsize_bluesky import (
    BlueskyAccountClient,
    BlueskyAPIError,
    BlueskyAuthError,
    ProfileStats,
)
from fastapi import APIRouter, Depends, HTTPException, status

from capsize_social.auth import require_api_key
from capsize_social.deps import BoxDep, SessionDep
from capsize_social.models import BlueskyAccount
from capsize_social.routers._bluesky_common import (
    authenticated_client,
    get_or_404,
)
from capsize_social.schemas import (
    BlueskyAccountCreate,
    BlueskyAccountOut,
    BlueskyAccountUpdate,
    PostBluesky,
    UpdateBlueskyHandle,
    UpdateBlueskyProfile,
)

router = APIRouter(
    prefix="/bluesky-accounts",
    tags=["bluesky-accounts"],
    dependencies=[Depends(require_api_key)],
)


def _login_or_400(
    client: BlueskyAccountClient, handle: str, app_password: str
) -> ProfileStats | None:
    try:
        return client.login(handle, app_password)
    except BlueskyAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Bluesky handle or app password",
        ) from exc


def _decode_image(data: str | None) -> bytes | None:
    """Decode a base64-encoded avatar/banner, or `None` if unset."""
    return base64.b64decode(data) if data is not None else None


def _apply_stats(account: BlueskyAccount, stats: ProfileStats) -> None:
    account.followers_count = stats.followers_count
    account.follows_count = stats.follows_count
    account.posts_count = stats.posts_count
    account.stats_fetched_at = datetime.datetime.now(datetime.UTC)


@router.get("", response_model=list[BlueskyAccountOut])
def list_accounts(session: SessionDep) -> list[BlueskyAccount]:
    """List all Bluesky accounts, with their last-cached stats."""
    return list(
        session.query(BlueskyAccount).order_by(BlueskyAccount.label)
    )


@router.post(
    "", response_model=BlueskyAccountOut, status_code=status.HTTP_201_CREATED
)
def create_account(
    body: BlueskyAccountCreate, session: SessionDep, box: BoxDep
) -> BlueskyAccount:
    """Add a Bluesky account. Rejects an invalid handle/app-password pair."""
    client = BlueskyAccountClient(service=body.pds_host)
    stats = _login_or_400(client, body.handle, body.app_password)
    account = BlueskyAccount(
        label=body.label,
        handle=body.handle,
        pds_host=body.pds_host,
        encrypted_app_password=box.encrypt(body.app_password),
    )
    if stats is not None:
        _apply_stats(account, stats)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.get("/{account_id}", response_model=BlueskyAccountOut)
def get_account(account_id: int, session: SessionDep) -> BlueskyAccount:
    """Fetch one account."""
    return get_or_404(session, account_id)


@router.patch("/{account_id}", response_model=BlueskyAccountOut)
def update_account(
    account_id: int,
    body: BlueskyAccountUpdate,
    session: SessionDep,
    box: BoxDep,
) -> BlueskyAccount:
    """Update an account's label, app password, and/or active flag."""
    account = get_or_404(session, account_id)
    if body.label is not None:
        account.label = body.label
    if body.is_active is not None:
        account.is_active = body.is_active
    if body.app_password is not None:
        client = BlueskyAccountClient(service=account.pds_host)
        _login_or_400(client, account.handle, body.app_password)
        account.encrypted_app_password = box.encrypt(body.app_password)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, session: SessionDep) -> None:
    """Remove an account."""
    account = get_or_404(session, account_id)
    session.delete(account)
    session.commit()


@router.post("/{account_id}/refresh-stats", response_model=BlueskyAccountOut)
def refresh_stats(
    account_id: int, session: SessionDep, box: BoxDep
) -> BlueskyAccount:
    """Pull fresh follower/follows/post counts for one account."""
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    stats = client.profile_stats()
    _apply_stats(account, stats)
    session.commit()
    session.refresh(account)
    return account


@router.post("/{account_id}/post", status_code=status.HTTP_204_NO_CONTENT)
def post(
    account_id: int, body: PostBluesky, session: SessionDep, box: BoxDep
) -> None:
    """Post `text` to Bluesky as this account."""
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    try:
        client.create_post(body.text)
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky post failed: {exc}",
        ) from exc


@router.patch(
    "/{account_id}/profile", status_code=status.HTTP_204_NO_CONTENT
)
def update_profile(
    account_id: int,
    body: UpdateBlueskyProfile,
    session: SessionDep,
    box: BoxDep,
) -> None:
    """Update this account's bio, display name, avatar, and/or banner."""
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    try:
        client.update_profile(
            description=body.description,
            display_name=body.display_name,
            avatar=_decode_image(body.avatar_base64),
            banner=_decode_image(body.banner_base64),
        )
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky profile update failed: {exc}",
        ) from exc


@router.post("/{account_id}/update-handle", response_model=BlueskyAccountOut)
def update_handle(
    account_id: int,
    body: UpdateBlueskyHandle,
    session: SessionDep,
    box: BoxDep,
) -> BlueskyAccount:
    """Switch this account's Bluesky handle (e.g. to a verified domain).

    The caller must have already published the domain-verification
    DNS record Bluesky requires - this only calls the AT Protocol
    identity update, it doesn't check DNS itself. Updates the stored
    `handle` only after Bluesky confirms the switch.
    """
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    try:
        client.update_handle(body.handle)
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky handle update failed: {exc}",
        ) from exc
    account.handle = body.handle
    session.commit()
    session.refresh(account)
    return account
