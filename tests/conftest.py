"""Shared test fixtures for the project-cars test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """Path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def fipe_fixtures_dir(fixtures_dir):
    """Path to FIPE-specific fixtures."""
    return fixtures_dir / "fipe"


def load_fixture(path: Path) -> dict | list:
    """Load a JSON fixture file."""
    return json.loads(path.read_text())


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create a temporary config directory with valid config files.

    Returns the tmp_path so tests can override individual files.
    """
    buyer = {
        "budget": {"min": 60000, "max": 90000},
        "vehicle": {
            "max_age_years": 5,
            "max_mileage_km": 80000,
            "categories": ["hatch", "sedan", "suv", "crossover"],
            "fuel_types": ["flex", "hybrid"],
        },
        "use_case": "city_highway_mix",
    }
    scoring = {
        "weights": {
            "depreciation": 0.20,
            "maintenance_cost": 0.15,
            "owner_satisfaction": 0.15,
            "safety": 0.15,
            "fuel_efficiency": 0.10,
            "theft_risk": 0.10,
            "resale_liquidity": 0.10,
            "price_vs_fipe": 0.05,
        },
        "missing_data_strategy": "median",
    }
    sources = {
        "fipe": {
            "parallelum_v2": "https://parallelum.com.br/fipe/api/v2",
            "parallelum_v1": "https://parallelum.com.br/fipe/api/v1",
            "brasil_api": "https://brasilapi.com.br/api/fipe",
            "rate_limit": {"parallelum_requests_per_day": 500, "request_delay_seconds": 0.5},
        },
        "latin_ncap": {
            "results_endpoint": "https://www.latinncap.com/get_res.php",
            "detail_url": "https://www.latinncap.com/en/result/{id}/{slug}",
            "rate_limit": {"request_delay_seconds": 1.0},
        },
        "carros_na_web": {
            "base_url": "https://www.carrosnaweb.com.br",
            "analysis_path": "/analise.asp?codigo={codigo}",
            "owner_opinions_path": "/opiniaolista.asp?fabricante={brand}&modelo={model}",
            "theft_stats_path": "/roubadosestatistica.asp",
            "rate_limit": {"request_delay_seconds": 1.0},
        },
        "carroclub": {
            "base_url": "https://www.carroclub.com.br",
            "opinions_path": "/carros/{brand}/{model}/opiniao-do-dono/",
            "rate_limit": {"request_delay_seconds": 1.0},
        },
        "inmetro_pbev": {
            "pdf_urls": {
                "2025": "https://example.com/2025.pdf",
                "2024": "https://example.com/2024.pdf",
            },
        },
    }

    for name, data in [
        ("buyer-profile.yaml", buyer),
        ("scoring-weights.yaml", scoring),
        ("sources.yaml", sources),
    ]:
        (tmp_path / name).write_text(yaml.dump(data))

    return tmp_path
