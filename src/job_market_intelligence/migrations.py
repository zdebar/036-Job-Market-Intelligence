from .database import run_command


def main() -> None:
    run_command("migration", "db/migrations")
