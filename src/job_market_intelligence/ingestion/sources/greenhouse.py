"""Download published job posts from configured Greenhouse boards."""

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
    """Return enabled Greenhouse boards."""
    return [board for board in config["boards"] if board.get("enabled", True)]


def build_endpoint(config: dict[str, Any], board_token: str) -> str:
    """Build the public Greenhouse jobs endpoint."""
    base_url = config["api"]["base_url"].rstrip("/")
    return f"{base_url}/{board_token}/jobs"


def build_params(config: dict[str, Any]) -> dict[str, str]:
    """Build Greenhouse query parameters."""
    if config["api"].get("include_content", True):
        return {"content": "true"}
    return {}


def download(
    config_path: Path,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
) -> list[Path]:
    """Download and store one response for each enabled Greenhouse board."""
    config = load_toml(config_path)
    settings = load_toml(settings_path)
    source_id = config["source"]["id"]
    client = HttpClient(timeout=config["api"]["timeout_seconds"])
    boards = enabled_boards(config)
    if not boards:
        raise RuntimeError("No enabled Greenhouse boards are configured.")

    saved_paths: list[Path] = []
    for board in boards:
        company = board["company"]
        board_token = board["board_token"]
        source_key = board.get("source_key", source_id)
        endpoint = build_endpoint(config, board_token)
        params = build_params(config)

        try:
            response = client.get(endpoint, params=params)
            payload = response.json()
        except (RuntimeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Greenhouse request failed for {company}: {error}"
            ) from error

        record_count = (
            len(payload["jobs"])
            if isinstance(payload, dict) and isinstance(payload.get("jobs"), list)
            else None
        )
        saved_paths.append(
            save_raw_response(
                project_root=PROJECT_ROOT,
                storage_directory=config["storage"]["directory"],
                source_key=source_key,
                method="GET",
                endpoint=endpoint,
                response=response,
                request=params,
                record_count=record_count,
                extra_metadata={
                    "company": company,
                    "board_token": board_token,
                    "adapter_id": source_id,
                    "search_settings": settings.get("search", {}),
                },
            )
        )

    return saved_paths


def print_dry_run(
    config_path: Path,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
) -> None:
    """Print configured Greenhouse requests without network access."""
    config = load_toml(config_path)
    settings = load_toml(settings_path)
    params = build_params(config)
    print(f"Base URL: {config['api']['base_url']}")
    print("API key: not required for public GET endpoints")
    print("Shared search settings:")
    print(json.dumps(settings.get("search", {}), ensure_ascii=False, indent=2))
    for board in enabled_boards(config):
        print(f"{board['source_key']}: {build_endpoint(config, board['board_token'])}")
        print(json.dumps(params, ensure_ascii=False, indent=2))
