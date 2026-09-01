from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    database_url: str = "postgresql+asyncpg://socialiq:socialiq@localhost:5432/socialiq"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "socialiq123"
    x_bearer_token: str = ""
    telegram_bot_token: str = ""
    instagram_access_token: str = ""
    instagram_user_id: str = ""
    pinterest_access_token: str = ""
    google_search_api_key: str = ""
    google_search_cx: str = ""
    n8n_webhook_url: str = "http://localhost:5678/webhook/socialiq"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    blockchain_mode: str = "local"
    blockchain_ledger_path: str = "./data/ledger.json"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
