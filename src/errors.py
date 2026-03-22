"""Structured error taxonomy following RFC 7807 pattern.

Every error carries an error_type classification, human-readable detail,
and actionable suggestions so agents can decide recovery strategy.
"""

from __future__ import annotations

from typing import Any


class CollectorError(Exception):
    """Base error for all collector operations."""

    error_type: str = "UNKNOWN"
    retriable: bool = False

    def __init__(
        self,
        detail: str,
        *,
        suggestions: list[str] | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.detail = detail
        self.suggestions = suggestions or [self._default_suggestion()]
        self.retry_after_seconds = retry_after_seconds
        super().__init__(detail)

    def _default_suggestion(self) -> str:
        return "Check logs for details"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to RFC 7807-style dict."""
        result: dict[str, Any] = {
            "error_type": self.error_type,
            "detail": self.detail,
            "suggestions": self.suggestions,
            "retriable": self.retriable,
        }
        if self.retry_after_seconds is not None:
            result["retry_after_seconds"] = self.retry_after_seconds
        return result


class RetriableError(CollectorError):
    """Transient failures that should be retried (HTTP 429, 503)."""

    error_type = "RETRIABLE"
    retriable = True

    def _default_suggestion(self) -> str:
        return "Wait and retry the request"


class NonRetriableError(CollectorError):
    """Permanent failures that should be skipped (404, structural change)."""

    error_type = "NON_RETRIABLE"
    retriable = False

    def _default_suggestion(self) -> str:
        return "Skip this resource and alert operator"


class ConfigError(CollectorError):
    """Configuration problems requiring human intervention."""

    error_type = "CONFIG_ERROR"
    retriable = False

    def _default_suggestion(self) -> str:
        return "Check configuration files in config/"


class RateLimitedError(CollectorError):
    """Rate limit hit — backoff required."""

    error_type = "RATE_LIMITED"
    retriable = True

    def __init__(
        self,
        detail: str,
        *,
        suggestions: list[str] | None = None,
        retry_after_seconds: int = 60,
    ) -> None:
        super().__init__(
            detail,
            suggestions=suggestions,
            retry_after_seconds=retry_after_seconds,
        )

    def _default_suggestion(self) -> str:
        return "Reduce concurrency or wait for rate limit reset"
