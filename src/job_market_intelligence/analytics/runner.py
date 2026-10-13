"""Run SQL reports and data-quality checks against PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT_DIRECTORY = PROJECT_ROOT / "sql" / "reports"
DEFAULT_QUALITY_DIRECTORY = PROJECT_ROOT / "sql" / "quality"


@dataclass
class SqlSummary:
    """Execution summary for a group of SQL files."""

    discovered: int = 0
    succeeded: int = 0
    failed: int = 0


def discover_sql_files(directory: Path) -> list[Path]:
    """Return SQL files in deterministic filename order."""
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.sql") if path.is_file())


def run_sql_files(
    sql_directory: Path,
    selected_files: list[str] | None = None,
) -> SqlSummary:
    """Execute selected SQL files and return an execution summary."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    discovered = discover_sql_files(sql_directory)
    if not discovered:
        raise RuntimeError(f"No SQL files found in {sql_directory}.")

    files = _select_files(discovered, selected_files)
    summary = SqlSummary(discovered=len(files))

    with psycopg.connect(database_url) as connection:
        for sql_path in files:
            _run_sql_file(connection, sql_path, summary)

    return summary


def _select_files(
    discovered: list[Path], selected_files: list[str] | None
) -> list[Path]:
    if not selected_files:
        return discovered

    by_name = {path.name: path for path in discovered}
    missing = [name for name in selected_files if name not in by_name]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"SQL file(s) not found: {names}")
    return [by_name[name] for name in selected_files]


def _run_sql_file(
    connection: psycopg.Connection,
    sql_path: Path,
    summary: SqlSummary,
) -> None:
    try:
        sql = sql_path.read_bytes()
        with connection.transaction():
            result = connection.execute(sql, prepare=False)
            _print_result(result)
    except (OSError, psycopg.Error) as error:
        summary.failed += 1
        print(f"[FAIL] {sql_path.name}: {error}", file=sys.stderr)
        return

    summary.succeeded += 1
    print(f"[PASS] {sql_path.name}")


def _print_result(result: psycopg.Cursor) -> None:
    if result.description is None:
        return

    columns = [column.name for column in result.description]
    print(" | ".join(columns))
    for row in result.fetchall():
        print(" | ".join(str(value) for value in row))


def _parse_args(default_directory: Path, description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--directory",
        type=Path,
        default=default_directory,
        help="Directory containing SQL files.",
    )
    parser.add_argument(
        "--file",
        action="append",
        dest="selected_files",
        help="Run only this filename; repeat the option to select more files.",
    )
    return parser.parse_args()


def _main(default_directory: Path, description: str) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    args = _parse_args(default_directory, description)
    try:
        summary = run_sql_files(args.directory, args.selected_files)
    except (OSError, RuntimeError, ValueError, psycopg.Error) as error:
        print(f"SQL execution failed: {error}", file=sys.stderr)
        return 1

    print(
        "SQL processing complete: "
        f"{summary.succeeded}/{summary.discovered} succeeded, "
        f"{summary.failed} failed."
    )
    return 1 if summary.failed else 0


def report_main() -> int:
    """CLI entry point for analytical reports."""
    return _main(DEFAULT_REPORT_DIRECTORY, "Run SQL analytical reports.")


def quality_main() -> int:
    """CLI entry point for SQL data-quality checks."""
    return _main(DEFAULT_QUALITY_DIRECTORY, "Run SQL data-quality checks.")
