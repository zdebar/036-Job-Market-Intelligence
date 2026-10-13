from pathlib import Path

from job_market_intelligence.processing.extraction import extract_hours
from job_market_intelligence.processing.sources.greenhouse import GreenhouseParser

PROJECT_ROOT = Path(__file__).parents[1]


def test_greenhouse_parser_normalizes_department_and_common_fields() -> None:
    parser = GreenhouseParser(PROJECT_ROOT)
    result = parser.parse(
        {
            "jobs": [
                {
                    "id": 123,
                    "title": "Senior Data Engineer",
                    "content": "Build data pipelines with Python and SQL.",
                    "departments": [{"name": "Software"}],
                    "location": {"name": "Prague, Czechia"},
                    "absolute_url": "https://example.test/jobs/123",
                }
            ]
        },
        {"company": "Mews"},
    )

    assert not result.errors
    record = result.records[0]
    assert record.company_name == "Mews"
    assert record.role_name == "Data Engineer"
    assert record.seniority_level_name == "Senior"
    assert record.departments == ("Engineering",)
    assert record.locations == ("Prague, Czechia",)
    assert {skill.name for skill in record.skill_requirements} == {"Python", "SQL"}


def test_extract_hours_normalizes_a_range() -> None:
    minimum, maximum, period = extract_hours("The role is 20-30 hours per week.")

    assert minimum == 20
    assert maximum == 30
    assert period == "week"
