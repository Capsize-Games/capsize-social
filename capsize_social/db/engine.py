"""SQLAlchemy engine/session setup, shared with the rest of the fleet.

This module used to hold its own copy. It now re-exports the shared
implementation, which adds two things the local copy documented but did not
actually do: it turns on `PRAGMA foreign_keys` for SQLite (SQLite leaves it
off by default, so every `ON DELETE CASCADE` was silently inert) and it
enables `pool_pre_ping` so a dropped pooled connection is replaced rather
than failing a request.
"""

from __future__ import annotations

from capsize_commons.db import make_engine, make_session_factory

__all__ = ["make_engine", "make_session_factory"]
