"""LLM clients with provider switch: Gemini or Bailian-compatible OpenAI API."""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from backend.core.config import get_settings


def _ensure_google_env() -> None:
    settings = get_settings()
    if settings.google_api_key:
        os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)


def _resolve_provider() -> str:
    return (get_settings().llm_provider or "google").strip().lower()


def _build_llm(temperature: float):
    settings = get_settings()
    provider = _resolve_provider()

    if provider in {"google", "gemini"}:
        _ensure_google_env()
        if not (settings.google_api_key or os.getenv("GOOGLE_API_KEY")):
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=google")
        return ChatGoogleGenerativeAI(model=settings.llm_model, temperature=temperature)

    if provider in {"bailian", "dashscope", "aliyun"}:
        api_key = settings.bailian_api_key or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError(
                "BAILIAN_API_KEY (or DASHSCOPE_API_KEY) is required when LLM_PROVIDER=bailian"
            )
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=temperature,
            api_key=api_key,
            base_url=settings.bailian_base_url,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


@lru_cache(maxsize=1)
def get_llm():
    return _build_llm(temperature=0.3)


@lru_cache(maxsize=1)
def get_llm_strict():
    return _build_llm(temperature=0.0)
