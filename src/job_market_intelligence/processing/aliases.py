"""Alias dictionaries used by deterministic normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from job_market_intelligence.ingestion.config import load_toml


@dataclass(frozen=True)
class AliasRule:
    """A canonical value and the provider labels mapped to it."""

    canonical_name: str
    aliases: tuple[str, ...]


class AliasDictionary:
    """Find canonical values in free text using word-boundary patterns."""

    def __init__(self, rules: tuple[AliasRule, ...]) -> None:
        patterns: list[tuple[str, re.Pattern[str]]] = []
        for rule in rules:
            for alias in sorted(rule.aliases, key=len, reverse=True):
                if alias:
                    patterns.append(
                        (
                            rule.canonical_name,
                            re.compile(
                                rf"(?<!\w){re.escape(alias)}(?!\w)",
                                flags=re.IGNORECASE,
                            ),
                        )
                    )
        self._patterns = tuple(patterns)

    @classmethod
    def from_file(cls, path: Path, section: str) -> AliasDictionary:
        """Load alias rules from a TOML array-of-tables section."""
        config = load_toml(path)
        values = config.get(section)
        if not isinstance(values, list):
            raise TypeError(f"Expected a TOML array named '{section}' in {path}")

        rules = tuple(
            AliasRule(
                canonical_name=str(item["name"]),
                aliases=tuple(
                    str(alias) for alias in item.get("aliases", [item["name"]])
                ),
            )
            for item in values
        )
        return cls(rules)

    def find_all(self, text: str) -> tuple[str, ...]:
        """Return distinct canonical values in source-text order."""
        matches: list[tuple[int, str]] = []
        for canonical_name, pattern in self._patterns:
            matches.extend(
                (match.start(), canonical_name) for match in pattern.finditer(text)
            )
        matches.sort(key=lambda item: item[0])
        return tuple(dict.fromkeys(value for _, value in matches))

    def find_non_overlapping(self, text: str) -> tuple[str, ...]:
        """Return matches while preferring longer aliases at each position."""
        candidates: list[tuple[int, int, str]] = []
        for canonical_name, pattern in self._patterns:
            candidates.extend(
                (match.start(), match.end(), canonical_name)
                for match in pattern.finditer(text)
            )

        selected: list[tuple[int, int, str]] = []
        for candidate in sorted(
            candidates,
            key=lambda item: (item[0], -(item[1] - item[0]), item[2]),
        ):
            if any(
                candidate[0] < existing[1] and existing[0] < candidate[1]
                for existing in selected
            ):
                continue
            selected.append(candidate)

        selected.sort(key=lambda item: item[0])
        return tuple(dict.fromkeys(item[2] for item in selected))

    def find_first(self, text: str) -> str | None:
        """Return the first matching canonical value."""
        matches: list[tuple[int, int, str]] = []
        for canonical_name, pattern in self._patterns:
            matches.extend(
                (match.start(), match.end(), canonical_name)
                for match in pattern.finditer(text)
            )
        if not matches:
            return None
        return min(matches, key=lambda item: (item[0], -(item[1] - item[0])))[2]
