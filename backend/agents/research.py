"""Research Agent: structured market research using internal RAG + optional web search."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.rag.kb import get_kb
from backend.tools.web_search import web_search
from backend.utils.json_parse import extract_json
from backend.utils.debug_logger import log_step

REQUIRED_BRIEF_FIELDS: list[str] = [
    "product_name",
    "one_sentence_summary",
    "target_users",
    "core_problem",
    "proposed_solution",
    "platform",
    "business_model",
    "constraints",
]

DEFAULT_RESEARCH_GOALS = [
    {
        "goal_id": "G1",
        "goal_name": "Target User Analysis",
        "goal_description": "Identify target user segments, needs, pain points, and motivations.",
        "required_evidence": [
            "identify target user segments",
            "summarize user needs",
            "summarize user pain points",
            "summarize user motivations",
        ],
        "priority": "high",
        "status": "unsatisfied",
    },
    {
        "goal_id": "G2",
        "goal_name": "Market Context Analysis",
        "goal_description": "Analyze market category, opportunities, and challenges.",
        "required_evidence": [
            "identify market category",
            "summarize market opportunities",
            "summarize market challenges",
        ],
        "priority": "high",
        "status": "unsatisfied",
    },
    {
        "goal_id": "G3",
        "goal_name": "Competitor Analysis",
        "goal_description": "Identify competitors/alternatives and summarize positioning, strengths, and weaknesses.",
        "required_evidence": [
            "identify competitors or alternatives",
            "summarize competitor positioning",
            "summarize competitor strengths",
            "summarize competitor weaknesses",
        ],
        "priority": "high",
        "status": "unsatisfied",
    },
    {
        "goal_id": "G4",
        "goal_name": "Business Model Analysis",
        "goal_description": "Evaluate given business model and propose alternative models with pros/cons.",
        "required_evidence": [
            "analyze the given business model",
            "identify possible alternative business models",
            "summarize pros and cons",
        ],
        "priority": "high",
        "status": "unsatisfied",
    },
    {
        "goal_id": "G5",
        "goal_name": "Risk Analysis",
        "goal_description": "Identify product, market, technical, and compliance risks if mentioned.",
        "required_evidence": [
            "identify product risks",
            "identify market risks",
            "identify technical risks",
            "identify compliance risks if mentioned in Brief",
        ],
        "priority": "high",
        "status": "unsatisfied",
    },
]


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def validate_brief(project_brief: object) -> dict:
    if not isinstance(project_brief, dict):
        return {
            "is_sufficient": False,
            "missing_fields": [],
            "vague_fields": [],
            "filled_assumptions": [],
            "error": "Project brief must be a JSON object (dict).",
        }

    missing_fields: list[str] = []
    vague_fields: list[str] = []
    filled_assumptions: list[dict] = []

    for field in REQUIRED_BRIEF_FIELDS:
        if field not in project_brief or _is_empty(project_brief.get(field)):
            missing_fields.append(field)

    # Simple vagueness heuristic.
    if _is_empty(project_brief.get("business_model")):
        vague_fields.append("business_model")
    if isinstance(project_brief.get("target_users"), list) and len(project_brief["target_users"]) <= 1:
        vague_fields.append("target_users")

    # Fill placeholders so downstream generation can proceed.
    for f in missing_fields:
        filled_assumptions.append(
            {
                "field": f,
                "assumption": f"Assumed unknown for missing field '{f}'.",
                "reason": "Field is missing or empty in the Project Brief.",
            }
        )
        if f not in project_brief:
            project_brief[f] = None

    is_sufficient = len(missing_fields) == 0 and len(vague_fields) == 0
    return {
        "is_sufficient": is_sufficient,
        "missing_fields": missing_fields,
        "vague_fields": vague_fields,
        "filled_assumptions": filled_assumptions,
    }


def generate_rag_queries(project_brief: dict, research_plan: dict) -> list[dict]:
    # Deterministic query templates aligned to research goals.
    product_name = project_brief.get("product_name", "") or ""
    core_problem = project_brief.get("core_problem", "") or ""
    platform = project_brief.get("platform", "") or ""
    business_model = project_brief.get("business_model", "") or ""

    queries = [
        {
            "query": (
                f"Target user analysis for '{product_name}' (core_problem='{core_problem}', platform='{platform}'): "
                "identify target user segments, summarize user needs, pain points, motivations."
            ),
            "target_goal_ids": ["G1"],
            "reason": "Need evidence for target user analysis.",
        },
        {
            "query": (
                f"Market context analysis for '{product_name}' (core_problem='{core_problem}'): "
                "identify market category, opportunities, challenges."
            ),
            "target_goal_ids": ["G2"],
            "reason": "Need evidence for market context analysis.",
        },
        {
            "query": (
                f"Competitor analysis for '{product_name}' (core_problem='{core_problem}'): "
                "identify competitors/alternatives and summarize positioning, strengths, weaknesses."
            ),
            "target_goal_ids": ["G3"],
            "reason": "Need evidence for competitor analysis.",
        },
        {
            "query": (
                f"Business model analysis for '{product_name}': "
                f"analyze the given business model ('{business_model}') and propose alternatives with pros/cons."
            ),
            "target_goal_ids": ["G4"],
            "reason": "Need evidence for business model analysis.",
        },
        {
            "query": (
                f"Risk analysis for '{product_name}': "
                "identify product risks, market risks, technical risks, and compliance risks if constraints mention compliance."
            ),
            "target_goal_ids": ["G5"],
            "reason": "Need evidence for risk analysis.",
        },
    ]
    return queries


def internal_rag_search(queries: list[dict]) -> list[dict]:
    # Use existing Chroma-backed KB.
    rag_results: list[dict] = []
    kb = get_kb()
    for q in queries:
        query_text = q.get("query", "")
        docs = kb.retrieve(query_text, agent="Research", k=4)
        # Normalize to the required format: {source_name, source_path, content, score}
        sources = []
        for idx, d in enumerate(docs):
            # kb.retrieve returns: {"doc": doc_text, "source_doc_id": ..., "kb": kb_name}
            sources.append(
                {
                    "source_name": d.get("kb", ""),
                    "source_path": d.get("source_doc_id", ""),
                    "content": d.get("doc", ""),
                    "score": 1.0 - (idx * 0.05),
                }
            )
        rag_results.append({"query": query_text, "target_goal_ids": q.get("target_goal_ids", []), "sources": sources})
    return rag_results


def summarize_rag_results_to_findings(
    rag_results: list[dict],
) -> list[dict]:
    # Convert rag sources into findings with lightweight heuristics.
    findings: list[dict] = []
    fid = 1
    for rr in rag_results:
        target_goals = rr.get("target_goal_ids", [])
        for src in (rr.get("sources") or [])[:2]:
            content = src.get("content", "") or ""
            text_sample = content.strip()
            text_sample = text_sample[:600]
            if not text_sample:
                continue
            confidence = "medium"
            limitations = ""
            if len(content) >= 250:
                confidence = "high"
            if any(tok in content.lower() for tok in ["template", "framework", "checklist"]):
                limitations = "This source may provide methodology/framework guidance rather than concrete facts."

            findings.append(
                {
                    "finding_id": f"RAG_F{fid}",
                    "source_type": "internal_rag",
                    "source_name": src.get("source_name", ""),
                    "source_path": src.get("source_path", ""),
                    "related_goal_ids": target_goals,
                    "finding": text_sample,
                    "confidence": confidence,
                    "limitations": limitations,
                }
            )
            fid += 1
    return findings


def evaluate_goal_satisfaction(
    research_plan: dict, findings: list[dict]
) -> list[dict]:
    # Heuristic satisfaction: whether a finding is linked to the goal and has enough content.
    goals = (research_plan.get("research_goals") or []) if isinstance(research_plan, dict) else []
    findings_by_goal: dict[str, list[dict]] = {}
    for f in findings:
        for gid in f.get("related_goal_ids", []) or []:
            findings_by_goal.setdefault(str(gid), []).append(f)

    goal_status: list[dict] = []
    for g in goals:
        gid = str(g.get("goal_id", ""))
        required_evidence = g.get("required_evidence", []) or []
        linked = findings_by_goal.get(gid, [])
        evidence_ids = [f.get("finding_id", "") for f in linked]
        if not linked:
            status = "unsatisfied"
            missing = ["No supporting evidence found from current findings."]
        else:
            # If any linked finding is high confidence, mark satisfied; else partially.
            has_high = any(f.get("confidence") == "high" for f in linked)
            status = "satisfied" if has_high else "partially_satisfied"
            missing = []
            if not has_high:
                missing.append("Evidence quality is insufficient for full satisfaction.")
            # Additional missing hints using required_evidence strings keywords.
            if required_evidence:
                joined = " ".join((f.get("finding", "") or "") for f in linked).lower()
                for ev in required_evidence:
                    key = ev.split()[0] if isinstance(ev, str) and ev else ""
                    if key and key not in joined:
                        missing.append(f"Missing evidence: {ev}")
                missing = missing[:3]

        goal_status.append(
            {
                "goal_id": gid,
                "status": status,
                "evidence_ids": [e for e in evidence_ids if e],
                "missing_information": missing,
            }
        )
    return goal_status


def generate_web_queries_from_goal_status(goal_status: list[dict], project_brief: dict) -> list[dict]:
    # Deterministic generation: create one query per unsatisfied/partially high priority goal.
    queries: list[dict] = []
    product_name = project_brief.get("product_name", "") or ""
    core_problem = project_brief.get("core_problem", "") or ""

    for gs in goal_status:
        gid = gs.get("goal_id")
        status = gs.get("status")
        missing_information = gs.get("missing_information", []) or []
        if status == "satisfied":
            continue
        reason = "; ".join(missing_information[:2]) if missing_information else "Missing evidence from internal RAG."
        queries.append(
            {
                "query": f"Find evidence for {gid} about '{product_name}' (core_problem='{core_problem}'). {reason}",
                "target_goal_ids": [gid],
                "reason": reason,
            }
        )
    return queries[:4]


def summarize_web_results_to_findings(
    web_queries: list[dict],
    web_results_map: dict[str, list[dict]],
) -> list[dict]:
    findings: list[dict] = []
    fid = 1000
    for q in web_queries:
        gid_list = q.get("target_goal_ids", []) or []
        query = q.get("query", "")
        results = web_results_map.get(query, []) or []
        for src in results[:2]:
            content = (src.get("content") or "").strip()
            text_sample = content[:600] if content else ""
            if not text_sample:
                continue
            findings.append(
                {
                    "finding_id": f"WEB_F{fid}",
                    "source_type": "web_search",
                    "source_name": src.get("source_name", ""),
                    "source_url": src.get("source_url", ""),
                    "source_path": "",
                    "related_goal_ids": gid_list,
                    "finding": text_sample,
                    "confidence": "medium",
                    "limitations": "Web evidence may be incomplete; verify sources.",
                }
            )
            fid += 1
    return findings


FINAL_SYSTEM = """You are the Research Agent.
Output ONLY a JSON object with keys:
- brief_summary (see template)
- research_plan
- rag_findings
- web_findings
- goal_status
- research_findings
- unresolved_gaps
- sources_used

Rules:
- Use provided findings/evidence; do not hallucinate facts.
- Every key must exist; keep arrays non-empty when possible.
- sources_used: include internal_rag (source_path_or_doc_id) and web_search (source_url).
"""


def research_agent(state: ProjectState) -> dict:
    brief = state.get("project_brief") or {}
    brief_validation = validate_brief(brief)
    # Always continue; do not hard-stop on missing fields.

    log_step(
        "research_agent_start",
        {
            "product_name": brief.get("product_name", ""),
            "is_brief_valid": bool(brief_validation.get("is_sufficient")),
            "missing_fields": brief_validation.get("missing_fields", []),
            "vague_fields": brief_validation.get("vague_fields", []),
        },
    )

    research_plan = {"research_objective": "Conduct structured research to support PM decision-making.", "research_goals": DEFAULT_RESEARCH_GOALS}

    state_max_rounds = 3
    max_web_search_rounds = state_max_rounds

    rag_queries = generate_rag_queries(brief if isinstance(brief, dict) else {}, research_plan)
    log_step("rag_queries_generated", {"count": len(rag_queries), "queries": [q.get("query", "")[:120] for q in (rag_queries or [])]})
    rag_results = internal_rag_search(rag_queries)
    log_step(
        "internal_rag_results",
        {
            "query_count": len(rag_results),
            "sources_per_query": [len(rr.get("sources") or []) for rr in rag_results],
            "top_source_per_query": [
                {
                    "source_name": (rr.get("sources") or [{}])[0].get("source_name", ""),
                    "source_path": (rr.get("sources") or [{}])[0].get("source_path", ""),
                }
                for rr in rag_results
            ],
        },
    )
    rag_findings = summarize_rag_results_to_findings(rag_results)
    log_step("rag_findings_summarized", {"count": len(rag_findings)})
    merged_findings = list(rag_findings)

    goal_status = evaluate_goal_satisfaction(research_plan, merged_findings)
    log_step(
        "goal_status_after_internal_rag",
        {
            "statuses": {
                "satisfied": sum(1 for gs in goal_status if gs.get("status") == "satisfied"),
                "partially_satisfied": sum(1 for gs in goal_status if gs.get("status") == "partially_satisfied"),
                "unsatisfied": sum(1 for gs in goal_status if gs.get("status") == "unsatisfied"),
            }
        },
    )
    web_queries: list[dict] = []
    web_findings: list[dict] = []
    web_round = 0

    while web_round < max_web_search_rounds and any(
        gs.get("status") in ("unsatisfied", "partially_satisfied") for gs in goal_status
    ):
        web_queries = generate_web_queries_from_goal_status(goal_status, brief if isinstance(brief, dict) else {})
        web_queries = web_queries or []
        if not web_queries:
            break

        log_step(
            "web_round_start",
            {
                "web_round": web_round,
                "max_web_search_rounds": max_web_search_rounds,
                "web_queries_count": len(web_queries),
                "web_queries": [q.get("query", "")[:120] for q in web_queries],
            },
        )

        # Execute web searches.
        web_results_map: dict[str, list[dict]] = {}
        for q in web_queries:
            query = q.get("query", "")
            results = web_search(query, limit=3)
            web_results_map[query] = results
            top1 = results[0] if results else {}
            log_step(
                "web_search_done",
                {
                    "web_round": web_round,
                    "query": query[:160],
                    "results_count": len(results),
                    "top1": {
                        "source_name": top1.get("source_name", ""),
                        "source_url": top1.get("source_url", ""),
                        "snippet": (top1.get("content", "") or "")[:160],
                    },
                },
            )

        new_web_findings = summarize_web_results_to_findings(web_queries, web_results_map)
        web_findings = new_web_findings if not web_findings else (web_findings + new_web_findings)
        merged_findings = list(rag_findings) + list(web_findings)
        log_step(
            "web_findings_updated",
            {
                "web_round": web_round,
                "new_web_findings_count": len(new_web_findings),
                "total_web_findings_count": len(web_findings),
            },
        )
        goal_status = evaluate_goal_satisfaction(research_plan, merged_findings)
        log_step(
            "goal_status_after_web_round",
            {
                "web_round": web_round,
                "statuses": {
                    "satisfied": sum(1 for gs in goal_status if gs.get("status") == "satisfied"),
                    "partially_satisfied": sum(1 for gs in goal_status if gs.get("status") == "partially_satisfied"),
                    "unsatisfied": sum(1 for gs in goal_status if gs.get("status") == "unsatisfied"),
                }
            },
        )
        web_round += 1

    unresolved_gaps: list[dict] = []
    for gs in goal_status:
        if gs.get("status") != "satisfied":
            for gap in (gs.get("missing_information") or [])[:3]:
                unresolved_gaps.append({"gap": gap, "related_goal_id": gs.get("goal_id"), "reason": "Not enough evidence."})

    log_step("unresolved_gaps_built", {"count": len(unresolved_gaps)})

    # sources_used for downstream transparency.
    sources_used: list[dict] = []
    for f in rag_findings:
        sources_used.append(
            {
                "source_type": "internal_rag",
                "source_name": f.get("source_name", ""),
                "source_path_or_url": f.get("source_path", ""),
                "used_for": f.get("related_goal_ids", []) or [],
            }
        )
    for f in web_findings:
        sources_used.append(
            {
                "source_type": "web_search",
                "source_name": f.get("source_name", ""),
                "source_path_or_url": f.get("source_url", "") or "",
                "used_for": f.get("related_goal_ids", []) or [],
            }
        )

    research_findings = {
        "market_context": "Derived from G2 findings.",
        "target_user_insights": [],
        "competitor_analysis": [],
        "business_model_insights": [],
        "risk_analysis": [],
    }

    # Final synthesis into required structured JSON via LLM to reduce formatting risk.
    prompt_payload = {
        "brief": brief,
        "brief_validation": brief_validation,
        "research_plan": research_plan,
        "rag_findings": rag_findings,
        "web_findings": web_findings,
        "goal_status": goal_status,
        "merged_findings": merged_findings,
        "unresolved_gaps": unresolved_gaps,
        "sources_used": sources_used,
    }
    resp = get_llm().invoke(
        [
            SystemMessage(content=FINAL_SYSTEM),
            HumanMessage(content=json.dumps(prompt_payload, ensure_ascii=False)),
        ]
    )
    report = extract_json(resp.content)
    fallback = not isinstance(report, dict) or "_raw" in report
    if not isinstance(report, dict) or "_raw" in report:
        # Fallback: return minimal JSON even if the model output is not valid.
        report = {
            "brief_summary": brief,
            "research_plan": research_plan,
            "rag_findings": rag_findings,
            "web_findings": web_findings,
            "goal_status": goal_status,
            "research_findings": research_findings,
            "unresolved_gaps": unresolved_gaps,
            "sources_used": sources_used,
        }
    log_step(
        "llm_report_ready",
        {
            "fallback_used": fallback,
            "rag_findings_count": len(rag_findings),
            "web_findings_count": len(web_findings),
            "unresolved_gaps_count": len(unresolved_gaps),
        },
    )

    return {
        "research_report": report,
        "citations": state.get("citations", []),
        "messages": [AIMessage(content=f"[Research] rag_findings={len(rag_findings)}, web_findings={len(web_findings)}")],
        "trace": append_trace(state, "research"),
    }
