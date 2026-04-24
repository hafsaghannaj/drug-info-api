from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenFDA (optional: raises rate limit from 240 → 1000 req/min)
    openfda_api_key: str = ""

    # Cache
    cache_db_path: str = "./cache.db"
    cache_ttl_label_seconds: int = 86400      # 24h — labels don't change often
    cache_ttl_rxcui_seconds: int = 604800     # 7d  — RxCUIs are stable
    cache_ttl_interaction_seconds: int = 3600  # 1h
    cache_ttl_search_seconds: int = 3600       # 1h

    # Rate limiting (per IP)
    rate_limit_default: str = "60/minute"
    rate_limit_interactions: str = "30/minute"

    # Upstream base URLs
    openfda_base_url: str = "https://api.fda.gov"
    rxnav_base_url: str = "https://rxnav.nlm.nih.gov/REST"
    dailymed_base_url: str = "https://dailymed.nlm.nih.gov/dailymed/services/v2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
