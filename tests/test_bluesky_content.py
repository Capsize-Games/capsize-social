from typing import Any
from unittest.mock import MagicMock, patch

from capsize_bluesky import (
    BlueskyAPIError,
    PostRecord,
    ProfileStats,
    RepostRecord,
)
from fastapi.testclient import TestClient

ACCOUNTS_URL = "/api/bluesky-accounts"


def _stats(**overrides: object) -> ProfileStats:
    defaults: dict[str, object] = {
        "did": "did:plc:abc123",
        "handle": "alice.bsky.social",
        "display_name": "Alice",
        "followers_count": 10,
        "follows_count": 3,
        "posts_count": 42,
    }
    defaults.update(overrides)
    return ProfileStats(**defaults)  # type: ignore[arg-type]


def _create(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    with patch(
        "capsize_social.routers.bluesky_accounts.BlueskyAccountClient"
    ) as mock_client_cls:
        mock_client_cls.return_value.login.return_value = _stats()
        result: dict[str, Any] = client.post(
            ACCOUNTS_URL,
            headers=headers,
            json={
                "label": "Main",
                "handle": "alice.bsky.social",
                "app_password": "xxxx-xxxx-xxxx-xxxx",
            },
        ).json()
        return result


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_list_posts_returns_page(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.list_posts.return_value = (
        [
            PostRecord(
                uri="at://did/app.bsky.feed.post/1",
                cid="cid1",
                text="hello",
                created_at="2026-01-01T00:00:00Z",
                reply_parent_uri="at://did/app.bsky.feed.post/0",
            )
        ],
        "next-cursor",
    )

    response = client.get(
        f"{ACCOUNTS_URL}/{account['id']}/posts", headers=api_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cursor"] == "next-cursor"
    assert body["posts"] == [
        {
            "uri": "at://did/app.bsky.feed.post/1",
            "cid": "cid1",
            "text": "hello",
            "created_at": "2026-01-01T00:00:00Z",
            "reply_parent_uri": "at://did/app.bsky.feed.post/0",
        }
    ]
    mock_client_cls.return_value.list_posts.assert_called_once_with(
        cursor=None
    )


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_list_posts_passes_through_cursor(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.list_posts.return_value = ([], None)

    client.get(
        f"{ACCOUNTS_URL}/{account['id']}/posts",
        headers=api_headers,
        params={"cursor": "page-2"},
    )

    mock_client_cls.return_value.list_posts.assert_called_once_with(
        cursor="page-2"
    )


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_list_posts_reports_api_failure(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.list_posts.side_effect = BlueskyAPIError(
        "rate limited"
    )

    response = client.get(
        f"{ACCOUNTS_URL}/{account['id']}/posts", headers=api_headers
    )

    assert response.status_code == 502


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_list_reposts_returns_page(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.list_reposts.return_value = (
        [
            RepostRecord(
                uri="at://did/app.bsky.feed.repost/1",
                subject_uri="at://other/app.bsky.feed.post/5",
                created_at="2026-01-01T00:00:00Z",
            )
        ],
        None,
    )

    response = client.get(
        f"{ACCOUNTS_URL}/{account['id']}/reposts", headers=api_headers
    )

    assert response.status_code == 200
    assert response.json()["reposts"][0]["subject_uri"] == (
        "at://other/app.bsky.feed.post/5"
    )


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_get_context_resolves_post_and_author(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.get_post.return_value = PostRecord(
        uri="at://other/app.bsky.feed.post/5",
        cid="cid5",
        text="the parent post",
        created_at="2026-01-01T00:00:00Z",
    )
    mock_client_cls.return_value.profile_stats.return_value = _stats(
        handle="bob.bsky.social", display_name="Bob"
    )

    response = client.get(
        f"{ACCOUNTS_URL}/{account['id']}/context",
        headers=api_headers,
        params={"uri": "at://other/app.bsky.feed.post/5"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "the parent post"
    assert body["author_handle"] == "bob.bsky.social"
    assert body["author_display_name"] == "Bob"


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_get_context_handles_unresolvable_post(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.get_post.return_value = None

    response = client.get(
        f"{ACCOUNTS_URL}/{account['id']}/context",
        headers=api_headers,
        params={"uri": "at://other/app.bsky.feed.post/gone"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] is None
    assert body["author_handle"] is None


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_delete_post_calls_client(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)

    response = client.delete(
        f"{ACCOUNTS_URL}/{account['id']}/posts",
        headers=api_headers,
        params={"uri": "at://did/app.bsky.feed.post/1"},
    )

    assert response.status_code == 204
    mock_client_cls.return_value.delete_post.assert_called_once_with(
        "at://did/app.bsky.feed.post/1"
    )


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
def test_delete_post_reports_api_failure(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    account = _create(client, api_headers)
    mock_client_cls.return_value.delete_post.side_effect = BlueskyAPIError(
        "not found"
    )

    response = client.delete(
        f"{ACCOUNTS_URL}/{account['id']}/posts",
        headers=api_headers,
        params={"uri": "at://did/app.bsky.feed.post/1"},
    )

    assert response.status_code == 502
