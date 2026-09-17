"""Pydantic request/response models for the HTTP API."""

import datetime

from pydantic import BaseModel, Field


class BlueskyAccountCreate(BaseModel):
    """Body for POST /bluesky-accounts."""

    label: str = Field(min_length=1, max_length=120)
    handle: str = Field(min_length=1, max_length=255)
    app_password: str = Field(min_length=1)
    pds_host: str = "https://bsky.social"


class BlueskyAccountUpdate(BaseModel):
    """Body for PATCH /bluesky-accounts/{id}. All fields optional."""

    label: str | None = Field(default=None, min_length=1, max_length=120)
    app_password: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class BlueskyAccountOut(BaseModel):
    """What the API returns for an account. Never includes the password."""

    model_config = {"from_attributes": True}

    id: int
    label: str
    handle: str
    pds_host: str
    is_active: bool
    followers_count: int
    follows_count: int
    posts_count: int
    stats_fetched_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PostBluesky(BaseModel):
    """Body for POST /bluesky-accounts/{id}/post."""

    text: str = Field(min_length=1, max_length=2000)


class DiscordServerCreate(BaseModel):
    """Body for POST /discord-servers."""

    label: str = Field(min_length=1, max_length=120)
    guild_id: str = Field(min_length=1, max_length=32)
    test_channel_id: str = Field(min_length=1, max_length=32)
    bot_token: str = Field(min_length=1)


class DiscordServerUpdate(BaseModel):
    """Body for PATCH /discord-servers/{id}. All fields optional."""

    label: str | None = Field(default=None, min_length=1, max_length=120)
    test_channel_id: str | None = Field(
        default=None, min_length=1, max_length=32
    )
    bot_token: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class DiscordServerOut(BaseModel):
    """What the API returns for a server. Never includes the bot token."""

    model_config = {"from_attributes": True}

    id: int
    label: str
    guild_id: str
    test_channel_id: str
    is_active: bool
    member_count: int
    stats_fetched_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class SendDiscordMessage(BaseModel):
    """Body for POST /discord-servers/{id}/send-message."""

    channel_id: str | None = Field(
        default=None,
        max_length=32,
        description="Defaults to the server's own test_channel_id.",
    )
    content: str = Field(min_length=1, max_length=2000)


class GatewayTokenOut(BaseModel):
    """What GET /discord-servers/{id}/gateway-token returns."""

    bot_token: str
