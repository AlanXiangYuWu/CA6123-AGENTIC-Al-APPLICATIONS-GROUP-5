"""Architect Agent: tech stack + system design."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.rag.kb import get_kb
from backend.utils.json_parse import extract_json

SYSTEM = """You are the Architect Agent. Choose the tech stack and design the
system. Cite [doc_id] markers from the technical context where relevant.
Output ONLY a JSON object with keys:
  tech_stack (list),
  system_components (list of {name, responsibility, depends_on}),
  data_model (object or list),
  api_contracts (list of {method, path, request, response}),
  deployment_notes (string)."""


def architect_agent(state: ProjectState) -> dict:
    docs = get_kb().retrieve("system architecture framework deployment", agent="Architect")
    ctx = "\n".join(f"[{d['source_doc_id']}] {d['doc']}" for d in docs)
    resp = get_llm().invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(
                content=f"PRD:\n{json.dumps(state['prd'])}\n\nTECH CONTEXT:\n{ctx}"
            ),
        ]
    )
    return {
        "tech_design": extract_json(resp.content),
        "messages": [AIMessage(content="[Architect] design ready")],
        "trace": append_trace(state, "architect"),
    }
