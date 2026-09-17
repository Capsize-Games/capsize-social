"""ORM models."""

import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from capsize_social.db.base import Base, UtcDateTime

__all__ = ["BlueskyAccount", "DiscordServer"]


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class BlueskyAccount(Base):
    """One Bluesky account this service can post as.

    The app password is stored encrypted (see `crypto.SecretBox`) and
    is never returned to a caller after it is written.
    """

    __tablename__ = "bluesky_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    handle: Mapped[str] = mapped_column(String(255), unique=True)
    pds_host: Mapped[str] = mapped_column(
        String(255), default="https://bsky.social"
    )
    encrypted_app_password: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(default=True)

    followers_count: Mapped[int] = mapped_column(Integer, default=0)
    follows_count: Mapped[int] = mapped_column(Integer, default=0)
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    stats_fetched_at: Mapped[datetime.datetime | None] = mapped_column(
        UtcDateTime, default=None
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
    )


class DiscordServer(Base):
    """One Discord server (guild) this service can send messages in.

    The bot token is stored encrypted (see `crypto.SecretBox`) and is
    never returned to a caller after it is written, except via the
    dedicated `/gateway-token` endpoint a persistent gateway connection
    needs (see the service README for why that isn't a new trust
    boundary beyond the shared API key every caller already has).
    """

    __tablename__ = "discord_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    guild_id: Mapped[str] = mapped_column(String(32), unique=True)
    test_channel_id: Mapped[str] = mapped_column(String(32))
    encrypted_bot_token: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(default=True)

    member_count: Mapped[int] = mapped_column(Integer, default=0)
    stats_fetched_at: Mapped[datetime.datetime | None] = mapped_column(
        UtcDateTime, default=None
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
    )
