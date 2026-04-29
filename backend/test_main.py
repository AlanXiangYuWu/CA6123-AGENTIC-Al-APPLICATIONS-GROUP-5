"""Unit-test style API server (separate port).

This server is intended for running a single agent/module in isolation
(e.g., only `research_agent`) with system-prepared inputs.

Run:
  uvicorn backend.test_main:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI

from backend.agents.research import research_agent
from backend.core.state import initial_state
from backend.rag.kb import configure_kb_collections, get_kb_runtime_status
from backend.utils.debug_logger import log_artifact, reset_log_buffer, set_log_buffer


test_router = APIRouter()
app = FastAPI(title="CA6123 Module Test Server", version="0.1.0")
app.include_router(test_router)


def _default_research_project_brief() -> dict[str, Any]:
    # Deterministic, requirement-aligned input for unit-testing research_agent.
    return {
        "product_name": "Kids Coding Companion (Python Missions)",
        "one_sentence_summary": "An educational coding app for kids (6–12) that teaches Python through game-like missions.",
        "target_users": ["Parents (buyers)", "Kids (learners)"],
        "user_scenario": "A parent wants structured coding learning for their 6–12-year-old with visible progress.",
        "core_problem": "Kids struggle to sustain learning motivation and parents lack clear milestones.",
        "proposed_solution": "A mission-based Python learning journey with daily progress, guided challenges, and parent-friendly dashboards.",
        "must_have_features": [
            "Mission progression with checkpoints",
            "Age-appropriate Python learning content",
        ],
        "nice_to_have_features": ["Adaptive hints", "Community showcases"],
        "platform": "Mobile + Web (progress dashboard)",
        "business_model": "Subscription with tiered plans for families",
        "constraints": {
            "budget": "Tight initial budget (MVP in 6–8 weeks).",
            "timeline": "MVP in 6–8 weeks; iterate after initial learning retention tests.",
            "region": "Global / English-first",
            "compliance": ["COPPA-style child privacy considerations"],
        },
        "success_criteria": ["Day-7 retention", "Lessons completed per week", "Parent satisfaction surveys"],
        "assumptions": ["Initial content can be adapted from curated educational materials."],
        "open_questions": ["Which age segment shows the fastest learning retention?"],
    }


@test_router.get("/api-test/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "module-test-server"}


@test_router.get("/api-test/test/default-input")
def get_default_input(module: str = "research") -> dict[str, Any]:
    m = (module or "").strip().lower()
    if m == "research":
        return {"module": "research", "project_brief": _default_research_project_brief()}
    return {"error": f"Unsupported module for default input: {m}"}  # type: ignore[return-value]


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

    # System-prepared inputs.
    project_brief = payload.get("project_brief") or _default_research_project_brief()

    state = initial_state(user_idea="__unit_test__")
    state["project_brief"] = project_brief
    # Ensure trace is empty and revision_round exists.
    state["trace"] = []
    state["revision_round"] = 0

    if module == "research":
        debug_logs: list[str] = []
        token = set_log_buffer(debug_logs)
        try:
            update = research_agent(state)
        finally:
            reset_log_buffer(token)
        # Merge update back into a snapshot-like output.
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
            "citations": state.get("citations", []),
            "guardrail_flags": state.get("guardrail_flags", []),
            "trace": state.get("trace", []),
        },
    )

    return {
        "thread_id": "unit_test_" + module,
        "trace": state.get("trace", []),
        "revision_round": state.get("revision_round", 0),
        "project_brief": state.get("project_brief"),
        "research_report": state.get("research_report"),
        "citations": state.get("citations", []),
        "guardrail_flags": state.get("guardrail_flags", []),
        "debug_logs": debug_logs if module == "research" else [],
    }

