from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    # Local Ollama instance (fully configurable via env)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    # LLM runtime behavior
    llm_max_output_tokens: int = 700
    # Web search tool-calling (used by the insight agent for live lookups)
    web_search_max_results: int = 6
    # Allowed web-search domains for the LLM tool call (empty = allow all)
    web_search_allowed_domains: str = ""
    # Data store files for users and chat sessions
    users_store_path: str = "./data/users.json"
    sessions_store_path: str = "./data/sessions.json"
    # Access-token lifetime in minutes
    access_token_expire_minutes: int = 60
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
    serpapi_api_key: str = ""
    serpapi_google_domain: str = "google.com"
    serpapi_trends_geo: str = ""
    serpapi_trends_date: str = "today 12-m"
    news_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    # n8n_webhook_url: str = "http://localhost:5678/webhook/socialiq"
    n8n_webhook_url: str = "http://host.docker.internal:8000/api/v1/chat"
    n8n_api_key: str = ""  # when set, service/webhook calls must present X-API-Key
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


def split_allowed_domains(raw: str) -> list[str]:
    """Parse the comma-separated allowed-domains list from settings."""
    return [d.strip().lower() for d in raw.split(",") if d.strip()]
