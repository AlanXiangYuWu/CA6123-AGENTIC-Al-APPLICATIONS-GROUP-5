"""Delivery Agent: assemble the Final Package."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.utils.json_parse import extract_json

SYSTEM = """You are the Delivery Agent. Assemble the Final Package.
Output ONLY a JSON object with these top-level keys (each a short summary
string or list):
  executive_summary, market_research, prd, technical_design, code_overview,
  qa_report, deployment_guide, demo_script, future_roadmap."""


def delivery_agent(state: ProjectState) -> dict:
    payload = {
        "brief": state["project_brief"],
        "research": state["research_report"],
        "prd": state["prd"],
        "tech_design": state["tech_design"],
        "code": state["code_artifact"],
        "qa": state["qa_report"],
        "guardrail_flags": state.get("guardrail_flags", []),
    }
    resp = get_llm().invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload))]
    )
    return {
        "final_package": extract_json(resp.content),
        "messages": [AIMessage(content="[Delivery] final package assembled")],
        "trace": append_trace(state, "delivery"),
    }
