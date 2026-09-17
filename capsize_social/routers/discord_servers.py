"""CRUD + stats-refresh + send/gateway-token endpoints for Discord servers."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from capsize_social import discord_client
from capsize_social.auth import require_api_key
from capsize_social.deps import BoxDep, SessionDep
from capsize_social.discord_client import DiscordError
from capsize_social.models import DiscordServer
from capsize_social.schemas import (
    DiscordServerCreate,
    DiscordServerOut,
    DiscordServerUpdate,
    GatewayTokenOut,
    SendDiscordMessage,
)

router = APIRouter(
    prefix="/discord-servers",
    tags=["discord-servers"],
    dependencies=[Depends(require_api_key)],
)


def _get_or_404(session: SessionDep, server_id: int) -> DiscordServer:
    server = session.get(DiscordServer, server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord server not found",
        )
    return server


def _validate_token_or_400(bot_token: str) -> None:
    try:
        discord_client.validate_token(bot_token)
    except DiscordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


def _member_count_or_400(bot_token: str, guild_id: str) -> int:
    try:
        return discord_client.get_member_count(bot_token, guild_id)
    except DiscordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("", response_model=list[DiscordServerOut])
def list_servers(session: SessionDep) -> list[DiscordServer]:
    """List all Discord servers, with their last-cached stats."""
    return list(session.query(DiscordServer).order_by(DiscordServer.label))


@router.post(
    "", response_model=DiscordServerOut, status_code=status.HTTP_201_CREATED
)
def create_server(
    body: DiscordServerCreate, session: SessionDep, box: BoxDep
) -> DiscordServer:
    """Add a Discord server. Rejects an invalid bot token or guild."""
    _validate_token_or_400(body.bot_token)
    member_count = _member_count_or_400(body.bot_token, body.guild_id)
    server = DiscordServer(
        label=body.label,
        guild_id=body.guild_id,
        test_channel_id=body.test_channel_id,
        encrypted_bot_token=box.encrypt(body.bot_token),
        member_count=member_count,
        stats_fetched_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(server)
    session.commit()
    session.refresh(server)
    return server


@router.get("/{server_id}", response_model=DiscordServerOut)
def get_server(server_id: int, session: SessionDep) -> DiscordServer:
    """Fetch one server."""
    return _get_or_404(session, server_id)


@router.patch("/{server_id}", response_model=DiscordServerOut)
def update_server(
    server_id: int,
    body: DiscordServerUpdate,
    session: SessionDep,
    box: BoxDep,
) -> DiscordServer:
    """Update a server's label, channel, token, and/or active flag."""
    server = _get_or_404(session, server_id)
    if body.label is not None:
        server.label = body.label
    if body.test_channel_id is not None:
        server.test_channel_id = body.test_channel_id
    if body.is_active is not None:
        server.is_active = body.is_active
    if body.bot_token is not None:
        _validate_token_or_400(body.bot_token)
        server.encrypted_bot_token = box.encrypt(body.bot_token)
    session.commit()
    session.refresh(server)
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: int, session: SessionDep) -> None:
    """Remove a server."""
    server = _get_or_404(session, server_id)
    session.delete(server)
    session.commit()


@router.post("/{server_id}/refresh-stats", response_model=DiscordServerOut)
def refresh_stats(
    server_id: int, session: SessionDep, box: BoxDep
) -> DiscordServer:
    """Pull a fresh member count for one server."""
    server = _get_or_404(session, server_id)
    bot_token = box.decrypt(server.encrypted_bot_token)
    try:
        server.member_count = discord_client.get_member_count(
            bot_token, server.guild_id
        )
    except DiscordError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    server.stats_fetched_at = datetime.datetime.now(datetime.UTC)
    session.commit()
    session.refresh(server)
    return server


@router.post(
    "/{server_id}/send-message", status_code=status.HTTP_204_NO_CONTENT
)
def send_message(
    server_id: int,
    body: SendDiscordMessage,
    session: SessionDep,
    box: BoxDep,
) -> None:
    """Post a message to `channel_id` (default: the server's test channel)."""
    server = _get_or_404(session, server_id)
    bot_token = box.decrypt(server.encrypted_bot_token)
    channel_id = body.channel_id or server.test_channel_id
    try:
        discord_client.send_message(bot_token, channel_id, body.content)
    except DiscordError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc


@router.get("/{server_id}/gateway-token", response_model=GatewayTokenOut)
def gateway_token(
    server_id: int, session: SessionDep, box: BoxDep
) -> GatewayTokenOut:
    """Return the decrypted bot token, for a persistent gateway connection.

    Not a broader trust boundary than every other endpoint here: the
    shared API key already authorizes "post/send as this account"
    freely, so also reading the raw token isn't meaningfully more
    access under the same key.
    """
    server = _get_or_404(session, server_id)
    return GatewayTokenOut(bot_token=box.decrypt(server.encrypted_bot_token))
