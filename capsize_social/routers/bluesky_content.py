"""Read (and delete) an account's own post history on Bluesky.

Split out from `bluesky_accounts.py` (account CRUD/stats) once this
grew its own shape: reading full post/repost history, resolving a
reply's surrounding context, and deleting a post are all about
content, not the account record itself.
"""

from capsize_bluesky import BlueskyAccountClient, BlueskyAPIError
from fastapi import APIRouter, Depends, HTTPException, status

from capsize_social.auth import require_api_key
from capsize_social.deps import BoxDep, SessionDep
from capsize_social.routers._bluesky_common import (
    authenticated_client,
    get_or_404,
)
from capsize_social.schemas import (
    BlueskyPostContextOut,
    BlueskyPostOut,
    BlueskyPostsPage,
    BlueskyRepostOut,
    BlueskyRepostsPage,
)

router = APIRouter(
    prefix="/bluesky-accounts",
    tags=["bluesky-accounts"],
    dependencies=[Depends(require_api_key)],
)


def _fetch_page(
    client: BlueskyAccountClient, cursor: str | None
) -> BlueskyPostsPage:
    try:
        records, next_cursor = client.list_posts(cursor=cursor)
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky post listing failed: {exc}",
        ) from exc
    posts = [
        BlueskyPostOut(
            uri=r.uri,
            cid=r.cid,
            text=r.text,
            created_at=r.created_at,
            reply_parent_uri=r.reply_parent_uri,
        )
        for r in records
    ]
    return BlueskyPostsPage(posts=posts, cursor=next_cursor)


@router.get("/{account_id}/posts", response_model=BlueskyPostsPage)
def list_posts(
    account_id: int,
    session: SessionDep,
    box: BoxDep,
    cursor: str | None = None,
) -> BlueskyPostsPage:
    """Read one page of this account's own posts, straight from Bluesky.

    Not cached, unlike the stats columns - a safety audit needs the
    real, current post history, not a snapshot that can drift from it.
    """
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    return _fetch_page(client, cursor)


def _fetch_reposts_page(
    client: BlueskyAccountClient, cursor: str | None
) -> BlueskyRepostsPage:
    try:
        records, next_cursor = client.list_reposts(cursor=cursor)
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky repost listing failed: {exc}",
        ) from exc
    reposts = [
        BlueskyRepostOut(
            uri=r.uri, subject_uri=r.subject_uri, created_at=r.created_at
        )
        for r in records
    ]
    return BlueskyRepostsPage(reposts=reposts, cursor=next_cursor)


@router.get("/{account_id}/reposts", response_model=BlueskyRepostsPage)
def list_reposts(
    account_id: int,
    session: SessionDep,
    box: BoxDep,
    cursor: str | None = None,
) -> BlueskyRepostsPage:
    """Read one page of this account's own reposts, straight from Bluesky."""
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    return _fetch_reposts_page(client, cursor)


def _resolve_context(
    client: BlueskyAccountClient, uri: str
) -> BlueskyPostContextOut:
    post = client.get_post(uri)
    if post is None:
        return BlueskyPostContextOut(
            uri=uri,
            text=None,
            created_at=None,
            author_handle=None,
            author_display_name=None,
        )
    did = uri.removeprefix("at://").split("/")[0]
    try:
        author = client.profile_stats(did)
    except BlueskyAPIError:
        author = None
    return BlueskyPostContextOut(
        uri=uri,
        text=post.text,
        created_at=post.created_at,
        author_handle=author.handle if author else None,
        author_display_name=author.display_name if author else None,
    )


@router.get("/{account_id}/context", response_model=BlueskyPostContextOut)
def get_context(
    account_id: int, session: SessionDep, box: BoxDep, uri: str
) -> BlueskyPostContextOut:
    """Resolve one arbitrary post's author + text, e.g. a reply's parent.

    Best-effort - a `None` field means that post couldn't be resolved
    (already deleted, or otherwise unreachable), not an error.
    """
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    return _resolve_context(client, uri)


@router.delete("/{account_id}/posts", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    account_id: int, session: SessionDep, box: BoxDep, uri: str
) -> None:
    """Permanently delete one of this account's own posts."""
    account = get_or_404(session, account_id)
    client = authenticated_client(account, box)
    try:
        client.delete_post(uri)
    except BlueskyAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bluesky delete failed: {exc}",
        ) from exc
