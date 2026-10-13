"""Process stored raw responses into normalized database records."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

import psycopg
from dotenv import load_dotenv

from job_market_intelligence.ingestion.config import load_toml, resolve_project_path
from job_market_intelligence.processing.database import ProcessingRepository, utc_now
from job_market_intelligence.processing.models import ParseResult, RecordError
from job_market_intelligence.processing.sources.ashby import AshbyParser
from job_market_intelligence.processing.sources.greenhouse import GreenhouseParser
from job_market_intelligence.processing.sources.lever import LeverParser
from job_market_intelligence.processing.utils import optional_text, parse_datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "ingestion.toml"


class Parser(Protocol):
    def parse(
        self, payload: Mapping[str, Any] | list[Any], metadata: Mapping[str, Any]
    ) -> ParseResult:
        """Parse one raw provider payload."""
        ...


WorkItem = tuple[str, Path]


PARSER_TYPES = {
    "greenhouse": GreenhouseParser,
    "lever": LeverParser,
    "ashby": AshbyParser,
}


def discover_raw_runs(storage_directory: Path) -> list[Path]:
    """Find complete raw run directories below a storage directory."""
    if not storage_directory.exists():
        return []
    return sorted(
        {
            metadata_path.parent
            for metadata_path in storage_directory.rglob("metadata.json")
            if (metadata_path.parent / "response.json").exists()
        }
    )


def run_processing(
    config_path: Path,
    selected_sources: list[str] | None = None,
    dry_run: bool = False,
    reprocess_processed: bool = False,
) -> int:
    """Process configured raw runs and return the number of processed runs."""
    runner_config = load_toml(config_path)
    selected_ids = set(selected_sources or [])
    source_entries = runner_config.get("sources", [])
    if not isinstance(source_entries, list):
        raise TypeError("The ingestion configuration must contain a sources list")
    _validate_source_selection(source_entries, selected_ids)
    work_items = _discover_work_items(source_entries, selected_ids)

    print(f"Discovered {len(work_items)} raw run(s).")
    if dry_run:
        for source_id, run_directory in work_items:
            print(f"[{source_id}] {run_directory}")
        return 0

    return _process_work_items(work_items, reprocess_processed)


def _validate_source_selection(
    source_entries: list[dict[str, Any]],
    selected_ids: set[str],
) -> None:
    configured_ids = {str(entry["id"]) for entry in source_entries}
    unknown = selected_ids - configured_ids
    if unknown:
        raise ValueError(
            f"Source is not present in ingestion configuration: {', '.join(sorted(unknown))}"
        )


def _discover_work_items(
    source_entries: list[dict[str, Any]],
    selected_ids: set[str],
) -> list[WorkItem]:
    work_items: list[WorkItem] = []
    for source_entry in source_entries:
        if _should_collect_source(source_entry, selected_ids):
            work_items.extend(_discover_source_work_items(source_entry))
    return work_items


def _should_collect_source(
    source_entry: dict[str, Any],
    selected_ids: set[str],
) -> bool:
    source_id = str(source_entry["id"])
    if selected_ids and source_id not in selected_ids:
        return False
    if not source_entry.get("enabled", True):
        print(f"Skipped disabled source: {source_id}")
        return False
    return True


def _discover_source_work_items(source_entry: dict[str, Any]) -> list[WorkItem]:
    source_id = str(source_entry["id"])
    source_config_path = resolve_project_path(
        PROJECT_ROOT, str(source_entry["config_path"])
    )
    source_config = load_toml(source_config_path)
    source_settings = source_config.get("source", {})
    storage = source_config.get("storage", {})
    source_keys = _enabled_source_keys(source_config.get("boards", []))
    storage_directory = resolve_project_path(
        PROJECT_ROOT, str(storage.get("directory", "data/01_bronze"))
    )
    configured_source_id = str(source_settings.get("id", source_id))
    return [
        (configured_source_id, run_directory)
        for source_key in source_keys
        for run_directory in discover_raw_runs(storage_directory / source_key)
    ]


def _enabled_source_keys(boards: Any) -> list[str]:
    if not isinstance(boards, list):
        return []
    return [
        str(board["source_key"])
        for board in boards
        if isinstance(board, dict) and board.get("enabled", True)
    ]


def _process_work_items(
    work_items: list[WorkItem],
    reprocess_processed: bool,
) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    processed_count = 0
    parser_cache: dict[str, Parser] = {}
    with psycopg.connect(database_url) as connection:
        repository = ProcessingRepository(connection)
        for source_id, run_directory in work_items:
            parser = _get_parser(parser_cache, source_id)
            if _process_run(repository, parser, run_directory, reprocess_processed):
                processed_count += 1
    return processed_count


def _get_parser(parser_cache: dict[str, Parser], source_id: str) -> Parser:
    parser = parser_cache.get(source_id)
    if parser is None:
        parser = PARSER_TYPES[source_id](PROJECT_ROOT)
        parser_cache[source_id] = parser
    return parser


def _process_run(
    repository: ProcessingRepository,
    parser: Parser,
    run_directory: Path,
    reprocess_processed: bool,
) -> bool:
    metadata = _read_json(run_directory / "metadata.json")
    payload = _read_json(run_directory / "response.json")
    source_key = optional_text(metadata.get("source_key") or metadata.get("source_id"))
    run_id = optional_text(metadata.get("run_id"))
    if not source_key or not run_id:
        raise ValueError(
            f"Raw run metadata is missing source_key or run_id: {run_directory}"
        )

    retrieved_at = parse_datetime(metadata.get("retrieved_at")) or utc_now()
    raw_path = str(run_directory.relative_to(PROJECT_ROOT))
    database_run_id, status = repository.register_raw_run(
        source_key=source_key,
        run_id=run_id,
        raw_path=raw_path,
        retrieved_at=retrieved_at,
        record_count=_integer(metadata.get("record_count")),
        payload_sha256=optional_text(metadata.get("payload_sha256")),
    )
    repository.connection.commit()
    if status == "processed" and not reprocess_processed:
        print(f"[{source_key}] Skipping processed run {run_id}")
        return False
    if status == "processed":
        print(f"[{source_key}] Reprocessing processed run {run_id}")

    repository.mark_processing(database_run_id)
    repository.connection.commit()
    try:
        parser_metadata = _flatten_context(metadata)
        result = parser.parse(payload, parser_metadata)
        for parse_error in result.errors:
            with repository.connection.transaction():
                repository.record_error(database_run_id, parse_error)

        processed_records = 0
        for record in result.records:
            try:
                with repository.connection.transaction():
                    repository.upsert_job_posting(
                        source_key=source_key,
                        record=record,
                        retrieved_at=retrieved_at,
                    )
                processed_records += 1
            except Exception as error:  # noqa: BLE001 - persist and continue per record
                record_error = RecordError(
                    source_job_id=record.source_job_id,
                    stage="persistence",
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
                with repository.connection.transaction():
                    repository.record_error(database_run_id, record_error)

        with repository.connection.transaction():
            if result.errors or processed_records != len(result.records):
                repository.mark_partial(database_run_id, processed_records)
            else:
                repository.mark_processed(database_run_id, processed_records)
                repository.mark_missing_postings_inactive(
                    source_key=source_key,
                    retrieved_at=retrieved_at,
                )
        print(
            f"[{source_key}] {run_id}: {processed_records}/{len(result.records)} "
            f"record(s) persisted"
        )
        return True
    except Exception as error:
        repository.connection.rollback()
        with repository.connection.transaction():
            repository.mark_failed(database_run_id, str(error))
        raise


def _flatten_context(metadata: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(metadata)
    context = metadata.get("context")
    if isinstance(context, Mapping):
        for key, value in context.items():
            result.setdefault(str(key), value)
    return result


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def _integer(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the ingestion runner TOML configuration.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="selected_sources",
        help="Process only this configured source; may be repeated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List discovered raw runs without connecting to PostgreSQL.",
    )
    parser.add_argument(
        "--reprocess-processed",
        action="store_true",
        help="Reprocess runs already marked as processed, for example after a processing change.",
    )
    return parser.parse_args()


def main() -> int:
    """Process stored raw responses."""
    args = parse_args()
    try:
        run_processing(
            args.config,
            selected_sources=args.selected_sources,
            dry_run=args.dry_run,
            reprocess_processed=args.reprocess_processed,
        )
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(f"Processing failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
