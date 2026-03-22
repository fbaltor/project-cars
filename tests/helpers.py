"""Shared test helpers — HTTP mocking patterns, data builders, etc."""

from __future__ import annotations

import json
from pathlib import Path

import httpx


def fixture_response(fixture_path: Path, status_code: int = 200) -> httpx.Response:
    """Build a mock httpx.Response from a fixture file."""
    content = fixture_path.read_bytes()
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={"content-type": "application/json"},
    )


def load_json_fixture(fixture_path: Path) -> dict | list:
    """Load and parse a JSON fixture file."""
    return json.loads(fixture_path.read_text())
