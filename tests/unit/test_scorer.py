"""Unit tests for the scoring engine.

These tests build plain row dicts (mirroring what the db.py query helpers return)
and verify ranking, score bounds, and missing-data handling without a live DB.
"""

from __future__ import annotations

from statistics import median

import pytest

from src.config import ScoringWeights
from src.models import ModelScore
from src.scorer import DIMENSION_KEYS, _normalize_0_1, score_candidates


@pytest.fixture
def weights() -> ScoringWeights:
    return ScoringWeights(
        weights={
            "depreciation": 0.20,
            "maintenance_cost": 0.15,
            "owner_satisfaction": 0.15,
            "safety": 0.15,
            "fuel_efficiency": 0.10,
            "theft_risk": 0.10,
            "resale_liquidity": 0.10,
            "price_vs_fipe": 0.05,
        },
        missing_data_strategy="median",
    )


@pytest.fixture
def vehicle_rows() -> list[dict]:
    return [
        {"brand": "Toyota", "model": "Corolla", "category": "sedan", "fipe_code": "001"},
        {"brand": "Honda", "model": "Civic", "category": "sedan", "fipe_code": "002"},
        {"brand": "Fiat", "model": "Argo", "category": "hatch", "fipe_code": "003"},
    ]


@pytest.fixture
def fipe_rows() -> list[dict]:
    # Two model-years per candidate so depreciation can be estimated.
    return [
        {"fipe_code": "001", "year": 2021, "price_brl": 90000.0},
        {"fipe_code": "001", "year": 2023, "price_brl": 100000.0},
        {"fipe_code": "002", "year": 2021, "price_brl": 80000.0},
        {"fipe_code": "002", "year": 2023, "price_brl": 95000.0},
        {"fipe_code": "003", "year": 2021, "price_brl": 60000.0},
        {"fipe_code": "003", "year": 2023, "price_brl": 70000.0},
    ]


@pytest.fixture
def safety_rows() -> list[dict]:
    # Fiat/Argo intentionally missing -> exercises median fill.
    return [
        {"brand": "Toyota", "model": "Corolla", "stars": 5},
        {"brand": "Honda", "model": "Civic", "stars": 4},
    ]


@pytest.fixture
def fuel_rows() -> list[dict]:
    return [
        {"brand": "Toyota", "model": "Corolla", "city_kml": 10.0, "highway_kml": 14.0},
        {"brand": "Honda", "model": "Civic", "city_kml": 9.0, "highway_kml": 13.0},
        {"brand": "Fiat", "model": "Argo", "city_kml": 12.0, "highway_kml": 16.0},
    ]


@pytest.fixture
def maintenance_rows() -> list[dict]:
    return [
        {"brand": "Toyota", "model": "Corolla", "cost_brl": 600.0},
        {"brand": "Honda", "model": "Civic", "cost_brl": 700.0},
        {"brand": "Fiat", "model": "Argo", "cost_brl": 500.0},
    ]


@pytest.fixture
def owner_rows() -> list[dict]:
    return [
        {"brand": "Toyota", "model": "Corolla", "overall": 4.5},
        {"brand": "Honda", "model": "Civic", "overall": 4.2},
        {"brand": "Fiat", "model": "Argo", "overall": 3.8},
    ]


@pytest.fixture
def theft_rows() -> list[dict]:
    return [
        {"brand": "Toyota", "model": "Corolla", "index_value": 0.5},
        {"brand": "Honda", "model": "Civic", "index_value": 0.8},
        {"brand": "Fiat", "model": "Argo", "index_value": 0.3},
    ]


@pytest.fixture
def result(
    vehicle_rows,
    fipe_rows,
    safety_rows,
    fuel_rows,
    maintenance_rows,
    owner_rows,
    theft_rows,
    weights,
) -> list[ModelScore]:
    return score_candidates(
        vehicle_rows,
        fipe_rows,
        safety_rows,
        fuel_rows,
        maintenance_rows,
        owner_rows,
        theft_rows,
        weights,
    )


def test_returns_one_score_per_candidate(result):
    assert len(result) == 3
    assert all(isinstance(ms, ModelScore) for ms in result)


def test_ranks_are_unique_and_one_based(result):
    ranks = [ms.rank for ms in result]
    assert sorted(ranks) == [1, 2, 3]
    assert len(set(ranks)) == 3


def test_sorted_descending_by_weighted_total(result):
    totals = [ms.weighted_total for ms in result]
    assert totals == sorted(totals, reverse=True)
    # Rank order matches sort order.
    for i, ms in enumerate(result, start=1):
        assert ms.rank == i


def test_weighted_total_in_bounds(result):
    for ms in result:
        assert 0.0 <= ms.weighted_total <= 1.0


def test_dimension_scores_in_bounds(result):
    for ms in result:
        assert set(ms.dimension_scores) == set(DIMENSION_KEYS)
        for value in ms.dimension_scores.values():
            assert 0.0 <= value <= 1.0


def test_missing_dimension_gets_median_not_zero(result):
    # Fiat/Argo has no safety row. Its safety score should equal the median of the
    # two present (normalised) safety scores, which is non-zero here.
    by_model = {ms.model: ms for ms in result}
    present_safety = sorted(
        by_model[m].dimension_scores["safety"] for m in ("Corolla", "Civic")
    )
    expected = median(present_safety)
    assert by_model["Argo"].dimension_scores["safety"] == pytest.approx(expected)
    assert by_model["Argo"].dimension_scores["safety"] > 0.0


def test_dimension_with_no_data_is_neutral(result):
    # resale_liquidity has no source -> every candidate gets neutral 0.5.
    for ms in result:
        assert ms.dimension_scores["resale_liquidity"] == pytest.approx(0.5)


def test_lower_is_better_inverts_scale(result):
    # Fiat/Argo has the lowest maintenance cost -> best (highest) maintenance score.
    by_model = {ms.model: ms for ms in result}
    assert by_model["Argo"].dimension_scores["maintenance_cost"] == pytest.approx(1.0)
    assert by_model["Civic"].dimension_scores["maintenance_cost"] == pytest.approx(0.0)


def test_higher_is_better_keeps_scale(result):
    by_model = {ms.model: ms for ms in result}
    # Corolla has the highest owner rating -> best owner score.
    assert by_model["Corolla"].dimension_scores["owner_satisfaction"] == pytest.approx(1.0)
    assert by_model["Argo"].dimension_scores["owner_satisfaction"] == pytest.approx(0.0)


def test_case_insensitive_join(weights):
    vehicles = [{"brand": "Toyota", "model": "Corolla", "category": "sedan", "fipe_code": "001"}]
    safety = [{"brand": "TOYOTA", "model": "corolla", "stars": 5}]
    out = score_candidates(vehicles, [], safety, [], [], [], [], weights)
    assert len(out) == 1
    # With a single candidate, normalisation yields the neutral 0.5 for every dimension.
    assert out[0].dimension_scores["safety"] == pytest.approx(0.5)


def test_empty_candidates_returns_empty_list(weights):
    assert score_candidates([], [], [], [], [], [], [], weights) == []


def test_normalize_higher_is_better():
    assert _normalize_0_1(5.0, 0.0, 10.0, higher_is_better=True) == pytest.approx(0.5)
    assert _normalize_0_1(10.0, 0.0, 10.0, higher_is_better=True) == pytest.approx(1.0)
    assert _normalize_0_1(0.0, 0.0, 10.0, higher_is_better=True) == pytest.approx(0.0)


def test_normalize_lower_is_better():
    assert _normalize_0_1(0.0, 0.0, 10.0, higher_is_better=False) == pytest.approx(1.0)
    assert _normalize_0_1(10.0, 0.0, 10.0, higher_is_better=False) == pytest.approx(0.0)


def test_normalize_equal_bounds_is_neutral():
    assert _normalize_0_1(5.0, 5.0, 5.0, higher_is_better=True) == pytest.approx(0.5)
