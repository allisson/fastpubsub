import typer

from fastpubsub.api import run_server
from fastpubsub.database import run_migrations

cli = typer.Typer()


@cli.command("db-migrate")
def run_migrations_command() -> None:
    return run_migrations(command_type="upgrade", revision="head")


@cli.command("server")
def run_server_command() -> None:
    return run_server()


if __name__ == "__main__":
    cli()
