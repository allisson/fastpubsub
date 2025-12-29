import typer

from fastpubsub.api import run_server
from fastpubsub.config import settings
from fastpubsub.database import run_migrations
from fastpubsub.logger import get_logger
from fastpubsub.services import cleanup_acked_messages, cleanup_stuck_messages

logger = get_logger(__name__)
cli = typer.Typer()


@cli.command("db-migrate")
def run_migrations_command() -> None:
    logger.info("Starting db-migrate command")
    run_migrations(command_type="upgrade", revision="head")
    logger.info("Finishing db-migrate command")


@cli.command("server")
def run_server_command() -> None:
    logger.info("Starting server command")
    run_server()


@cli.command("cleanup_acked_messages")
def run_cleanup_acked_messages() -> None:
    logger.info("Starting cleanup_acked_messages command")
    cleanup_acked_messages(older_than_seconds=settings.cleanup_acked_messages_older_than_seconds)
    logger.info("Finishing cleanup_acked_messages command")


@cli.command("cleanup_stuck_messages")
def run_cleanup_stuck_messages() -> None:
    logger.info("Starting cleanup_stuck_messages command")
    cleanup_stuck_messages(lock_timeout_seconds=settings.cleanup_stuck_messages_lock_timeout_seconds)
    logger.info("Finishing cleanup_stuck_messages command")


if __name__ == "__main__":
    cli()
