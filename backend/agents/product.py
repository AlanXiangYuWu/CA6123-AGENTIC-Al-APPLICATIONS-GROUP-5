"""Product Agent: PRD from brief + research + internal RAG."""

from __future__ import annotations

import json
from typing import Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.config import get_settings
from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.rag.kb import get_kb
from backend.utils.json_parse import extract_json
from backend.utils.debug_logger import log_llm_call_end, log_llm_call_start, log_step

_SETTINGS = get_settings()

SYSTEM = """You are the Product Agent. Write a PRD based on:
1) project brief
2) research report:
   - research_findings
   - goal_status.resolved_answers
   - unresolved_gaps
3) internal RAG context from business KB

Use only the provided context. Do not invent external facts.
When useful, cite source markers like [doc_id] inline in rationale text.

Output ONLY a JSON object with keys:
  positioning (string),
  user_flows (list of {name, steps}),
  features (priority-ranked list of {name, priority, rationale}),
  non_functional_requirements (list of strings),
  success_metrics (list of strings)."""

QUERY_SYSTEM = """You are the Product Agent query planner.
Generate focused internal-RAG retrieval queries for PRD drafting.

Input:
- project_brief
- research_selected (research_findings, resolved_answers, unresolved_gaps)

Output ONLY JSON:
{
  "queries": [
    "query text 1",
    "query text 2",
    "query text 3"
  ]
}

Rules:
- Return 3 to 5 concise, retrieval-friendly queries.
- Cover positioning, prioritized features/MVP, user flows, NFRs/metrics.
- Use only provided input context.
- Return valid JSON only.
"""


class ProductSelectedResearch(TypedDict):
    research_findings: list
    resolved_answers: list[str]
    unresolved_gaps: list


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _build_rag_queries_fallback(brief: dict, research_selected: ProductSelectedResearch) -> list[str]:
    product_name = (brief or {}).get("product_name", "") or ""
    core_problem = (brief or {}).get("core_problem", "") or ""
    target_users = _to_text((brief or {}).get("target_users", ""))
    findings = _to_text(research_selected.get("research_findings", ""))
    resolved_answers = _to_text(research_selected.get("resolved_answers", ""))
    unresolved_gaps = _to_text(research_selected.get("unresolved_gaps", ""))

    return [
        (
            f"PRD positioning for '{product_name}', core problem '{core_problem}', "
            f"target users '{target_users}'."
        ),
        (
            f"Feature prioritization and MVP scope for '{product_name}', "
            f"research findings: {findings[:220]}, resolved answers: {resolved_answers[:180]}"
        ),
        (
            f"User flow design and success metrics for '{product_name}', "
            f"problem '{core_problem}', unresolved gaps: {unresolved_gaps[:180]}."
        ),
    ]


def _build_rag_queries_with_llm(
    brief: dict, research_selected: ProductSelectedResearch
) -> tuple[list[str], bool]:
    fallback_queries = _build_rag_queries_fallback(brief, research_selected)
    payload = {
        "project_brief": brief if isinstance(brief, dict) else {},
        "research_selected": research_selected,
        "fallback_queries_reference": fallback_queries,
    }
    try:
        log_llm_call_start(
            "product_query_generation",
            {
                "provider": _SETTINGS.llm_provider,
                "brief_keys": sorted(list(brief.keys())) if isinstance(brief, dict) else [],
            },
        )
        resp = get_llm().invoke(
            [
                SystemMessage(content=QUERY_SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ]
        )
        log_llm_call_end(
            "product_query_generation",
            ok=True,
            response_chars=len(getattr(resp, "content", "") or ""),
        )
        parsed = extract_json(resp.content)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("queries"), list):
            raise ValueError("Invalid query planner output schema.")
        queries = []
        for q in parsed.get("queries", []):
            if isinstance(q, str) and q.strip():
                queries.append(q.strip())
        if len(queries) < 3:
            raise ValueError("Not enough valid queries from LLM planner.")
        return queries[:5], False
    except Exception as exc:
        log_llm_call_end("product_query_generation", ok=False, error=str(exc)[:200])
        log_step("product_query_generation_fallback", {"reason": str(exc)[:200]})
        return fallback_queries, True


def _select_research_input(research_report: dict) -> ProductSelectedResearch:
    report = research_report if isinstance(research_report, dict) else {}
    research_findings = report.get("research_findings", [])
    unresolved_gaps = report.get("unresolved_gaps", [])
    goal_status = report.get("goal_status", [])

    resolved_answers: list[str] = []
    if isinstance(goal_status, list):
        for gs in goal_status:
            if not isinstance(gs, dict):
                continue
            answers = gs.get("resolved_answers", [])
            if not isinstance(answers, list):
                continue
            for ans in answers:
                if isinstance(ans, str) and ans.strip():
                    resolved_answers.append(ans.strip())

    return {
        "research_findings": research_findings if isinstance(research_findings, list) else [],
        "resolved_answers": resolved_answers[:20],
        "unresolved_gaps": unresolved_gaps if isinstance(unresolved_gaps, list) else [],
    }


def _retrieve_rag_context(
    brief: dict, research_selected: ProductSelectedResearch, k_per_query: int = 3
) -> list[dict]:
    rag_queries, query_fallback = _build_rag_queries_with_llm(brief, research_selected)
    log_step(
        "product_rag_queries_generated",
        {
            "count": len(rag_queries),
            "fallback_used": query_fallback,
            "queries": [q[:120] for q in rag_queries],
        },
    )
    log_step(
        "product_kb_init_start",
        {"milvus_expected": True, "query_count": len(rag_queries)},
    )
    try:
        kb = get_kb()
        log_step("product_kb_init_done", {"ok": True})
    except Exception as exc:
        log_step("product_kb_init_failed", {"error": str(exc)[:200]}, level="WARN")
        return []

    docs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for query in rag_queries:
        for d in kb.retrieve(query, agent="Product", k=k_per_query):
            doc_id = str(d.get("source_doc_id", "") or "")
            text = str(d.get("doc", "") or "").strip()
            kb_name = str(d.get("kb", "") or "")
            key = (doc_id, text[:120])
            if not text or key in seen:
                continue
            seen.add(key)
            docs.append({"source_doc_id": doc_id, "kb": kb_name, "doc": text})
    top_docs = docs[:8]
    log_step(
        "product_internal_rag_results",
        {
            "query_count": len(rag_queries),
            "doc_count": len(top_docs),
            "source_doc_ids": [x.get("source_doc_id", "") for x in top_docs],
        },
    )
    return top_docs


def _format_rag_context(docs: list[dict]) -> str:
    if not docs:
        return ""
    lines = []
    for d in docs:
        source_id = d.get("source_doc_id", "")
        text = (d.get("doc", "") or "").strip().replace("\n", " ")
        lines.append(f"[{source_id}] {text[:700]}")
    return "\n".join(lines)


def _fallback_prd(brief: dict, research_report: dict, rag_docs: list[dict]) -> dict:
    product_name = (brief or {}).get("product_name", "Product") or "Product"
    target_users = (brief or {}).get("target_users", [])
    core_problem = (brief or {}).get("core_problem", "") or ""
    top_source = rag_docs[0].get("source_doc_id", "") if rag_docs else ""
    source_note = f" [source:{top_source}]" if top_source else ""
    return {
        "positioning": (
            f"{product_name} helps {_to_text(target_users) or 'target users'} "
            f"solve '{core_problem}' with a focused MVP approach.{source_note}"
        ),
        "user_flows": [
            {
                "name": "Core task completion",
                "steps": [
                    "User opens product and onboards quickly",
                    "User performs the primary task with guided workflow",
                    "User receives immediate feedback and can iterate",
                ],
            }
        ],
        "features": [
            {"name": "Core workflow", "priority": "P0", "rationale": "Directly addresses the core problem."},
            {"name": "Feedback loop", "priority": "P1", "rationale": "Improves retention and task success."},
            {"name": "Insights dashboard", "priority": "P2", "rationale": "Supports optimization after MVP."},
        ],
        "non_functional_requirements": [
            "Responsive UI for target platform",
            "Basic observability and error logging",
            "Data privacy and access control baseline",
        ],
        "success_metrics": [
            "Activation rate",
            "Core task completion rate",
            "Week-4 retention rate",
        ],
    }


def product_agent(state: ProjectState) -> dict:
    brief = state.get("project_brief") or {}
    research_report = state.get("research_report") or {}
    selected_research = _select_research_input(research_report)
    log_step(
        "product_agent_start",
        {
            "product_name": (brief or {}).get("product_name", ""),
            "research_findings_count": len(selected_research.get("research_findings", [])),
            "resolved_answers_count": len(selected_research.get("resolved_answers", [])),
            "unresolved_gaps_count": len(selected_research.get("unresolved_gaps", [])),
        },
    )
    rag_docs = _retrieve_rag_context(brief, selected_research)
    rag_context = _format_rag_context(rag_docs)

    payload = (
        f"BRIEF:\n{json.dumps(brief, ensure_ascii=False)}\n\n"
        f"RESEARCH_SELECTED:\n{json.dumps(selected_research, ensure_ascii=False)}\n\n"
        f"INTERNAL_RAG_CONTEXT:\n{rag_context or 'No relevant internal context found.'}"
    )
    try:
        log_llm_call_start(
            "product_prd_generation",
            {
                "provider": _SETTINGS.llm_provider,
                "rag_docs_count": len(rag_docs),
                "payload_chars": len(payload),
            },
        )
        resp = get_llm().invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=payload),
            ]
        )
        log_llm_call_end(
            "product_prd_generation",
            ok=True,
            response_chars=len(getattr(resp, "content", "") or ""),
        )
        prd = extract_json(resp.content)
    except Exception as exc:
        log_llm_call_end("product_prd_generation", ok=False, error=str(exc)[:200])
        prd = {}

    fallback = not isinstance(prd, dict) or "_raw" in prd
    if fallback:
        prd = _fallback_prd(brief, research_report, rag_docs)
    log_step(
        "product_prd_ready",
        {"fallback_used": fallback, "rag_docs_count": len(rag_docs)},
    )
    return {
        "prd": prd,
        "messages": [AIMessage(content=f"[Product] PRD ready, rag_docs={len(rag_docs)}")],
        "trace": append_trace(state, "product"),
    }
