import sys

from job_market_intelligence.processing.runner import parse_args


def test_parse_args_supports_reprocessing_processed_runs(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["job-market-parse", "--reprocess-processed"],
    )

    args = parse_args()

    assert args.reprocess_processed is True
