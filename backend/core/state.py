"""Global ProjectState for the LangGraph workflow."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ProjectState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    project_brief: dict | None
    research_report: dict | None
    prd: dict | None
    tech_design: dict | None
    code_artifact: dict | None
    qa_report: dict | None
    final_package: dict | None
    revision_round: int
    citations: list[dict]
    guardrail_flags: list[dict]
    trace: list[str]


def initial_state(user_idea: str) -> ProjectState:
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=user_idea)],
        "project_brief": None,
        "research_report": None,
        "prd": None,
        "tech_design": None,
        "code_artifact": None,
        "qa_report": None,
        "final_package": None,
        "revision_round": 0,
        "citations": [],
        "guardrail_flags": [],
        "trace": [],
    }


def append_trace(state: ProjectState, who: str) -> list[str]:
    return state.get("trace", []) + [who]
