"""Unit-test style API server (separate port).

This server is intended for running a single agent/module in isolation
(e.g., only `research_agent`) with system-prepared inputs.

Run:
  uvicorn backend.test_main:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI

from backend.agents.product import product_agent
from backend.agents.research import research_agent
from backend.core.state import initial_state
from backend.rag.kb import configure_kb_collections, get_kb_runtime_status
from backend.utils.debug_logger import log_artifact, reset_log_buffer, set_log_buffer


test_router = APIRouter()
app = FastAPI(title="CA6123 Module Test Server", version="0.1.0")
app.include_router(test_router)

_FIXTURE_DIR = Path(__file__).resolve().parent / "test_fixtures"

def _load_module_fixture(module: str) -> dict[str, Any]:
    fixture_path = _FIXTURE_DIR / f"{module}.json"
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")
    with fixture_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Fixture must be a JSON object: {fixture_path}")
    return data


@test_router.get("/api-test/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "module-test-server"}


@test_router.get("/api-test/test/default-input")
def get_default_input(module: str = "research") -> dict[str, Any]:
    m = (module or "").strip().lower()
    if m not in {"research", "product"}:
        return {"error": f"Unsupported module for default input: {m}"}  # type: ignore[return-value]
    try:
        fixture = _load_module_fixture(m)
    except Exception as exc:
        return {"error": f"Failed to load fixture for module '{m}': {exc}"}  # type: ignore[return-value]
    return {
        "module": m,
        "project_brief": fixture.get("project_brief"),
        "research_report": fixture.get("research_report"),
    }


@test_router.get("/api-test/rag/collections")
def get_rag_collections() -> dict[str, Any]:
    return get_kb_runtime_status()


@test_router.post("/api-test/rag/collections")
def set_rag_collections(payload: dict[str, Any]) -> dict[str, Any]:
    business = payload.get("business_collection")
    technical = payload.get("technical_collection")
    if business is not None and not isinstance(business, str):
        return {"error": "business_collection must be string"}  # type: ignore[return-value]
    if technical is not None and not isinstance(technical, str):
        return {"error": "technical_collection must be string"}  # type: ignore[return-value]
    active = configure_kb_collections(
        business_collection=business,
        technical_collection=technical,
    )
    status = get_kb_runtime_status()
    return {"status": "ok", "active_collections": active, "runtime": status}


@test_router.post("/api-test/test/run")
def run_module_test(payload: dict[str, Any]) -> dict[str, Any]:
    module = (payload.get("module") or "").strip().lower()
    if not module:
        return {"error": "Missing 'module' field. Example: {\"module\":\"research\"}"}  # type: ignore[return-value]

    try:
        fixture = _load_module_fixture(module)
    except Exception as exc:
        return {"error": f"Failed to load fixture for module '{module}': {exc}"}  # type: ignore[return-value]

    # System-prepared inputs from fixture, optionally overridden by payload.
    project_brief = payload.get("project_brief") or fixture.get("project_brief") or {}
    research_report = payload.get("research_report") or fixture.get("research_report") or {}

    state = initial_state(user_idea="__unit_test__")
    state["project_brief"] = project_brief
    # Ensure trace is empty and revision_round exists.
    state["trace"] = []
    state["revision_round"] = 0

    if module == "research":
        debug_logs: list[str] = []
        token = set_log_buffer(debug_logs, log_prefix=module)
        try:
            update = research_agent(state)
        finally:
            reset_log_buffer(token)
        # Merge update back into a snapshot-like output.
        state.update(update)
    elif module == "product":
        state["research_report"] = research_report if isinstance(research_report, dict) else {}
        debug_logs = []
        token = set_log_buffer(debug_logs, log_prefix=module)
        try:
            update = product_agent(state)
        finally:
            reset_log_buffer(token)
        state.update(update)
    else:
        return {"error": f"Unsupported module: {module}"}  # type: ignore[return-value]

    # Persist final artifacts to a dedicated log file for audit/debug.
    log_artifact(
        "module_test_artifacts",
        {
            "module": module,
            "thread_id": "unit_test_" + module,
            "project_brief": state.get("project_brief"),
            "research_report": state.get("research_report"),
            "prd": state.get("prd"),
            "citations": state.get("citations", []),
            "guardrail_flags": state.get("guardrail_flags", []),
            "trace": state.get("trace", []),
        },
        file_prefix=f"{module}_artifacts",
    )

    return {
        "thread_id": "unit_test_" + module,
        "trace": state.get("trace", []),
        "revision_round": state.get("revision_round", 0),
        "project_brief": state.get("project_brief"),
        "research_report": state.get("research_report"),
        "prd": state.get("prd"),
        "citations": state.get("citations", []),
        "guardrail_flags": state.get("guardrail_flags", []),
        "debug_logs": debug_logs,
    }

