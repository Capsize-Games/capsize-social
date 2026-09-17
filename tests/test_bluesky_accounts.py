from unittest.mock import MagicMock, patch

from capsize_bluesky import BlueskyAPIError, BlueskyAuthError, ProfileStats
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


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_refresh_stats(
    mock_create_cls: MagicMock,
    mock_auth_cls: MagicMock,
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    mock_create_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_auth_cls.return_value.profile_stats.return_value = _stats(
        followers_count=99
    )

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/refresh-stats", headers=api_headers
    )

    assert response.status_code == 200
    assert response.json()["followers_count"] == 99


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_refresh_stats_reports_transient_login_failure(
    mock_create_cls: MagicMock,
    mock_auth_cls: MagicMock,
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """A non-auth login failure surfaces as a 502, not a raw 500.

    E.g. a transient upstream API error, not a bad credential.
    """
    mock_create_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_auth_cls.return_value.login.side_effect = BlueskyAPIError(
        "rate limited"
    )

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/refresh-stats", headers=api_headers
    )

    assert response.status_code == 502


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_post_succeeds(
    mock_create_cls: MagicMock,
    mock_auth_cls: MagicMock,
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    mock_create_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/post",
        headers=api_headers,
        json={"text": "hello world"},
    )

    assert response.status_code == 204
    mock_auth_cls.return_value.create_post.assert_called_once_with(
        "hello world"
    )


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_post_reports_api_failure(
    mock_create_cls: MagicMock,
    mock_auth_cls: MagicMock,
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    mock_create_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_auth_cls.return_value.create_post.side_effect = BlueskyAPIError(
        "rate limited"
    )

    response = client.post(
        f"{ACCOUNTS_URL}/{account['id']}/post",
        headers=api_headers,
        json={"text": "hello world"},
    )

    assert response.status_code == 502


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_update_profile_succeeds(
    mock_create_cls: MagicMock,
    mock_auth_cls: MagicMock,
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    mock_create_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)

    response = client.patch(
        f"{ACCOUNTS_URL}/{account['id']}/profile",
        headers=api_headers,
        json={"description": "new bio", "display_name": "New Name"},
    )

    assert response.status_code == 204
    mock_auth_cls.return_value.update_profile.assert_called_once_with(
        description="new bio", display_name="New Name"
    )


@patch("capsize_social.routers._bluesky_common.BlueskyAccountClient")
@patch("capsize_social.routers.bluesky_accounts.BlueskyAccountClient")
def test_update_profile_reports_api_failure(
    mock_create_cls: MagicMock,
    mock_auth_cls: MagicMock,
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    mock_create_cls.return_value.login.return_value = _stats()
    account = _create(client, api_headers)
    mock_auth_cls.return_value.update_profile.side_effect = BlueskyAPIError(
        "nope"
    )

    response = client.patch(
        f"{ACCOUNTS_URL}/{account['id']}/profile",
        headers=api_headers,
        json={"description": "new bio"},
    )

    assert response.status_code == 502


def test_update_profile_requires_api_key(client: TestClient) -> None:
    response = client.patch(
        f"{ACCOUNTS_URL}/1/profile", json={"description": "new bio"}
    )
    assert response.status_code == 401


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
