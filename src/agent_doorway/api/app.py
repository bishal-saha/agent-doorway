"""Application factory. Everything the app needs is passed in, so tests can swap any part."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent_doorway import __version__
from agent_doorway.api import health
from agent_doorway.config import Settings, get_settings
from agent_doorway.health import PostgresProbe, Probe, RedisProbe


def create_app(settings: Settings | None = None, probes: Sequence[Probe] | None = None) -> FastAPI:
    settings = settings or get_settings()
    owned: list[PostgresProbe | RedisProbe] = []
    if probes is None:
        # Production default: probe the real dependencies, and close them on shutdown.
        owned = [PostgresProbe(settings.database_url), RedisProbe(settings.redis_url)]
        probes = owned

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        for probe in owned:
            await probe.close()

    app = FastAPI(title="Agent Doorway", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.probes = list(probes)
    app.include_router(health.router)
    return app
