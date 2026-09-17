from unittest.mock import MagicMock, patch

from capsize_bluesky import (
    BlueskyAPIError,
    BlueskyAuthError,
    PostRecord,
    ProfileStats,
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


def _create(client: TestClient, headers: dict[str, str]) -> dict:
    return client.post(
        ACCOUNTS_URL,
        headers=headers,
        json={
            "label": "Main",
            "handle": "alice.bsky.social",
            "app_password": "xxxx-xxxx-xxxx-xxxx",
        },
    ).json()


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_create_account_success(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()

    response = client.post(
        ACCOUNTS_URL,
        headers=api_headers,
        json={
            "label": "Main",
            "handle": "alice.bsky.social",
            "app_password": "xxxx-xxxx-xxxx-xxxx",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["handle"] == "alice.bsky.social"
    assert body["followers_count"] == 10
    assert "app_password" not in body


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_create_account_rejects_bad_login(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.side_effect = BlueskyAuthError("no")

    response = client.post(
        ACCOUNTS_URL,
        headers=api_headers,
        json={
            "label": "Main",
            "handle": "alice.bsky.social",
            "app_password": "bad",
        },
    )

    assert response.status_code == 400


def test_create_account_requires_api_key(client: TestClient) -> None:
    response = client.post(
        ACCOUNTS_URL,
        json={
            "label": "Main",
            "handle": "alice.bsky.social",
            "app_password": "x",
        },
    )
    assert response.status_code == 401


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_refresh_stats(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_client_cls.return_value.profile_stats.return_value = _stats(
        followers_count=99
    )

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/refresh-stats", headers=api_headers
    )

    assert response.status_code == 200
    assert response.json()["followers_count"] == 99


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_post_succeeds(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/post",
        headers=api_headers,
        json={"text": "hello world"},
    )

    assert response.status_code == 204
    mock_client_cls.return_value.create_post.assert_called_once_with(
        "hello world"
    )


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_post_reports_api_failure(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_client_cls.return_value.create_post.side_effect = BlueskyAPIError(
        "rate limited"
    )

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/post",
        headers=api_headers,
        json={"text": "hello world"},
    )

    assert response.status_code == 502


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_list_posts_returns_page(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_client_cls.return_value.list_posts.return_value = (
        [
            PostRecord(
                uri="at://did/app.bsky.feed.post/1",
                cid="cid1",
                text="hello",
                created_at="2026-01-01T00:00:00Z",
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
        }
    ]
    mock_client_cls.return_value.list_posts.assert_called_once_with(
        cursor=None
    )


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_list_posts_passes_through_cursor(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()
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


@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_list_posts_reports_api_failure(
    mock_client_cls: MagicMock, client: TestClient, api_headers: dict[str, str]
) -> None:
    mock_client_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_client_cls.return_value.list_posts.side_effect = BlueskyAPIError(
        "rate limited"
    )

    response = client.get(
        f"{ACCOUNTS_URL}/{account['id']}/posts", headers=api_headers
    )

    assert response.status_code == 502


def test_delete_account(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    with patch(
        "capsize_social.routers.bluesky_accounts.BlueskyAccountClient"
    ) as mock_client_cls:
        mock_client_cls.return_value.login.return_value = _stats()
        account = _create(client, api_headers)

    response = client.delete(
        f"{ACCOUNTS_URL}/{account['id']}", headers=api_headers
    )

    assert response.status_code == 204
    assert (
        client.get(
            f"{ACCOUNTS_URL}/{account['id']}", headers=api_headers
        ).status_code
        == 404
    )
