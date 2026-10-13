"""Deterministic content fingerprints for normalized advertisements."""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_text(value: str | None) -> str:
    """Convert HTML or plain text into normalized text."""
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip().casefold()


def content_fingerprint(value: str | None) -> str | None:
    """Return a SHA-256 fingerprint, or ``None`` for empty content."""
    normalized = plain_text(value)
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
