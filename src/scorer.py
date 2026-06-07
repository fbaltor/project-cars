"""Scoring & ranking engine.

Reads dimension data (already fetched from the DB as plain row dicts), computes a
normalised per-dimension score in [0.0, 1.0] for each candidate, combines them into
a ``weighted_total`` using the configured weights, and returns a ranked list of
``ModelScore`` objects.

Design notes:

* Dimension rows are joined to candidates by a case-insensitive ``(brand, model)`` key.
* Each dimension produces a *raw* value per candidate (or ``None`` when no data exists).
  Raw values are min-max normalised across all candidates so that the best candidate in
  a dimension scores ``1.0`` and the worst ``0.0``. For "lower is better" dimensions the
  scale is inverted.
* Missing raw values follow ``ScoringWeights.missing_data_strategy``. The supported
  strategy is ``median`` (the default): a candidate lacking data in a dimension receives
  the median *normalised* score of the candidates that do have data, rather than ``0``.
"""

from __future__ import annotations

from collections.abc import Callable
from statistics import median
from typing import Any

from src.config import ScoringWeights
from src.models import ModelScore

DIMENSION_KEYS = [
    "depreciation",
    "maintenance_cost",
    "owner_satisfaction",
    "safety",
    "fuel_efficiency",
    "theft_risk",
    "resale_liquidity",
    "price_vs_fipe",
]

# For each dimension, whether a larger raw value is a better outcome.
HIGHER_IS_BETTER: dict[str, bool] = {
    "depreciation": False,  # lower annual depreciation = better
    "maintenance_cost": False,  # lower cost = better
    "owner_satisfaction": True,  # higher rating = better
    "safety": True,  # more stars = better
    "fuel_efficiency": True,  # higher km/L = better
    "theft_risk": False,  # lower theft index = better
    "resale_liquidity": True,  # higher sales volume = better
    "price_vs_fipe": True,  # closer to budget sweet spot = better
}


def _key(brand: str, model: str) -> tuple[str, str]:
    """Case-insensitive join key for ``(brand, model)``."""
    return (brand.strip().casefold(), model.strip().casefold())


def _index_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group rows by their case-insensitive ``(brand, model)`` key."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_key(row["brand"], row["model"]), []).append(row)
    return grouped


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _raw_depreciation(rows: list[dict[str, Any]]) -> float | None:
    """Estimate annual depreciation percent from FIPE price history.

    Compares the newest model-year price against the oldest within the candidate's
    FIPE rows. Returns a per-year percent (lower is better). Needs at least two
    distinct years to be meaningful.
    """
    by_year: dict[int, list[float]] = {}
    for row in rows:
        by_year.setdefault(int(row["year"]), []).append(float(row["price_brl"]))
    if len(by_year) < 2:
        return None
    newest_year = max(by_year)
    oldest_year = min(by_year)
    newest_price = _mean(by_year[newest_year])
    oldest_price = _mean(by_year[oldest_year])
    if not newest_price or not oldest_price or newest_price <= 0:
        return None
    span = newest_year - oldest_year
    if span <= 0:
        return None
    total_drop_pct = (newest_price - oldest_price) / newest_price
    return (total_drop_pct / span) * 100.0


def _raw_maintenance(rows: list[dict[str, Any]]) -> float | None:
    return _mean([float(r["cost_brl"]) for r in rows])


def _raw_owner_satisfaction(rows: list[dict[str, Any]]) -> float | None:
    return _mean([float(r["overall"]) for r in rows])


def _raw_safety(rows: list[dict[str, Any]]) -> float | None:
    return _mean([float(r["stars"]) for r in rows])


def _raw_fuel_efficiency(rows: list[dict[str, Any]]) -> float | None:
    values = [(float(r["city_kml"]) + float(r["highway_kml"])) / 2.0 for r in rows]
    return _mean(values)


def _raw_theft_risk(rows: list[dict[str, Any]]) -> float | None:
    return _mean([float(r["index_value"]) for r in rows])


def _raw_price(rows: list[dict[str, Any]]) -> float | None:
    return _mean([float(r["price_brl"]) for r in rows])


def _normalize_0_1(value: float, low: float, high: float, higher_is_better: bool) -> float:
    """Min-max normalize a raw value to [0, 1].

    When every candidate shares the same raw value (``low == high``) the dimension
    carries no signal, so all candidates receive a neutral ``0.5``.
    """
    if high == low:
        return 0.5
    scaled = (value - low) / (high - low)
    return scaled if higher_is_better else 1.0 - scaled


def score_candidates(
    vehicle_rows: list[dict[str, Any]],
    fipe_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
    fuel_rows: list[dict[str, Any]],
    maintenance_rows: list[dict[str, Any]],
    owner_rows: list[dict[str, Any]],
    theft_rows: list[dict[str, Any]],
    weights: ScoringWeights,
) -> list[ModelScore]:
    """Compute per-dimension scores and ``weighted_total`` for each candidate.

    Returns a list sorted by ``weighted_total`` descending, with ``rank`` assigned
    1-based. Missing dimension data is filled with the median normalised score for
    that dimension across all candidates (``missing_data_strategy: median``).
    """
    if not vehicle_rows:
        return []

    # FIPE prices are keyed on fipe_code; map each candidate's fipe_code to its rows.
    fipe_by_code: dict[str, list[dict[str, Any]]] = {}
    for row in fipe_rows:
        fipe_by_code.setdefault(str(row["fipe_code"]), []).append(row)

    safety_by_key = _index_rows(safety_rows)
    fuel_by_key = _index_rows(fuel_rows)
    maintenance_by_key = _index_rows(maintenance_rows)
    owner_by_key = _index_rows(owner_rows)
    theft_by_key = _index_rows(theft_rows)

    candidates: list[tuple[str, str]] = [(v["brand"], v["model"]) for v in vehicle_rows]

    def fipe_for(vehicle: dict[str, Any]) -> list[dict[str, Any]]:
        return fipe_by_code.get(str(vehicle.get("fipe_code", "")), [])

    # Extractor per dimension: (vehicle row, join key) -> raw value (or None).
    extractors: dict[str, Callable[[dict[str, Any], tuple[str, str]], float | None]] = {
        "depreciation": lambda v, _k: _raw_depreciation(fipe_for(v)),
        "maintenance_cost": lambda _v, k: _raw_maintenance(maintenance_by_key.get(k, [])),
        "owner_satisfaction": lambda _v, k: _raw_owner_satisfaction(owner_by_key.get(k, [])),
        "safety": lambda _v, k: _raw_safety(safety_by_key.get(k, [])),
        "fuel_efficiency": lambda _v, k: _raw_fuel_efficiency(fuel_by_key.get(k, [])),
        "theft_risk": lambda _v, k: _raw_theft_risk(theft_by_key.get(k, [])),
        "resale_liquidity": lambda _v, _k: None,  # no data source yet
        "price_vs_fipe": lambda v, _k: _raw_price(fipe_for(v)),
    }

    # 1. Collect raw values per dimension across all candidates.
    raw_by_dim: dict[str, list[float | None]] = {}
    for dim in DIMENSION_KEYS:
        extractor = extractors[dim]
        raw_by_dim[dim] = [
            extractor(vehicle_rows[i], _key(brand, model))
            for i, (brand, model) in enumerate(candidates)
        ]

    # 2. Normalise each dimension, then fill gaps with the median normalised score.
    norm_by_dim: dict[str, list[float]] = {}
    for dim in DIMENSION_KEYS:
        raws = raw_by_dim[dim]
        present = [r for r in raws if r is not None]
        if present:
            low, high = min(present), max(present)
            higher = HIGHER_IS_BETTER[dim]
            normalised_present = [
                _normalize_0_1(r, low, high, higher) for r in raws if r is not None
            ]
            fill = median(normalised_present)
            scores = [_normalize_0_1(r, low, high, higher) if r is not None else fill for r in raws]
        else:
            # No candidate has data in this dimension: neutral score for everyone.
            scores = [0.5] * len(candidates)
        norm_by_dim[dim] = scores

    # 3. Build ModelScore objects with the weighted total.
    results: list[ModelScore] = []
    for i, (brand, model) in enumerate(candidates):
        dimension_scores = {dim: round(norm_by_dim[dim][i], 6) for dim in DIMENSION_KEYS}
        weighted_total = sum(
            weight * dimension_scores[dim]
            for dim, weight in weights.weights.items()
            if dim in dimension_scores
        )
        results.append(
            ModelScore(
                brand=brand,
                model=model,
                dimension_scores=dimension_scores,
                weighted_total=round(weighted_total, 6),
                rank=0,
            )
        )

    # 4. Sort descending by weighted_total and assign 1-based ranks.
    results.sort(key=lambda ms: ms.weighted_total, reverse=True)
    for rank, ms in enumerate(results, start=1):
        ms.rank = rank

    return results
