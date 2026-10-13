"""Configuration-backed deterministic normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from job_market_intelligence.processing.aliases import AliasDictionary


@dataclass(frozen=True)
class NormalizationDictionaries:
    """All alias dictionaries used by source adapters."""

    companies: AliasDictionary
    roles: AliasDictionary
    departments: AliasDictionary
    skills: AliasDictionary
    seniority_levels: AliasDictionary
    proficiency_levels: AliasDictionary
    requirement_types: AliasDictionary
    work_modes: AliasDictionary
    locations: AliasDictionary
    employment_relations: AliasDictionary
    workloads: AliasDictionary

    @classmethod
    def from_project_root(cls, project_root: Path) -> NormalizationDictionaries:
        directory = project_root / "config" / "normalization"

        def load(name: str) -> AliasDictionary:
            return AliasDictionary.from_file(directory / f"{name}.toml", name)

        return cls(
            companies=load("companies"),
            roles=load("roles"),
            departments=load("departments"),
            skills=load("skills"),
            seniority_levels=load("seniority_levels"),
            proficiency_levels=load("proficiency_levels"),
            requirement_types=load("requirement_types"),
            work_modes=load("work_modes"),
            locations=load("locations"),
            employment_relations=load("employment_relations"),
            workloads=load("workloads"),
        )
