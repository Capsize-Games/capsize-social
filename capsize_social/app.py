"""The FastAPI application."""

from fastapi import FastAPI

from capsize_social.routers import bluesky_accounts, discord_servers


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Every route resolves settings per-request via the `get_settings`
    dependency, so tests isolate configuration with
    `app.dependency_overrides[get_settings]` rather than a constructor
    argument here.
    """
    app = FastAPI(title="Capsize Social")
    app.include_router(bluesky_accounts.router, prefix="/api")
    app.include_router(discord_servers.router, prefix="/api")

    @app.get("/health")
    def health() -> dict[str, bool]:
        """Report liveness for container healthchecks."""
        return {"ok": True}

    return app


app = create_app()
