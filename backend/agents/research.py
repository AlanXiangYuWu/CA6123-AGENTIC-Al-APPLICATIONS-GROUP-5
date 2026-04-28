"""Research Agent: market info, competitors, pain points (RAG + citations)."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.rag.kb import get_kb
from backend.utils.json_parse import extract_json

SYSTEM = """You are the Research Agent. Produce a market research report.
You MUST cite supporting facts using [doc_id] markers from the provided context.
Output ONLY a JSON object with keys:
  competitors (list of {name, url, notes}),
  user_pain_points (list of strings),
  opportunities (list of strings),
  citations (list of {claim, source_doc_id})."""


def research_agent(state: ProjectState) -> dict:
    brief = state["project_brief"] or {}
    query = (
        f"{brief.get('product_name','')} {brief.get('core_problem','')} "
        "competitors market user research"
    )
    docs = get_kb().retrieve(query, agent="Research")
    ctx = "\n".join(f"[{d['source_doc_id']}] {d['doc']}" for d in docs)
    resp = get_llm().invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(
                content=f"BRIEF:\n{json.dumps(brief)}\n\nCONTEXT:\n{ctx}"
            ),
        ]
    )
    report = extract_json(resp.content)
    return {
        "research_report": report,
        "citations": state.get("citations", []) + report.get("citations", []),
        "messages": [AIMessage(content=f"[Research] {len(docs)} docs cited")],
        "trace": append_trace(state, "research"),
    }
