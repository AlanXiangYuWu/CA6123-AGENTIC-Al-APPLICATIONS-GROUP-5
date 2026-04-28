"""Product Agent: PRD from brief + research."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.utils.json_parse import extract_json

SYSTEM = """You are the Product Agent. Write a PRD based on the brief and
research report. Output ONLY a JSON object with keys:
  positioning (string),
  user_flows (list of {name, steps}),
  features (priority-ranked list of {name, priority, rationale}),
  non_functional_requirements (list of strings),
  success_metrics (list of strings)."""


def product_agent(state: ProjectState) -> dict:
    resp = get_llm().invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(
                content=(
                    f"BRIEF:\n{json.dumps(state['project_brief'])}\n\n"
                    f"RESEARCH:\n{json.dumps(state['research_report'])}"
                )
            ),
        ]
    )
    return {
        "prd": extract_json(resp.content),
        "messages": [AIMessage(content="[Product] PRD ready")],
        "trace": append_trace(state, "product"),
    }
