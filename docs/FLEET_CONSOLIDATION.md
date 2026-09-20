# Fleet consolidation audit

## Boundary and deployment

`capsize-social` is a Python 3.11+ FastAPI service owned by Capsize-Games.
It stores encrypted Bluesky/Discord credentials and provider-specific account
records in SQLAlchemy/Alembic-managed persistence, exposes REST-only routes,
and runs from the Docker image with an init-time migration and `/health`
container healthcheck. The service-to-service `X-API-Key` is not a human
login system; callers and secret delivery are deployment responsibilities.

The canonical repository is `Capsize-Games/capsize-social`. The published
shared dependency is `capsize-commons[config,db,web]>=0.1.2`; the local
`capsize-bluesky` source override remains because no published
`capsize-bluesky` artifact currently exists.

## Adopt / retain-local matrix

| Surface | Disposition | Evidence and decision |
| --- | --- | --- |
| Health/readiness routes | adopt | `capsize_commons.web.install_health_routes` supplies `/ready`; `health_body={"ok": true}` preserves the existing `/health` payload. Tests assert both status/body contracts. |
| Settings base and cache | adopt | `CapsizeSettings` and shared `get_settings` provide generic environment/file loading; `Settings` retains the `SOCIAL_` prefix and service fields. |
| API-key comparison | adopt | `capsize_commons.web.check_api_key` supplies constant-time comparison; the service retains its `X-API-Key` header and 401 response shape. |
| SQLAlchemy engine/session | adopt | `capsize_commons.db.make_engine` and `make_session_factory` replace the duplicated generic setup; service tables, migrations, and database URL policy remain local. |
| Bluesky transport/content policy | retain-local | Account refresh, posting, provider errors, and credential behavior remain in the social domain layer; the Bluesky package is a separate provider library. |
| Discord transport/gateway policy | retain-local | Discord REST actions, gateway-token exposure, and caller-owned persistent gateway behavior remain provider-specific. |
| Credential encryption | retain-local | `SecretBox` owns Fernet at-rest encryption and key handling; no shared database or auth primitive is substituted for it. |
| Service auth/routes | retain-local | Route prefixes, API-key dependency, moderation/posting behavior, schemas, and Alembic migrations are product API contracts. |
| Logging/retry policy | retain-local | Provider request behavior and operational logs are not changed for metric symmetry; no generic retry adapter is introduced. |
| Deployment/healthcheck | retain-local | Docker, Alembic startup, port 8880, `/health` probe, and secret injection are deployment policy. |

## Compatibility and release gate

The completed health migration is additive and shape-preserving: `/health`
remains `200 {"ok": true}` and `/ready` is the shared unauthenticated
`200 {"status":"ready"}` contract. Existing API routes, auth status, data
models, migrations, provider calls, and persistence remain unchanged.

The consumer currently declares `capsize-bluesky>=0.1.0` but resolves an
editable `../capsize-bluesky` source in `uv` and installs the Git `main` source
in local Docker/CI instructions. That is deliberately documented as a release
blocker: do not replace it with a fabricated PyPI version. Once hq#23 proves
trusted publishing and a compatible artifact exists, pinning belongs in a
separate focused consumer PR with a published-package compatibility test.

Rollback is to revert the prior focused health-adoption PR or this audit-only
metadata commit. The service's route, database, credential, and deployment
contracts remain explicit and recoverable.

## Dependency provenance and metrics

Runtime authorities are public PyPI packages: `capsize-commons[config,db,web]
>=0.1.2`, FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic,
`pydantic-settings`, cryptography, httpx, and the provider package. `uv.lock`
records the resolved graph; the only local exception is the explicitly
documented Bluesky checkout override. The repository has 34 passing tests,
including the health parity fixtures. This PR changes no runtime source or
dependency resolution.
