import typer

from fastpubsub.api import run_server
from fastpubsub.config import settings
from fastpubsub.database import run_migrations
from fastpubsub.logger import get_logger
from fastpubsub.services import cleanup_acked_messages, cleanup_stuck_messages

logger = get_logger(__name__)
cli = typer.Typer()


def _log_command_execution(command_name: str, func, *args, **kwargs):
    """Helper to log command execution with start and finish messages."""
    logger.info(f"Starting {command_name} command")
    result = func(*args, **kwargs)
    logger.info(f"Finishing {command_name} command")
    return result


@cli.command("db-migrate")
def run_migrations_command() -> None:
    # Return value is ignored as run_migrations has no meaningful return value
    _log_command_execution("db-migrate", run_migrations, command_type="upgrade", revision="head")


@cli.command("server")
def run_server_command() -> None:
    # Server is a long-running command, so we only log the start
    logger.info("Starting server command")
    run_server()


@cli.command("cleanup_acked_messages")
def run_cleanup_acked_messages() -> None:
    _log_command_execution(
        "cleanup_acked_messages",
        cleanup_acked_messages,
        older_than_seconds=settings.cleanup_acked_messages_older_than_seconds,
    )


@cli.command("cleanup_stuck_messages")
def run_cleanup_stuck_messages() -> None:
    _log_command_execution(
        "cleanup_stuck_messages",
        cleanup_stuck_messages,
        lock_timeout_seconds=settings.cleanup_stuck_messages_lock_timeout_seconds,
    )


if __name__ == "__main__":
    cli()
