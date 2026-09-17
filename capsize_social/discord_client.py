"""A thin Discord REST client: token validation, guild stats, messages.

Deliberately REST-only, over plain `httpx` calls, with no gateway
(websocket) connection. Posting/sending is a one-shot action; nothing
here reads or reacts to Discord events. A gateway-connected bot process
is a real, separate piece of infrastructure that belongs to whatever
owns *receiving* messages, not this service.
"""

import httpx

API_BASE = "https://discord.com/api/v10"


class DiscordError(Exception):
    """Any Discord API failure: bad token, missing permissions, etc."""


def _headers(bot_token: str) -> dict[str, str]:
    return {"Authorization": f"Bot {bot_token}"}


def validate_token(bot_token: str) -> str:
    """Confirm `bot_token` is valid. Returns the bot's own username."""
    response = httpx.get(f"{API_BASE}/users/@me", headers=_headers(
        bot_token
    ))
    if response.status_code != 200:
        raise DiscordError("Invalid bot token")
    return str(response.json()["username"])


def get_member_count(bot_token: str, guild_id: str) -> int:
    """Return the approximate member count of `guild_id`.

    The bot must already be a member of the guild.
    """
    response = httpx.get(
        f"{API_BASE}/guilds/{guild_id}",
        headers=_headers(bot_token),
        params={"with_counts": "true"},
    )
    if response.status_code != 200:
        raise DiscordError(
            "Could not read guild — is the bot invited to it?"
        )
    return int(response.json()["approximate_member_count"])


def send_message(bot_token: str, channel_id: str, content: str) -> None:
    """Post `content` to `channel_id`."""
    response = httpx.post(
        f"{API_BASE}/channels/{channel_id}/messages",
        headers=_headers(bot_token),
        json={"content": content},
    )
    if response.status_code != 200:
        raise DiscordError(
            "Could not send message — check the bot's channel permissions"
        )
