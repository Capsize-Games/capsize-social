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


class UpdateBlueskyProfile(BaseModel):
    """Body for PATCH /bluesky-accounts/{id}/profile. Fields optional."""

    description: str | None = Field(default=None, max_length=256)
    display_name: str | None = Field(default=None, max_length=64)


class BlueskyPostOut(BaseModel):
    """One post, as returned by GET /bluesky-accounts/{id}/posts."""

    uri: str
    cid: str
    text: str
    created_at: str
    reply_parent_uri: str | None = None


class BlueskyPostsPage(BaseModel):
    """One page of GET /bluesky-accounts/{id}/posts."""

    posts: list[BlueskyPostOut]
    cursor: str | None


class BlueskyRepostOut(BaseModel):
    """One repost, as returned by GET /bluesky-accounts/{id}/reposts."""

    uri: str
    subject_uri: str
    created_at: str


class BlueskyRepostsPage(BaseModel):
    """One page of GET /bluesky-accounts/{id}/reposts."""

    reposts: list[BlueskyRepostOut]
    cursor: str | None


class BlueskyPostContextOut(BaseModel):
    """What GET /bluesky-accounts/{id}/context returns.

    `None` fields mean the referenced post couldn't be resolved (e.g.
    the other account since deleted it) - a best-effort lookup, not a
    required one.
    """

    uri: str
    text: str | None
    created_at: str | None
    author_handle: str | None
    author_display_name: str | None


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
