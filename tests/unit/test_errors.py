from src.errors import (
    CollectorError,
    ConfigError,
    NonRetriableError,
    RateLimitedError,
    RetriableError,
)


class TestCollectorErrorSerialization:
    def test_base_error_to_dict(self):
        err = CollectorError("something broke")
        d = err.to_dict()
        assert d["error_type"] == "UNKNOWN"
        assert d["detail"] == "something broke"
        assert d["retriable"] is False
        assert len(d["suggestions"]) > 0
        assert "retry_after_seconds" not in d

    def test_retriable_error(self):
        err = RetriableError("503 from server", retry_after_seconds=30)
        d = err.to_dict()
        assert d["error_type"] == "RETRIABLE"
        assert d["retriable"] is True
        assert d["retry_after_seconds"] == 30

    def test_non_retriable_error(self):
        err = NonRetriableError("404 not found")
        d = err.to_dict()
        assert d["error_type"] == "NON_RETRIABLE"
        assert d["retriable"] is False

    def test_config_error(self):
        err = ConfigError("missing sources.yaml")
        d = err.to_dict()
        assert d["error_type"] == "CONFIG_ERROR"
        assert d["retriable"] is False
        assert "config" in d["suggestions"][0].lower()

    def test_rate_limited_error_defaults(self):
        err = RateLimitedError("429 on /cars/page/12")
        d = err.to_dict()
        assert d["error_type"] == "RATE_LIMITED"
        assert d["retriable"] is True
        assert d["retry_after_seconds"] == 60

    def test_rate_limited_custom_retry(self):
        err = RateLimitedError("429", retry_after_seconds=120)
        assert err.to_dict()["retry_after_seconds"] == 120

    def test_custom_suggestions_override_default(self):
        err = RetriableError("fail", suggestions=["Try plan B", "Escalate"])
        d = err.to_dict()
        assert d["suggestions"] == ["Try plan B", "Escalate"]

    def test_suggestions_always_non_empty(self):
        """Every error subclass must have at least one suggestion."""
        for cls in [
            CollectorError,
            RetriableError,
            NonRetriableError,
            ConfigError,
            RateLimitedError,
        ]:
            err = cls("test")
            assert len(err.suggestions) > 0, f"{cls.__name__} has empty suggestions"
            assert len(err.to_dict()["suggestions"]) > 0

    def test_error_is_exception(self):
        err = RetriableError("boom")
        assert isinstance(err, Exception)
        assert str(err) == "boom"
