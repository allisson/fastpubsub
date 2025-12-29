import typer

from fastpubsub.api import run_server
from fastpubsub.config import settings
from fastpubsub.database import run_migrations
from fastpubsub.services import cleanup_acked_messages, cleanup_stuck_messages

cli = typer.Typer()


@cli.command("db-migrate")
def run_migrations_command() -> None:
    run_migrations(command_type="upgrade", revision="head")


@cli.command("server")
def run_server_command() -> None:
    run_server()


@cli.command("cleanup_acked_messages")
def run_cleanup_acked_messages() -> None:
    cleanup_acked_messages(older_than_seconds=settings.cleanup_acked_messages_older_than_seconds)


@cli.command("cleanup_stuck_messages")
def run_cleanup_stuck_messages() -> None:
    cleanup_stuck_messages(lock_timeout_seconds=settings.cleanup_stuck_messages_lock_timeout_seconds)


if __name__ == "__main__":
    cli()
