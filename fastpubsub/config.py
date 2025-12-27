from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # database
    database_url: str
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_pre_ping: bool = True

    # log
    log_formatter: str = (
        "asctime=%(asctime)s level=%(levelname)s pathname=%(pathname)s line=%(lineno)s message=%(message)s"
    )
    log_level: str = "info"

    # subscription defaults
    subscription_max_attempts: int = 5
    subscription_backoff_min_seconds: int = 5
    subscription_backoff_max_seconds: int = 300

    # load .env
    model_config = SettingsConfigDict(env_file=".env", env_prefix="fastpubsub_")


settings = Settings()
