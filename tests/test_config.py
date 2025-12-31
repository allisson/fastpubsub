import pytest
from pydantic import ValidationError

from fastpubsub.config import Settings


def test_settings_log_level():
    with pytest.raises(ValidationError) as excinfo:
        Settings(log_level="invalid")
    assert "Input should be 'debug', 'info', 'warning', 'error' or 'critical'" in str(excinfo.value)


def test_settings_database_url_format():
    with pytest.raises(ValidationError) as excinfo:
        Settings(database_url="postgresql://fastpubsub:fastpubsub@localhost:5432/fastpubsub")
    assert "Value error, must start with 'postgresql+psycopg://'" in str(excinfo.value)


def test_settings_subscription_backoff_order():
    with pytest.raises(ValidationError) as excinfo:
        Settings(subscription_backoff_min_seconds=5, subscription_backoff_max_seconds=4)
    assert (
        "Value error, subscription_backoff_max_seconds must be greater than subscription_backoff_min_seconds"
        in str(excinfo.value)
    )
