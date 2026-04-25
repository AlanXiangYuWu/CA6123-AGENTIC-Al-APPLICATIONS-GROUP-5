"""Gemini LLM clients. Two variants: creative (default) and strict (temp=0)."""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.core.config import get_settings


def _ensure_env() -> None:
    settings = get_settings()
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    _ensure_env()
    return ChatGoogleGenerativeAI(model=get_settings().llm_model, temperature=0.3)


@lru_cache(maxsize=1)
def get_llm_strict() -> ChatGoogleGenerativeAI:
    _ensure_env()
    return ChatGoogleGenerativeAI(model=get_settings().llm_model, temperature=0.0)
