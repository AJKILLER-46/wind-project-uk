"""Application configuration via environment variables."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    # Elexon API
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    elexon_timeout_seconds: float = 30.0
    elexon_max_retries: int = 3

    # Cache
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_max_size: int = 128

    # CORS - comma-separated list
    cors_origins_str: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins_str.split(",") if o.strip()]

    # Analysis period defaults
    analysis_start_date: str = "2026-01-01"
    analysis_end_date: str = "2026-01-31"

    # Default decision cutoff time (HH:MM, Europe/London)
    # Illustrative default: end of day-ahead auction window (approx 11:00 UK time on D-1)
    # Real trading workflows must use the client-approved auction-specific cutoff.
    default_cutoff_time: str = "11:00"


settings = Settings()
