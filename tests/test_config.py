"""Tests for configuration settings validation."""

import pytest
from pydantic import ValidationError

from fastpubsub.config import Settings


def test_settings_log_level():
    """Test that invalid log level values are rejected.

    Validates that Settings raises a ValidationError when an invalid
    log level string is provided.
    """
    with pytest.raises(ValidationError) as excinfo:
        Settings(log_level="invalid")
    assert "Input should be 'debug', 'info', 'warning', 'error' or 'critical'" in str(excinfo.value)


def test_settings_database_url_format():
    """Test that database URL format is validated.

    Validates that Settings requires the correct PostgreSQL URL format
    starting with 'postgresql+psycopg://'.
    """
    with pytest.raises(ValidationError) as excinfo:
        Settings(database_url="postgresql://fastpubsub:fastpubsub@localhost:5432/fastpubsub")
    assert "must start with 'postgresql+psycopg://'" in str(excinfo.value)


def test_settings_subscription_backoff_order():
    """Test that subscription backoff timing is validated.

    Validates that max backoff seconds must be greater than or equal
    to min backoff seconds in subscription configuration.
    """
    with pytest.raises(ValidationError) as excinfo:
        Settings(subscription_backoff_min_seconds=5, subscription_backoff_max_seconds=4)
    assert (
        "subscription_backoff_max_seconds must be greater than or equal to subscription_backoff_min_seconds"
        in str(excinfo.value)
    )
