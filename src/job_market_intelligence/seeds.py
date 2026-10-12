from .database import run_command


def main() -> None:
    run_command("seed", "db/seeds")
