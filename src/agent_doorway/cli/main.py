"""`doorway` CLI entry point. Later phases add tenants, keys, policy and audit commands."""

from typing import Annotated

import typer
import uvicorn
from pydantic import ValidationError

from agent_doorway import __version__
from agent_doorway.config import get_settings

app = typer.Typer(help="Agent Doorway: a control plane for company AI.", no_args_is_help=True)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"agent-doorway {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_print_version, is_eager=True, help="Show the version."),
    ] = False,
) -> None:
    """Agent Doorway command-line interface."""


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Interface to bind.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to listen on.")] = 8080,
    reload: Annotated[bool, typer.Option(help="Restart on code changes (dev only).")] = False,
) -> None:
    """Run the gateway HTTP server."""
    # Validate the configuration here, before uvicorn starts, so a mistake is reported in a few
    # clear lines instead of a long traceback. Only field names and messages are printed: never
    # the input values, which can contain passwords.
    try:
        get_settings()
    except ValidationError as exc:
        typer.echo("Invalid configuration:", err=True)
        for error in exc.errors():
            field = "DOORWAY_" + "_".join(str(part) for part in error["loc"]).upper()
            typer.echo(f"  {field}: {error['msg']}", err=True)
        raise typer.Exit(code=2) from None
    uvicorn.run(
        "agent_doorway.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )
