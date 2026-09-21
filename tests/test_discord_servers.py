from unittest.mock import patch

from fastapi.testclient import TestClient

from capsize_social.discord_client import DiscordError

SERVERS_URL = "/api/discord-servers"


def _create(client: TestClient, headers: dict[str, str]) -> dict:
    with (
        patch(
            "capsize_social.routers.discord_servers.discord_client"
            ".validate_token",
            return_value="capsize#0000",
        ),
        patch(
            "capsize_social.routers.discord_servers.discord_client"
            ".get_member_count",
            return_value=42,
        ),
    ):
        return client.post(
            SERVERS_URL,
            headers=headers,
            json={
                "label": "Test Server",
                "guild_id": "1",
                "test_channel_id": "2",
                "bot_token": "tok",
            },
        ).json()


def test_create_server_success(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    body = _create(client, api_headers)
    assert body["label"] == "Test Server"
    assert body["member_count"] == 42
    assert "bot_token" not in body


def test_create_server_rejects_bad_token(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    with patch(
        "capsize_social.routers.discord_servers.discord_client.validate_token",
        side_effect=DiscordError("bad token"),
    ):
        response = client.post(
            SERVERS_URL,
            headers=api_headers,
            json={
                "label": "Test Server",
                "guild_id": "1",
                "test_channel_id": "2",
                "bot_token": "bad",
            },
        )
    assert response.status_code == 400


def test_send_message_uses_default_test_channel(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    server = _create(client, api_headers)
    with patch(
        "capsize_social.routers.discord_servers.discord_client.send_message"
    ) as mock_send:
        response = client.post(
            f"{SERVERS_URL}/{server['id']}/send-message",
            headers=api_headers,
            json={"content": "hi"},
        )
    assert response.status_code == 204
    mock_send.assert_called_once_with("tok", "2", "hi")


def test_send_message_uses_explicit_channel(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    server = _create(client, api_headers)
    with patch(
        "capsize_social.routers.discord_servers.discord_client.send_message"
    ) as mock_send:
        client.post(
            f"{SERVERS_URL}/{server['id']}/send-message",
            headers=api_headers,
            json={"content": "hi", "channel_id": "999"},
        )
    mock_send.assert_called_once_with("tok", "999", "hi")


def test_gateway_token_returns_decrypted_token(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    server = _create(client, api_headers)

    response = client.get(
        f"{SERVERS_URL}/{server['id']}/gateway-token", headers=api_headers
    )

    assert response.status_code == 200
    assert response.json()["bot_token"] == "tok"


def test_gateway_token_requires_api_key(client: TestClient) -> None:
    response = client.get(f"{SERVERS_URL}/1/gateway-token")
    assert response.status_code == 401


def test_refresh_stats(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    server = _create(client, api_headers)
    with patch(
        "capsize_social.routers.discord_servers.discord_client"
        ".get_member_count",
        return_value=99,
    ):
        response = client.post(
            f"{SERVERS_URL}/{server['id']}/refresh-stats", headers=api_headers
        )
    assert response.status_code == 200
    assert response.json()["member_count"] == 99


def test_delete_server(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    server = _create(client, api_headers)

    response = client.delete(
        f"{SERVERS_URL}/{server['id']}", headers=api_headers
    )

    assert response.status_code == 204
    assert (
        client.get(
            f"{SERVERS_URL}/{server['id']}", headers=api_headers
        ).status_code
        == 404
    )


def test_list_servers_requires_api_key(client: TestClient) -> None:
    response = client.get(SERVERS_URL)
    assert response.status_code == 401
