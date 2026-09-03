from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.api.routes import router

settings = get_settings()

app = FastAPI(
    title="SOCIALIQ API",
    description="Agentic AI Social Intelligence & Decision Support Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "SOCIALIQ",
        "tagline": "From Social Signals to Actionable Intelligence.",
        "docs": "/docs",
    }
