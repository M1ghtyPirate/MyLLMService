from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_access_token_endpoint: str
    api_endpoint: str
    authorization_key: str
    llm_model: str = "GigaChat-2"
    llm_temperature: float = 0.2
    llm_timeout: float = 15.0
    llm_max_retries: int = 3
    llm_retry_backoff: float = 0.5
    cache_ttl_seconds: int = 600
    log_file: str = "logs/service.log"

    class Config:
        env_file = ".env"
        extra = "ignore"
