from pathlib import Path

from job_market_intelligence.analytics.runner import discover_sql_files


def test_sql_files_are_discovered_in_sorted_order(tmp_path: Path) -> None:
    sql_directory = tmp_path / "sql"
    sql_directory.mkdir()
    (sql_directory / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (sql_directory / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (sql_directory / "README.md").write_text("Documentation", encoding="utf-8")

    assert discover_sql_files(sql_directory) == [
        sql_directory / "001_first.sql",
        sql_directory / "002_second.sql",
    ]
