"""Application factory. Everything the app needs is passed in, so tests can swap any part."""

from collections.abc import Sequence

from fastapi import FastAPI

from agent_doorway import __version__
from agent_doorway.api import health
from agent_doorway.config import Settings, get_settings


def create_app(settings: Settings | None = None, probes: Sequence[object] | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Agent Doorway", version=__version__)
    app.state.settings = settings
    app.state.probes = list(probes) if probes is not None else []
    app.include_router(health.router)
    return app