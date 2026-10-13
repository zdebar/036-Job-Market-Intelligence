"""Download published job posts from configured Ashby boards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from job_market_intelligence.ingestion.config import load_toml
from job_market_intelligence.ingestion.http_client import HttpClient
from job_market_intelligence.ingestion.storage import save_raw_response

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.toml"


def enabled_boards(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Return enabled Ashby boards."""
    return [board for board in config["boards"] if board.get("enabled", True)]


def build_endpoint(config: dict[str, Any], board_name: str) -> str:
    """Build the public Ashby job-board endpoint."""
    return f"{config['api']['base_url'].rstrip('/')}/{board_name}"


def build_params(config: dict[str, Any]) -> dict[str, str]:
    """Build the Ashby public API parameters."""
    if config["api"].get("include_compensation", False):
        return {"includeCompensation": "true"}
    return {}


def record_count(payload: Any) -> int | None:
    """Return the number of jobs in an Ashby response when available."""
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return len(payload["jobs"])
    return None


def download(
    config_path: Path,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
) -> list[Path]:
    """Download and store one response for each enabled Ashby board."""
    del settings_path
    config = load_toml(config_path)
    source_id = config["source"]["id"]
    client = HttpClient(timeout=config["api"]["timeout_seconds"])
    boards = enabled_boards(config)
    if not boards:
        raise RuntimeError("No enabled Ashby boards are configured.")

    saved_paths: list[Path] = []
    for board in boards:
        company = board["company"]
        board_name = board["board_name"]
        source_key = board.get("source_key", source_id)
        endpoint = build_endpoint(config, board_name)
        params = build_params(config)
        try:
            response = client.get(endpoint, params=params)
            payload = response.json()
        except (RuntimeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Ashby request failed for {company}: {error}"
            ) from error

        saved_paths.append(
            save_raw_response(
                project_root=PROJECT_ROOT,
                storage_directory=config["storage"]["directory"],
                source_key=source_key,
                method="GET",
                endpoint=endpoint,
                response=response,
                request=params,
                record_count=record_count(payload),
                extra_metadata={
                    "company": company,
                    "board_name": board_name,
                    "adapter_id": source_id,
                },
            )
        )

    return saved_paths


def print_dry_run(
    config_path: Path,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
) -> None:
    """Print configured Ashby requests without network access."""
    del settings_path
    config = load_toml(config_path)
    print(f"Base URL: {config['api']['base_url']}")
    print("API key: not required for public GET endpoints")
    for board in enabled_boards(config):
        print(f"{board['source_key']}: {build_endpoint(config, board['board_name'])}")
        print(json.dumps(build_params(config), indent=2))
