"""Command-line interface for fastpubsub application."""

import asyncio
from typing import Annotated

import typer

from fastpubsub.api import app, run_server
from fastpubsub.config import settings
from fastpubsub.database import run_migrations
from fastpubsub.logger import get_logger
from fastpubsub.models import CreateClient
from fastpubsub.services import cleanup_acked_messages, cleanup_stuck_messages, create_client
from fastpubsub.services.clients import generate_secret

logger = get_logger(__name__)
cli = typer.Typer()


async def _log_command_execution_async(command_name: str, func, *args, **kwargs):
    """Helper to log async command execution with start and finish messages.

    Args:
        command_name: Name of the command being executed.
        func: Async function to execute.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the executed function.
    """
    logger.info(f"Starting {command_name} command")
    result = await func(*args, **kwargs)
    logger.info(f"Finishing {command_name} command")
    return result


@cli.command("db-migrate")
def run_migrations_command() -> None:
    """Run database migrations to upgrade to the latest schema.

    Executes all pending Alembic migrations to update the database schema
    to the latest version. This is typically used during application deployment.
    """
    asyncio.run(
        _log_command_execution_async("db-migrate", run_migrations, command_type="upgrade", revision="head")
    )


@cli.command("server")
def run_server_command() -> None:
    """Start the FastAPI server.

    Launches the HTTP server that serves the fastpubsub API endpoints.
    This is a long-running command that will continue until stopped.
    """
    # Server is a long-running command, so we only log the start
    logger.info("Starting server command")
    run_server(app)


@cli.command("cleanup_acked_messages")
def run_cleanup_acked_messages() -> None:
    """Remove acknowledged messages older than the configured threshold.

    Cleans up message history by removing messages that have been acknowledged
    and are older than the configured time threshold. Helps prevent database
    bloat and improve performance.
    """
    asyncio.run(
        _log_command_execution_async(
            "cleanup_acked_messages",
            cleanup_acked_messages,
            older_than_seconds=settings.cleanup_acked_messages_older_than_seconds,
        )
    )


@cli.command("cleanup_stuck_messages")
def run_cleanup_stuck_messages() -> None:
    """Unlock messages that have been locked for too long.

    Releases locks on messages that have been locked beyond the timeout period,
    making them available for consumption again. This helps recover from
    consumer failures or crashes.
    """
    asyncio.run(
        _log_command_execution_async(
            "cleanup_stuck_messages",
            cleanup_stuck_messages,
            lock_timeout_seconds=settings.cleanup_stuck_messages_lock_timeout_seconds,
        )
    )


@cli.command("generate_secret_key")
def run_generate_secret_key() -> None:
    """Generate a new random secret key for client authentication.

    Creates a cryptographically secure random string that can be used as
    a client secret for JWT token generation and validation.
    """
    secret = generate_secret()
    typer.echo(f"new_secret={secret}")


@cli.command("create_client")
def run_create_client(
    name: Annotated[str, typer.Argument(help="The client name.")],
    scopes: Annotated[str, typer.Argument(help="The client scopes.")] = "*",
    is_active: Annotated[bool, typer.Argument(help="The flag to enable or disable client.")] = True,
) -> None:
    """Create a new client with the specified name and scopes.

    Creates a new authorized client in the system that can access the
    pub/sub API endpoints based on their granted scopes.

    Args:
        name: Human-readable name for the client.
        scopes: Space-separated list of permissions/scopes granted to the client.
        is_active: Whether the client is initially active and can authenticate.
    """
    client_result = asyncio.run(
        create_client(data=CreateClient(name=name, scopes=scopes, is_active=is_active))
    )
    typer.echo(f"client_id={client_result.id}")
    typer.echo(f"client_secret={client_result.secret}")


if __name__ == "__main__":
    cli()
