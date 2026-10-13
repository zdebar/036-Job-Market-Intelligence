import hashlib
import json
from pathlib import Path

from job_market_intelligence.ingestion.http_client import HttpResponse
from job_market_intelligence.ingestion.runner import run_ingestion
from job_market_intelligence.ingestion.storage import save_raw_response

PROJECT_ROOT = Path(__file__).parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "ingestion.toml"


def test_runner_dry_run_reads_greenhouse_configuration(capsys) -> None:
    saved_paths = run_ingestion(CONFIG_PATH, dry_run=True)

    assert saved_paths == []
    output = capsys.readouterr().out
    assert "Source: greenhouse" in output
    assert "greenhouse_mews" in output


def test_save_raw_response_writes_documented_layout(tmp_path) -> None:
    payload = b'{"jobs":[]}'
    response = HttpResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        content=payload,
    )

    response_path = save_raw_response(
        project_root=tmp_path,
        storage_directory="data/01_bronze",
        source_key="greenhouse_mews",
        method="GET",
        endpoint="https://example.test/jobs",
        response=response,
        request={"content": "true"},
        record_count=0,
    )

    metadata = json.loads(response_path.with_name("metadata.json").read_text())

    assert response_path.read_bytes() == payload
    assert response_path.parent.parent.parent.name == "greenhouse_mews"
    assert metadata["run_id"] == response_path.parent.name
    assert metadata["source_key"] == "greenhouse_mews"
    assert metadata["payload_sha256"] == hashlib.sha256(payload).hexdigest()
    assert metadata["payload_size_bytes"] == len(payload)
    assert metadata["record_count"] == 0
