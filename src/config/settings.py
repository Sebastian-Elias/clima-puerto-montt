from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    db_host: str = "localhost"
    db_port: int = 5432
    db_password: str
    db_name: str ="chile-weather"
    db_user: str ="salmon_user"
    api_url: str
    log_level: str = "INFO"
    db_sslmode: str = "prefer"
    weather_start_date: str = "1940-01-01"
    weather_end_date: str = "2025-12-31"
    env: str = "development"

@lru_cache
def get_settings() -> Settings:
    return Settings()