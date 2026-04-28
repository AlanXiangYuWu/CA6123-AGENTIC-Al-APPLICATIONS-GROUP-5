"""QA Agent: review coverage, run grounding checks, decide pass/fail."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm_strict
from backend.utils.json_parse import extract_json

SYSTEM = """You are the QA Agent. Evaluate whether:
1) the PRD covers the brief,
2) the tech design covers the PRD,
3) the code matches the design,
4) any hallucinations or ungrounded claims exist.
Output ONLY a JSON object with keys:
  passed (bool, true if score >= 0.7 and no critical issues),
  score (float 0-1),
  issues (list of {type, target, description}),
  test_cases (list of {name, input, expected})."""


def qa_agent(state: ProjectState) -> dict:
    payload = {
        "brief": state["project_brief"],
        "prd": state["prd"],
        "tech_design": state["tech_design"],
        "code_artifact_summary": [
            f.get("path") for f in (state["code_artifact"] or {}).get("files", [])
        ],
    }
    resp = get_llm_strict().invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload))]
    )
    return {
        "qa_report": extract_json(resp.content),
        "messages": [AIMessage(content="[QA] review done")],
        "trace": append_trace(state, "qa"),
    }
