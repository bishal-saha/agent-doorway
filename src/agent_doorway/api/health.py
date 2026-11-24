"""Liveness endpoint. Liveness never touches dependencies: it only says the process is up."""

from fastapi import APIRouter

from agent_doorway import __version__

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}