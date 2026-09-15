import logging
import os

# An invalid OPENAI_API_KEY once leaked into this process via Windows user/
# system environment variables and silently overrode `.env` (OS env has
# priority in pydantic-settings). Drop it BEFORE any Settings instantiation
# so `.env` remains the single source of truth for API keys.
_leaked_key = os.environ.pop("OPENAI_API_KEY", None)
if _leaked_key:
    logging.getLogger("socialiq").warning(
        "Removed OPENAI_API_KEY leaked from OS environment (set keys in .env instead)"
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.api.routes import router
from backend.auth.routes import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("socialiq")

settings = get_settings()

app = FastAPI(
    title="SOCIALIQ API",
    description="Agentic AI Social Intelligence & Decision Support Platform",
    version="0.1.0",
)

# CORS_ORIGINS accepts either a comma-separated origin list or a regex
# pattern prefixed with "regex:" (useful for dev ports like 3000-65535).
if settings.cors_origins.startswith("regex:"):
    cors_options = {"allow_origin_regex": settings.cors_origins.removeprefix("regex:")}
else:
    cors_options = {"allow_origins": [o.strip() for o in settings.cors_origins.split(",") if o.strip()]}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    **cors_options,
)


def _log_llm_chain() -> None:
    """Log the resolved LLM engine chain so 'which engine answered?' is greppable."""
    if settings.openai_api_key:
        openai_state = f"configured (model {settings.llm_model})"
    else:
        openai_state = "not configured (system-env leak guarded: keys not read from OS env)"
    logger.info(
        "LLM chain: OpenAI %s -> Ollama %s (model %s, keep_alive %s, auto_fallback %s)"
        " -> offline composer (socialiq-template-0.3)",
        openai_state,
        settings.ollama_base_url,
        settings.ollama_model,
        settings.ollama_keep_alive,
        settings.ollama_auto_fallback,
    )


@app.on_event("startup")
async def on_startup() -> None:
    _log_llm_chain()

app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "SOCIALIQ",
        "tagline": "From Social Signals to Actionable Intelligence.",
        "docs": "/docs",
    }
