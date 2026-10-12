from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_CHANGELOG_LOCK = 360_360_036
MIGRATION_FILENAME_PATTERN = re.compile(r"^\d+_[a-z0-9][a-z0-9_-]*\.sql$")

CREATE_CHANGELOG_TABLE = """
CREATE TABLE IF NOT EXISTS database_changelog (
    kind TEXT NOT NULL CHECK (kind IN ('migration', 'seed')),
    filename TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (kind, filename)
)
"""


def _database_url() -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and configure it."
        )
    return database_url


def _sql_files(directory: Path) -> list[Path]:
    files = sorted(directory.glob("*.sql"))
    invalid_files = [
        path.name
        for path in files
        if not MIGRATION_FILENAME_PATTERN.fullmatch(path.name)
    ]
    if invalid_files:
        names = ", ".join(invalid_files)
        raise RuntimeError(f"Invalid SQL filename(s): {names}")
    return files


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _applied_files(connection: psycopg.Connection, kind: str) -> dict[str, str]:
    rows = connection.execute(
        """
        SELECT filename, checksum
        FROM database_changelog
        WHERE kind = %s
        """,
        (kind,),
    ).fetchall()
    return dict(rows)


def run_sql_files(kind: str, relative_directory: str) -> None:
    directory = (PROJECT_ROOT / relative_directory).resolve()
    files = _sql_files(directory)
    if not files:
        print(f"No SQL files found in {directory}")
        return

    with psycopg.connect(_database_url()) as connection:
        connection.execute(
            "SELECT pg_advisory_lock(%s)",
            (DATABASE_CHANGELOG_LOCK,),
        )
        connection.commit()

        try:
            with connection.transaction():
                connection.execute(CREATE_CHANGELOG_TABLE, prepare=False)

            applied = _applied_files(connection, kind)
            connection.commit()

            for path in files:
                checksum = _checksum(path)
                previous_checksum = applied.get(path.name)

                if previous_checksum is not None:
                    if previous_checksum != checksum:
                        raise RuntimeError(
                            f"Applied {kind} changed: {path.name}. "
                            "Create a new SQL file instead of editing it."
                        )
                    print(f"Skipping {kind}: {path.name}")
                    continue

                sql = path.read_text(encoding="utf-8").strip()
                if not sql:
                    raise RuntimeError(f"SQL file is empty: {path.name}")

                print(f"Applying {kind}: {path.name}")
                with connection.transaction():
                    # Migration/seed files must not contain BEGIN/COMMIT;
                    # the runner controls the transaction boundary.
                    # Bytes are accepted by Psycopg for runtime SQL text and
                    # avoid requiring a LiteralString type for file content.
                    connection.execute(sql.encode("utf-8"), prepare=False)
                    connection.execute(
                        """
                        INSERT INTO database_changelog (kind, filename, checksum)
                        VALUES (%s, %s, %s)
                        """,
                        (kind, path.name, checksum),
                    )
                applied[path.name] = checksum

            print(f"{kind.capitalize()} processing complete.")
        finally:
            connection.execute(
                "SELECT pg_advisory_unlock(%s)",
                (DATABASE_CHANGELOG_LOCK,),
            )
            connection.commit()


def run_command(kind: str, relative_directory: str) -> None:
    try:
        run_sql_files(kind, relative_directory)
    except Exception as error:
        print(f"Database {kind} failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
