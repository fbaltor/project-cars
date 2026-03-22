import pytest
import yaml
from pydantic import ValidationError

from src.config import BuyerProfile, ScoringWeights, load_config
from src.errors import ConfigError


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config directory with valid files."""
    buyer = {
        "budget": {"min": 60000, "max": 90000},
        "vehicle": {
            "max_age_years": 5,
            "max_mileage_km": 80000,
            "categories": ["hatch", "sedan"],
            "fuel_types": ["flex"],
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


class TestLoadConfig:
    def test_loads_valid_config(self, tmp_config):
        cfg = load_config(
            buyer_path=tmp_config / "buyer-profile.yaml",
            scoring_path=tmp_config / "scoring-weights.yaml",
            sources_path=tmp_config / "sources.yaml",
        )
        assert cfg.buyer.budget.min == 60000
        assert cfg.buyer.budget.max == 90000
        assert cfg.scoring.missing_data_strategy == "median"
        assert cfg.sources.fipe.parallelum_v2.startswith("https://")

    def test_loads_real_config(self):
        """Verify the actual config files in config/ are valid."""
        cfg = load_config()
        assert cfg.buyer.budget.min == 60000
        assert sum(cfg.scoring.weights.values()) == pytest.approx(1.0)

    def test_missing_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            load_config(buyer_path=tmp_path / "nonexistent.yaml")

    def test_invalid_yaml_raises_config_error(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("just a string")
        with pytest.raises(ConfigError, match="not a YAML mapping"):
            load_config(buyer_path=bad_file)


class TestScoringWeights:
    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValidationError, match="sum to 1.0"):
            ScoringWeights(weights={"a": 0.5, "b": 0.3})

    def test_weights_valid_sum(self):
        w = ScoringWeights(weights={"a": 0.6, "b": 0.4})
        assert w.weights["a"] == 0.6


class TestBuyerProfile:
    def test_valid_profile(self):
        p = BuyerProfile(
            budget={"min": 60000, "max": 90000},
            vehicle={
                "max_age_years": 5,
                "max_mileage_km": 80000,
                "categories": ["sedan"],
                "fuel_types": ["flex"],
            },
            use_case="city",
        )
        assert p.vehicle.max_age_years == 5
