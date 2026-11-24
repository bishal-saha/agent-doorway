"""Liveness (/healthz) and readiness (/readyz) endpoints.

Liveness never touches dependencies: it only says the process is up.
Readiness checks every dependency, so a load balancer only sends traffic to a gateway
that can actually serve it.
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agent_doorway import __version__
from agent_doorway.health import run_probes

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    state: Any = request.app.state
    checks = await run_probes(state.probes, timeout_seconds=state.settings.probe_timeout_seconds)
    ready = all(result == "ok" for result in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )
