"""Unit tests for db.py upsert and query helpers.

These tests use a mock cursor to verify SQL generation and parameter passing
without requiring a running database. Integration tests hit a real Postgres.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from src.db import (
    upsert_fipe_price,
    upsert_fuel_efficiency,
    upsert_maintenance_cost,
    upsert_model_score,
    upsert_owner_rating,
    upsert_safety_rating,
    upsert_theft_index,
    upsert_vehicle_model,
)
from src.models import (
    FipePrice,
    FuelEfficiency,
    MaintenanceCost,
    ModelScore,
    OwnerRating,
    SafetyRating,
    TheftIndex,
    VehicleModel,
)


def make_cursor():
    return MagicMock()


class TestUpsertVehicleModel:
    def test_calls_execute_with_correct_params(self):
        cur = make_cursor()
        m = VehicleModel(brand="Toyota", model="Corolla", category="sedan", fipe_code="015362-5")
        upsert_vehicle_model(cur, m)
        cur.execute.assert_called_once()
        sql, params = cur.execute.call_args.args
        assert "ON CONFLICT" in sql
        assert params["brand"] == "Toyota"
        assert params["fipe_code"] == "015362-5"


class TestUpsertFipePrice:
    def test_calls_execute_with_correct_params(self):
        cur = make_cursor()
        p = FipePrice(
            fipe_code="015362-5",
            year=2023,
            price_brl=82500.0,
            reference_month="2026-03",
            fuel_type="flex",
        )
        upsert_fipe_price(cur, p)
        cur.execute.assert_called_once()
        sql, params = cur.execute.call_args.args
        assert "ON CONFLICT" in sql
        assert params["price_brl"] == 82500.0


class TestUpsertSafetyRating:
    def test_calls_execute_with_correct_params(self):
        cur = make_cursor()
        s = SafetyRating(
            brand="Toyota",
            model="Corolla",
            protocol="latin_ncap_2024",
            stars=4,
            adult_pct=85.0,
            child_pct=78.0,
        )
        upsert_safety_rating(cur, s)
        cur.execute.assert_called_once()
        _, params = cur.execute.call_args.args
        assert params["stars"] == 4
        assert params["adult_pct"] == 85.0
        assert params["pedestrian_pct"] is None


class TestUpsertFuelEfficiency:
    def test_calls_execute(self):
        cur = make_cursor()
        f = FuelEfficiency(
            brand="Toyota",
            model="Corolla",
            version="2.0 XEi",
            city_kml=10.5,
            highway_kml=14.2,
            rating="A",
        )
        upsert_fuel_efficiency(cur, f)
        cur.execute.assert_called_once()


class TestUpsertMaintenanceCost:
    def test_calls_execute(self):
        cur = make_cursor()
        m = MaintenanceCost(brand="Toyota", model="Corolla", interval_km=10000, cost_brl=650.0)
        upsert_maintenance_cost(cur, m)
        cur.execute.assert_called_once()


class TestUpsertOwnerRating:
    def test_serializes_dimension_scores_as_json(self):
        cur = make_cursor()
        r = OwnerRating(
            brand="Toyota",
            model="Corolla",
            source="carros_na_web",
            dimension_scores={"comfort": 4.2},
            overall=4.0,
            review_count=150,
        )
        upsert_owner_rating(cur, r)
        _, params = cur.execute.call_args.args
        assert '"comfort"' in params["dimension_scores"]


class TestUpsertTheftIndex:
    def test_calls_execute(self):
        cur = make_cursor()
        t = TheftIndex(brand="Toyota", model="Corolla", index_value=0.85)
        upsert_theft_index(cur, t)
        cur.execute.assert_called_once()


class TestUpsertModelScore:
    def test_serializes_dimension_scores_as_json(self):
        cur = make_cursor()
        s = ModelScore(
            brand="Toyota",
            model="Corolla",
            dimension_scores={"depreciation": 0.8},
            weighted_total=0.85,
            rank=1,
        )
        upsert_model_score(cur, s)
        _, params = cur.execute.call_args.args
        assert '"depreciation"' in params["dimension_scores"]
        assert params["rank"] == 1
