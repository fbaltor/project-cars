"""Load and validate YAML configuration using Pydantic.

All config lives in config/*.yaml — never hardcode values that could vary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, model_validator

from src.errors import ConfigError

CONFIG_DIR = Path("config")


class BudgetConfig(BaseModel):
    min: int
    max: int


class VehicleConfig(BaseModel):
    max_age_years: int
    max_mileage_km: int
    categories: list[str]
    fuel_types: list[str]


class BuyerProfile(BaseModel):
    budget: BudgetConfig
    vehicle: VehicleConfig
    use_case: str


class ScoringWeights(BaseModel):
    weights: dict[str, float]
    missing_data_strategy: str = "median"

    @model_validator(mode="after")
    def validate_weights_sum(self) -> ScoringWeights:
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            msg = f"Scoring weights must sum to 1.0, got {total:.4f}"
            raise ValueError(msg)
        return self


class RateLimitConfig(BaseModel, extra="allow"):
    request_delay_seconds: float = 1.0


class FipeSourceConfig(BaseModel):
    parallelum_v2: str
    parallelum_v1: str
    brasil_api: str
    rate_limit: RateLimitConfig


class LatinNcapSourceConfig(BaseModel):
    results_endpoint: str
    detail_url: str
    rate_limit: RateLimitConfig


class CarrosNaWebSourceConfig(BaseModel):
    base_url: str
    analysis_path: str
    owner_opinions_path: str
    theft_stats_path: str
    rate_limit: RateLimitConfig


class CarroClubSourceConfig(BaseModel):
    base_url: str
    opinions_path: str
    rate_limit: RateLimitConfig


class InmetroPbevSourceConfig(BaseModel):
    pdf_urls: dict[int | str, str]


class SourcesConfig(BaseModel):
    fipe: FipeSourceConfig
    latin_ncap: LatinNcapSourceConfig
    carros_na_web: CarrosNaWebSourceConfig
    carroclub: CarroClubSourceConfig
    inmetro_pbev: InmetroPbevSourceConfig


class AppConfig(BaseModel):
    """All application configuration bundled together."""

    buyer: BuyerProfile
    scoring: ScoringWeights
    sources: SourcesConfig


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(
            f"Config file not found: {path}",
            suggestions=[f"Create {path} or check the config/ directory"],
        )
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(
            f"Config file is not a YAML mapping: {path}",
            suggestions=[f"Verify the format of {path}"],
        )
    return data


def load_config(
    *,
    buyer_path: Path | None = None,
    scoring_path: Path | None = None,
    sources_path: Path | None = None,
) -> AppConfig:
    """Load all config files and return a validated AppConfig.

    Path overrides are primarily for testing.
    """
    buyer = BuyerProfile(**_load_yaml(buyer_path or CONFIG_DIR / "buyer-profile.yaml"))
    scoring = ScoringWeights(**_load_yaml(scoring_path or CONFIG_DIR / "scoring-weights.yaml"))
    sources = SourcesConfig(**_load_yaml(sources_path or CONFIG_DIR / "sources.yaml"))
    return AppConfig(buyer=buyer, scoring=scoring, sources=sources)
