# capsize-social

## Fleet boundary

This service adopts shared settings, database, API-key, and health primitives
while retaining provider-specific moderation, posting, credential encryption,
and deployment behavior. Its boundary and the unavailable published Bluesky
consumer pin are documented in
[`docs/FLEET_CONSOLIDATION.md`](docs/FLEET_CONSOLIDATION.md).

Decoupled social-account connections: credential storage and one-shot
posting/sending actions for Bluesky and Discord, over HTTP. The
"connections" counterpart to
[capsize-persona](https://github.com/capsize-games/capsize-persona)'s
"voice/memory" - callable by a human-facing dashboard and by a headless
agent (e.g. an AIRunner extension) equally, neither one owning the
other.

Deliberately **REST-only** - no Discord gateway (websocket) connection.
Receiving and reacting to incoming messages is a different, stateful
piece of infrastructure that belongs to whatever owns that job, not
this service.

## Auth

Every request needs an `X-API-Key` header matching `SOCIAL_API_KEY`.
Service-to-service auth, not a login system - no human authenticates
against this service directly.

## API

- `POST/GET/PATCH/DELETE /api/bluesky-accounts`,
  `POST /api/bluesky-accounts/{id}/refresh-stats`,
  `POST /api/bluesky-accounts/{id}/post`.
- `POST/GET/PATCH/DELETE /api/discord-servers`,
  `POST /api/discord-servers/{id}/refresh-stats`,
  `POST /api/discord-servers/{id}/send-message`,
  `GET /api/discord-servers/{id}/gateway-token` - the decrypted bot
  token, for a caller running its own persistent gateway connection
  (`Client.start()` needs the raw token; there's no way around that).
  Not a broader trust boundary than every other endpoint here: the
  shared API key already authorizes posting/sending as any stored
  account freely.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "capsize-bluesky @ git+https://github.com/Capsize-Games/capsize-bluesky.git@main"
pip install -e ".[dev]"

cp .env.example .env   # fill in the generated secrets, see comments inside
alembic upgrade head
python -m capsize_social   # serves on :8880
```

## Tests

```bash
pytest
```

## Checks

```bash
ruff check capsize_social tests migrations
mypy capsize_social
```
