from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "sqlite+aiosqlite:///./newsfeed.db"
    debug: bool = False
    log_level: str = "INFO"
    # Set to false if your environment uses SSL inspection (e.g. corporate proxy)
    ssl_verify: bool = True


settings = Settings()
