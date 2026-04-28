"""Orchestrator: deterministic routing function (no LLM call)."""

from __future__ import annotations

from typing import Literal

from backend.core.state import ProjectState, append_trace

RouteTarget = Literal[
    "customer", "research", "product", "architect", "coder", "qa", "delivery", "__end__"
]

MAX_REVISIONS = 2


def orchestrator_router(state: ProjectState) -> RouteTarget:
    # 5.7 revision-loop guard
    if state.get("revision_round", 0) > MAX_REVISIONS:
        return "delivery" if not state.get("final_package") else "__end__"

    # 5.8 Task Plan constraints (linear gating)
    brief = state.get("project_brief")
    if not brief:
        return "customer"
    if isinstance(brief, dict) and brief.get("status") == "needs_clarification":
        return "__end__"
    if not state.get("research_report"):
        return "research"
    if not state.get("prd"):
        return "product"
    if not state.get("tech_design"):
        return "architect"
    if not state.get("code_artifact"):
        return "coder"
    if not state.get("qa_report"):
        return "qa"

    qa = state["qa_report"] or {}
    if qa.get("passed") is False and state.get("revision_round", 0) <= MAX_REVISIONS:
        return "coder"

    if not state.get("final_package"):
        return "delivery"
    return "__end__"


def qa_post(state: ProjectState) -> dict:
    """Bump revision counter and clear stale artifacts when QA fails."""
    qa = state.get("qa_report") or {}
    out: dict = {"trace": append_trace(state, "qa_post")}
    if qa.get("passed") is False:
        out["revision_round"] = state.get("revision_round", 0) + 1
        out["code_artifact"] = None
        out["qa_report"] = None
    return out
