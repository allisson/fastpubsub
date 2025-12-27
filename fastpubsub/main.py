import typer

from fastpubsub.database import run_migrations

cli = typer.Typer()


@cli.command("db-migrate")
def run_migrations_command() -> None:
    return run_migrations(command_type="upgrade", revision="head")


if __name__ == "__main__":
    cli()
