import pytest
from pydantic import ValidationError

from src.models import (
    DepreciationCurve,
    FipePrice,
    FuelEfficiency,
    MaintenanceCost,
    ModelScore,
    OwnerRating,
    SafetyRating,
    TheftIndex,
    VehicleModel,
)


class TestVehicleModel:
    def test_create(self):
        m = VehicleModel(brand="Toyota", model="Corolla", category="sedan", fipe_code="001234-5")
        assert m.brand == "Toyota"
        assert m.fipe_code == "001234-5"

    def test_timestamps_optional(self):
        m = VehicleModel(brand="Honda", model="Civic", category="sedan", fipe_code="001234-6")
        assert m.created_at is None


class TestFipePrice:
    def test_create(self):
        p = FipePrice(
            fipe_code="001234-5",
            year=2023,
            price_brl=85000.0,
            reference_month="2026-03",
            fuel_type="flex",
        )
        assert p.price_brl == 85000.0


class TestDepreciationCurve:
    def test_empty_prices(self):
        d = DepreciationCurve(brand="Toyota", model="Corolla", year=2023)
        assert d.prices == []
        assert d.annual_depreciation_pct is None


class TestSafetyRating:
    def test_valid_stars(self):
        s = SafetyRating(brand="Toyota", model="Corolla", protocol="latin_ncap_2024", stars=4)
        assert s.stars == 4

    def test_invalid_stars_too_high(self):
        with pytest.raises(ValidationError):
            SafetyRating(brand="Toyota", model="Corolla", protocol="latin_ncap_2024", stars=6)

    def test_invalid_stars_negative(self):
        with pytest.raises(ValidationError):
            SafetyRating(brand="Toyota", model="Corolla", protocol="latin_ncap_2024", stars=-1)

    def test_optional_percentages(self):
        s = SafetyRating(brand="Toyota", model="Corolla", protocol="latin_ncap_2024", stars=3)
        assert s.adult_pct is None


class TestFuelEfficiency:
    def test_create(self):
        f = FuelEfficiency(
            brand="Toyota",
            model="Corolla",
            version="2.0 XEi",
            city_kml=10.5,
            highway_kml=14.2,
            rating="A",
        )
        assert f.city_kml == 10.5


class TestMaintenanceCost:
    def test_create(self):
        m = MaintenanceCost(brand="Toyota", model="Corolla", interval_km=10000, cost_brl=650.0)
        assert m.interval_km == 10000


class TestOwnerRating:
    def test_create_with_dimensions(self):
        r = OwnerRating(
            brand="Toyota",
            model="Corolla",
            source="carros_na_web",
            dimension_scores={"comfort": 4.2, "performance": 3.8},
            overall=4.0,
            review_count=150,
        )
        assert r.dimension_scores["comfort"] == 4.2

    def test_empty_dimensions(self):
        r = OwnerRating(
            brand="Toyota",
            model="Corolla",
            source="carroclub",
            overall=3.5,
            review_count=10,
        )
        assert r.dimension_scores == {}


class TestTheftIndex:
    def test_create(self):
        t = TheftIndex(brand="Toyota", model="Corolla", index_value=0.85)
        assert t.index_value == 0.85


class TestModelScore:
    def test_create(self):
        s = ModelScore(
            brand="Toyota",
            model="Corolla",
            dimension_scores={"depreciation": 0.8, "safety": 0.9},
            weighted_total=0.85,
            rank=1,
        )
        assert s.rank == 1
        assert s.weighted_total == 0.85
