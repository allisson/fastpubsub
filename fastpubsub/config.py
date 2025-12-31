from enum import StrEnum

from pydantic import Field, field_validator, model_validator
from pydantic.networks import IPvAnyAddress
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class Settings(BaseSettings):
    # database
    database_url: str
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=1)
    database_pool_pre_ping: bool = True

    # log
    log_formatter: str = (
        "asctime=%(asctime)s level=%(levelname)s pathname=%(pathname)s line=%(lineno)s message=%(message)s"
    )
    log_level: LogLevel = LogLevel.info

    # subscription defaults
    subscription_max_attempts: int = Field(default=5, ge=1)
    subscription_backoff_min_seconds: int = Field(default=5, ge=1)
    subscription_backoff_max_seconds: int = Field(default=300, ge=1)

    # api
    api_debug: bool = False
    api_host: IPvAnyAddress = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1)
    api_num_workers: int = Field(default=1, ge=1)

    # workers
    cleanup_acked_messages_older_than_seconds: int = Field(default=3600, ge=1)
    cleanup_stuck_messages_lock_timeout_seconds: int = Field(default=60, ge=1)

    # load .env
    model_config = SettingsConfigDict(env_file=".env", env_prefix="fastpubsub_")

    @field_validator("database_url")
    def validate_database_url_format(cls, v: str):
        if not v.startswith("postgresql+psycopg://"):
            raise ValueError("must start with 'postgresql+psycopg://'")
        return v

    @model_validator(mode="after")
    def check_subscription_backoff_order(self) -> "Settings":
        if self.subscription_backoff_max_seconds < self.subscription_backoff_min_seconds:
            raise ValueError(
                "subscription_backoff_max_seconds must be greater than or equal to subscription_backoff_min_seconds"
            )
        return self


settings = Settings()
