"""FastAPI app entrypoint.

Run:
    cd agentic_app
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="CA6123 Agentic Workflow API",
    description="Multi-agent product-design pipeline (LangGraph + Gemini).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {
        "service": "agentic-workflow",
        "docs": "/docs",
        "endpoints": ["/api/health", "/api/run", "/api/ws/run"],
    }
