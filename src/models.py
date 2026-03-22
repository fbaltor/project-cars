"""Pydantic data models for all domain entities.

Collectors return these typed models — never raw dicts.
The DB layer accepts and returns these models for persistence.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VehicleModel(BaseModel):
    """A car model identified in FIPE, keyed on brand+model."""

    brand: str
    model: str
    category: str  # hatch, sedan, suv, crossover
    fipe_code: str

    created_at: datetime | None = None
    updated_at: datetime | None = None


class FipePrice(BaseModel):
    """FIPE table price for a specific model/year/month/fuel combination."""

    fipe_code: str
    year: int
    price_brl: float
    reference_month: str  # e.g. "2026-03"
    fuel_type: str  # flex, gasoline, diesel, hybrid

    created_at: datetime | None = None
    updated_at: datetime | None = None


class DepreciationCurve(BaseModel):
    """Price trajectory over time, derived from multiple FipePrice records."""

    brand: str
    model: str
    year: int
    prices: list[FipePrice] = Field(default_factory=list)
    annual_depreciation_pct: float | None = None


class SafetyRating(BaseModel):
    """Latin NCAP or equivalent safety test results."""

    brand: str
    model: str
    protocol: str  # e.g. "latin_ncap_2024"
    stars: int = Field(ge=0, le=5)
    adult_pct: float | None = None
    child_pct: float | None = None
    pedestrian_pct: float | None = None
    safety_assist_pct: float | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class FuelEfficiency(BaseModel):
    """Inmetro PBEV fuel efficiency data."""

    brand: str
    model: str
    version: str
    city_kml: float  # km/L in city
    highway_kml: float  # km/L on highway
    rating: str  # A, B, C, D, E

    created_at: datetime | None = None
    updated_at: datetime | None = None


class MaintenanceCost(BaseModel):
    """Scheduled maintenance cost at a given interval."""

    brand: str
    model: str
    interval_km: int
    cost_brl: float

    created_at: datetime | None = None
    updated_at: datetime | None = None


class OwnerRating(BaseModel):
    """Aggregated owner satisfaction ratings from a given source."""

    brand: str
    model: str
    source: str  # carros_na_web, carroclub
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    overall: float
    review_count: int

    created_at: datetime | None = None
    updated_at: datetime | None = None


class TheftIndex(BaseModel):
    """Theft/robbery index for a model."""

    brand: str
    model: str
    index_value: float

    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelScore(BaseModel):
    """Computed score for a candidate model across all dimensions."""

    brand: str
    model: str
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    weighted_total: float
    rank: int

    created_at: datetime | None = None
    updated_at: datetime | None = None
