"""Research Agent: structured market research using internal RAG + optional web search."""

from __future__ import annotations

import json
from typing import TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from backend.core.config import get_settings
from backend.core.state import ProjectState, append_trace
from backend.agents.web_research_agent import run_web_research_agent
from backend.llm.gemini import get_llm
from backend.rag.kb import get_kb
from backend.tools.web_search import web_search
from backend.utils.json_parse import extract_json
from backend.utils.debug_logger import log_llm_call_end, log_llm_call_start, log_step

_SETTINGS = get_settings()

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
    },
]


PLAN_AND_QUERY_SYSTEM = """You are the Research Agent planner.
Given a project brief, generate:
1) a concise research_plan
2) rag_queries aligned to the goals

Output ONLY a JSON object:
{
  "research_plan": {
    "research_objective": string,
    "research_goals": [
      {
        "goal_id": "G1" | "G2" | ...,
        "goal_name": string,
        "goal_description": string,
        "required_evidence": [string, ...],
        "priority": "high" | "medium" | "low"
      }
    ]
  },
  "rag_queries": [
    {
      "query": string,
      "target_goal_ids": [string, ...],
      "reason": string
    }
  ]
}

Rules:
- Use the brief context to tailor goals and queries.
- Keep goal count between 4 and 6.
- goal_id must be stable and start from G1.
- Every query must map to at least one valid goal_id.
- Return valid JSON only.
"""


RAG_FINDING_SUMMARY_SYSTEM = """You are summarizing one internal RAG passage for PM research.
Output ONLY a concise plain-text finding (1-3 sentences).

Rules:
- Use only information from the provided raw_text.
- Keep concrete and decision-useful details.
- Do not add facts not present in raw_text.
- Do not output JSON/markdown bullets.
"""


GOAL_EVALUATION_SYSTEM = """You are evaluating research goal satisfaction from findings.
Output ONLY JSON:
{
  "goal_status": [
    {
      "goal_id": string,
      "status": "satisfied" | "partially_satisfied" | "unsatisfied",
      "evidence_ids": [string, ...],
      "missing_information": [string, ...],
      "resolved_answers": [string, ...],
      "required_evidence_answers": [
        {
          "required_evidence": string,
          "covered": boolean,
          "answer": string,
          "evidence_ids": [string, ...]
        }
      ]
    }
  ]
}

Rules:
- Use only provided findings/evidence_ids.
- If status is satisfied, missing_information must be empty.
- required_evidence_answers must align with each required_evidence item.
- answer must be concise and evidence-grounded.
- Return valid JSON only.
"""


WEB_QUERY_SYSTEM = """You are generating web search queries for unresolved research gaps.
Output ONLY JSON:
{
  "web_queries": [
    {
      "query": string,
      "target_goal_ids": [string, ...],
      "reason": string
    }
  ]
}

Rules:
- Use project brief + current goal_status + existing findings to generate targeted gap-closing queries.
- Only generate queries for goals not fully satisfied.
- Each query must map to at least one unresolved goal_id.
- Keep each query specific and search-engine friendly.
- Return valid JSON only.
"""


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


def generate_plan_and_queries(project_brief: dict) -> tuple[dict, list[dict], bool]:
    default_plan = {
        "research_objective": "Conduct structured research to support PM decision-making.",
        "research_goals": DEFAULT_RESEARCH_GOALS,
    }
    default_queries = generate_rag_queries(project_brief, default_plan)

    payload = {"brief": project_brief, "default_goals_reference": DEFAULT_RESEARCH_GOALS}
    try:
        log_llm_call_start(
            "plan_and_query_generation",
            {
                "provider": _SETTINGS.llm_provider,
                "brief_keys": sorted(list(project_brief.keys())) if isinstance(project_brief, dict) else [],
            },
        )
        resp = get_llm().invoke(
            [
                SystemMessage(content=PLAN_AND_QUERY_SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ]
        )
        log_llm_call_end(
            "plan_and_query_generation",
            ok=True,
            response_chars=len(getattr(resp, "content", "") or ""),
        )
        parsed = extract_json(resp.content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM planner did not return a JSON object.")

        research_plan = parsed.get("research_plan")
        rag_queries = parsed.get("rag_queries")
        if not isinstance(research_plan, dict):
            raise ValueError("Missing or invalid research_plan.")
        if not isinstance(rag_queries, list) or not rag_queries:
            raise ValueError("Missing or invalid rag_queries.")

        goals = research_plan.get("research_goals")
        if not isinstance(goals, list) or not goals:
            raise ValueError("research_goals must be a non-empty list.")
        objective = research_plan.get("research_objective")
        if not isinstance(objective, str) or not objective.strip():
            research_plan["research_objective"] = default_plan["research_objective"]

        valid_goal_ids = set()
        normalized_goals = []
        for idx, g in enumerate(goals, start=1):
            if not isinstance(g, dict):
                continue
            gid = g.get("goal_id")
            if not isinstance(gid, str) or not gid.strip():
                gid = f"G{idx}"
            goal_name = g.get("goal_name")
            goal_desc = g.get("goal_description")
            required_evidence = g.get("required_evidence")
            if not isinstance(goal_name, str) or not goal_name.strip():
                continue
            if not isinstance(goal_desc, str) or not goal_desc.strip():
                continue
            if not isinstance(required_evidence, list) or not required_evidence:
                continue
            cleaned_evidence = [x for x in required_evidence if isinstance(x, str) and x.strip()]
            if not cleaned_evidence:
                continue
            priority = g.get("priority")
            if priority not in {"high", "medium", "low"}:
                priority = "high"
            normalized_goal = {
                "goal_id": gid,
                "goal_name": goal_name.strip(),
                "goal_description": goal_desc.strip(),
                "required_evidence": cleaned_evidence[:6],
                "priority": priority,
            }
            valid_goal_ids.add(gid)
            normalized_goals.append(normalized_goal)
        if not normalized_goals:
            raise ValueError("No valid goals produced by LLM planner.")
        research_plan["research_goals"] = normalized_goals

        normalized_queries = []
        for q in rag_queries:
            if not isinstance(q, dict):
                continue
            query = q.get("query")
            reason = q.get("reason")
            target_goal_ids = q.get("target_goal_ids")
            if not isinstance(query, str) or not query.strip():
                continue
            if not isinstance(reason, str) or not reason.strip():
                reason = "Need evidence for research goal."
            if not isinstance(target_goal_ids, list):
                target_goal_ids = []
            mapped_ids = [gid for gid in target_goal_ids if isinstance(gid, str) and gid in valid_goal_ids]
            if not mapped_ids:
                # Fallback map by first goal so the query remains usable.
                mapped_ids = [normalized_goals[0]["goal_id"]]
            normalized_queries.append(
                {
                    "query": query.strip(),
                    "target_goal_ids": mapped_ids,
                    "reason": reason.strip(),
                }
            )
        if not normalized_queries:
            raise ValueError("No valid rag_queries produced by LLM planner.")

        return research_plan, normalized_queries, False
    except Exception as exc:
        log_llm_call_end("plan_and_query_generation", ok=False, error=str(exc)[:200])
        log_step("plan_query_llm_fallback", {"reason": str(exc)[:200]})
        return default_plan, default_queries, True


def internal_rag_search(queries: list[dict]) -> list[dict]:
    # Use existing Milvus-backed KB.
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
    # Convert rag sources into findings; each raw_text is summarized by LLM.
    findings: list[dict] = []
    fid = 1
    for rr in rag_results:
        target_goals = rr.get("target_goal_ids", [])
        for src in (rr.get("sources") or [])[:2]:
            content = src.get("content", "") or ""
            raw_text = content.strip()
            if not raw_text:
                continue
            finding_text = raw_text[:600]
            llm_fallback = False
            try:
                summary_payload = {
                    "query_context": rr.get("query", ""),
                    "target_goal_ids": target_goals,
                    "raw_text": raw_text,
                }
                log_llm_call_start(
                    "rag_finding_summary",
                    {
                        "query_context": (rr.get("query", "") or "")[:120],
                        "source_name": src.get("source_name", ""),
                        "source_path": src.get("source_path", ""),
                        "raw_text_chars": len(raw_text),
                    },
                )
                resp = get_llm().invoke(
                    [
                        SystemMessage(content=RAG_FINDING_SUMMARY_SYSTEM),
                        HumanMessage(content=json.dumps(summary_payload, ensure_ascii=False)),
                    ]
                )
                log_llm_call_end(
                    "rag_finding_summary",
                    ok=True,
                    response_chars=len(getattr(resp, "content", "") or ""),
                )
                candidate = (resp.content or "").strip() if hasattr(resp, "content") else ""
                if candidate:
                    finding_text = candidate
                else:
                    llm_fallback = True
            except Exception as exc:
                log_llm_call_end("rag_finding_summary", ok=False, error=str(exc)[:200])
                llm_fallback = True

            confidence = "medium"
            limitations = ""
            if len(content) >= 250:
                confidence = "high"
            if any(tok in content.lower() for tok in ["template", "framework", "checklist"]):
                limitations = "This source may provide methodology/framework guidance rather than concrete facts."
            if llm_fallback:
                limitations = (limitations + " " if limitations else "") + "LLM summary fallback to raw text truncation."

            findings.append(
                {
                    "finding_id": f"RAG_F{fid}",
                    "source_type": "internal_rag",
                    "source_name": src.get("source_name", ""),
                    "source_path": src.get("source_path", ""),
                    "query": rr.get("query", ""),
                    "related_goal_ids": target_goals,
                    "finding": finding_text,
                    # Keep original retrieved text for traceability/debugging.
                    "raw_text": raw_text,
                    "confidence": confidence,
                    "limitations": limitations,
                }
            )
            fid += 1
    return findings


def evaluate_goal_satisfaction(
    research_plan: dict, findings: list[dict]
) -> list[dict]:
    # LLM-driven satisfaction with deterministic fallback and strict normalization.
    goals = (research_plan.get("research_goals") or []) if isinstance(research_plan, dict) else []
    findings_by_goal: dict[str, list[dict]] = {}
    for f in findings:
        for gid in f.get("related_goal_ids", []) or []:
            findings_by_goal.setdefault(str(gid), []).append(f)

    heuristic_goal_status: list[dict] = []
    for g in goals:
        gid = str(g.get("goal_id", ""))
        required_evidence = g.get("required_evidence", []) or []
        linked = findings_by_goal.get(gid, [])
        evidence_ids = [f.get("finding_id", "") for f in linked]
        required_evidence_answers: list[dict] = []

        def _clean_answer_text(text: str) -> str:
            t = (text or "").replace("\n", " ").replace("|", " ")
            t = " ".join(t.split()).strip()
            # Trim long raw chunk tails to keep a readable synthesized answer.
            return t[:320]

        def _best_answer_for_requirement(ev: str) -> tuple[str, list[str], bool]:
            ev_text = (ev or "").strip()
            if not ev_text:
                return "", [], False
            tokens = [
                t
                for t in ev_text.lower().split()
                if len(t) > 2 and t not in {"the", "and", "for", "with", "from"}
            ]
            best = None
            best_score = -1
            for f in linked:
                text = (f.get("finding", "") or "").lower()
                if not text:
                    continue
                score = sum(1 for t in tokens if t in text)
                if score > best_score:
                    best = f
                    best_score = score
            if best and best_score > 0:
                return (
                    _clean_answer_text(best.get("finding", "") or ""),
                    [best.get("finding_id", "")] if best.get("finding_id") else [],
                    True,
                )
            return "", [], False

        if not linked:
            status = "unsatisfied"
            missing = ["No supporting evidence found from current findings."]
            resolved_answers: list[str] = []
            if isinstance(required_evidence, list):
                for ev in required_evidence:
                    if not isinstance(ev, str):
                        continue
                    required_evidence_answers.append(
                        {
                            "required_evidence": ev,
                            "covered": False,
                            "answer": "",
                            "evidence_ids": [],
                        }
                    )
        else:
            # Determine status by required_evidence coverage, not just confidence.
            status = "partially_satisfied"
            missing = []
            resolved_answers = []
            # Additional missing hints using required_evidence strings keywords.
            if required_evidence:
                covered_count = 0
                for ev in required_evidence:
                    if not isinstance(ev, str):
                        continue
                    answer_text, answer_ids, covered = _best_answer_for_requirement(ev)
                    required_evidence_answers.append(
                        {
                            "required_evidence": ev,
                            "covered": covered,
                            "answer": answer_text,
                            "evidence_ids": answer_ids,
                        }
                    )
                    if covered:
                        covered_count += 1
                        resolved_answers.append(f"Covered: {ev} -> {answer_text}")
                    else:
                        missing.append(f"Missing evidence: {ev}")
                if covered_count == len(required_evidence):
                    status = "satisfied"
                elif covered_count == 0:
                    status = "unsatisfied"
                else:
                    status = "partially_satisfied"
            else:
                # No explicit requirements: fallback by existence of linked evidence.
                status = "satisfied" if linked else "unsatisfied"

            if status == "satisfied":
                missing = []
            else:
                missing = missing[:5]
            resolved_answers = resolved_answers[:5]

        heuristic_goal_status.append(
            {
                "goal_id": gid,
                "status": status,
                "evidence_ids": [e for e in evidence_ids if e],
                "missing_information": missing,
                "resolved_answers": resolved_answers,
                "required_evidence_answers": required_evidence_answers,
            }
        )

    # LLM refinement for status/answers.
    llm_goal_status: list[dict] = []
    try:
        payload = {
            "research_goals": goals,
            "findings": [
                {
                    "finding_id": f.get("finding_id", ""),
                    "related_goal_ids": f.get("related_goal_ids", []),
                    "finding": f.get("finding", ""),
                    "raw_text": f.get("raw_text", ""),
                    "source_type": f.get("source_type", ""),
                    "source_name": f.get("source_name", ""),
                }
                for f in findings
                if isinstance(f, dict)
            ],
            "heuristic_goal_status_reference": heuristic_goal_status,
        }
        log_llm_call_start(
            "goal_satisfaction_evaluation",
            {"goal_count": len(goals), "finding_count": len(findings)},
        )
        resp = get_llm().invoke(
            [
                SystemMessage(content=GOAL_EVALUATION_SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ]
        )
        log_llm_call_end(
            "goal_satisfaction_evaluation",
            ok=True,
            response_chars=len(getattr(resp, "content", "") or ""),
        )
        parsed = extract_json(resp.content)
        if isinstance(parsed, dict) and isinstance(parsed.get("goal_status"), list):
            llm_goal_status = parsed.get("goal_status", [])
    except Exception as exc:
        log_llm_call_end("goal_satisfaction_evaluation", ok=False, error=str(exc)[:200])
        log_step("goal_eval_llm_fallback", {"reason": str(exc)[:200]})

    # Normalize and align goal statuses.
    valid_finding_ids = {
        str(f.get("finding_id"))
        for f in findings
        if isinstance(f, dict) and isinstance(f.get("finding_id"), str) and f.get("finding_id")
    }
    llm_map = {
        str(gs.get("goal_id", "")): gs
        for gs in llm_goal_status
        if isinstance(gs, dict) and isinstance(gs.get("goal_id"), str)
    }
    final_goal_status: list[dict] = []
    for hs in heuristic_goal_status:
        gid = str(hs.get("goal_id", ""))
        ref = llm_map.get(gid, {}) if isinstance(llm_map.get(gid, {}), dict) else {}
        status = ref.get("status", hs.get("status", "unsatisfied"))
        if status not in {"satisfied", "partially_satisfied", "unsatisfied"}:
            status = hs.get("status", "unsatisfied")

        evid = ref.get("evidence_ids", hs.get("evidence_ids", []))
        if not isinstance(evid, list):
            evid = hs.get("evidence_ids", [])
        evid = [e for e in evid if isinstance(e, str) and e in valid_finding_ids]

        missing = ref.get("missing_information", hs.get("missing_information", []))
        if not isinstance(missing, list):
            missing = hs.get("missing_information", [])
        missing = [m for m in missing if isinstance(m, str)]

        resolved = ref.get("resolved_answers", hs.get("resolved_answers", []))
        if not isinstance(resolved, list):
            resolved = hs.get("resolved_answers", [])
        resolved = [r for r in resolved if isinstance(r, str)]

        rea_ref = ref.get("required_evidence_answers", hs.get("required_evidence_answers", []))
        if not isinstance(rea_ref, list):
            rea_ref = hs.get("required_evidence_answers", [])
        rea_map = {}
        for item in rea_ref:
            if not isinstance(item, dict):
                continue
            req = item.get("required_evidence")
            if isinstance(req, str) and req.strip():
                rea_map[req.strip()] = item

        normalized_rea = []
        for item in hs.get("required_evidence_answers", []):
            if not isinstance(item, dict):
                continue
            req = item.get("required_evidence", "")
            src_item = rea_map.get(req, item)
            covered = bool(src_item.get("covered", item.get("covered", False)))
            answer = src_item.get("answer", item.get("answer", ""))
            if not isinstance(answer, str):
                answer = item.get("answer", "")
            ev_ids = src_item.get("evidence_ids", item.get("evidence_ids", []))
            if not isinstance(ev_ids, list):
                ev_ids = item.get("evidence_ids", [])
            ev_ids = [e for e in ev_ids if isinstance(e, str) and e in valid_finding_ids]
            normalized_rea.append(
                {
                    "required_evidence": req,
                    "covered": covered,
                    "answer": answer.strip(),
                    "evidence_ids": ev_ids,
                }
            )

        if status == "satisfied":
            missing = []

        final_goal_status.append(
            {
                "goal_id": gid,
                "status": status,
                "evidence_ids": evid,
                "missing_information": missing[:5],
                "resolved_answers": resolved[:5],
                "required_evidence_answers": normalized_rea,
            }
        )
    return final_goal_status


def generate_web_queries_from_goal_status(goal_status: list[dict], project_brief: dict) -> list[dict]:
    # Deterministic fallback generation: create one query per unsatisfied/partially high priority goal.
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


def generate_web_queries_with_llm(
    goal_status: list[dict], project_brief: dict, findings: list[dict]
) -> tuple[list[dict], bool]:
    fallback_queries = generate_web_queries_from_goal_status(goal_status, project_brief)
    unresolved_goal_ids = {
        str(gs.get("goal_id", ""))
        for gs in goal_status
        if isinstance(gs, dict) and gs.get("status") in ("unsatisfied", "partially_satisfied")
    }
    unresolved_goal_ids = {gid for gid in unresolved_goal_ids if gid}
    if not unresolved_goal_ids:
        return [], False

    try:
        payload = {
            "brief": project_brief,
            "goal_status": goal_status,
            "findings": [
                {
                    "finding_id": f.get("finding_id", ""),
                    "related_goal_ids": f.get("related_goal_ids", []),
                    "finding": f.get("finding", ""),
                    "source_type": f.get("source_type", ""),
                }
                for f in findings
                if isinstance(f, dict)
            ],
            "fallback_queries_reference": fallback_queries,
        }
        log_llm_call_start(
            "web_query_generation",
            {"unresolved_goal_count": len(unresolved_goal_ids), "finding_count": len(findings)},
        )
        resp = get_llm().invoke(
            [
                SystemMessage(content=WEB_QUERY_SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ]
        )
        log_llm_call_end(
            "web_query_generation",
            ok=True,
            response_chars=len(getattr(resp, "content", "") or ""),
        )
        parsed = extract_json(resp.content)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("web_queries"), list):
            raise ValueError("LLM web query output schema invalid.")

        normalized: list[dict] = []
        for q in parsed.get("web_queries", []):
            if not isinstance(q, dict):
                continue
            query = q.get("query")
            reason = q.get("reason")
            target_goal_ids = q.get("target_goal_ids")
            if not isinstance(query, str) or not query.strip():
                continue
            if not isinstance(reason, str) or not reason.strip():
                reason = "Missing evidence from current findings."
            if not isinstance(target_goal_ids, list):
                target_goal_ids = []
            mapped_ids = [
                gid
                for gid in target_goal_ids
                if isinstance(gid, str) and gid in unresolved_goal_ids
            ]
            if not mapped_ids:
                continue
            normalized.append(
                {
                    "query": query.strip(),
                    "target_goal_ids": mapped_ids,
                    "reason": reason.strip(),
                }
            )
        if not normalized:
            raise ValueError("No valid LLM web queries.")
        return normalized[:4], False
    except Exception as exc:
        log_llm_call_end("web_query_generation", ok=False, error=str(exc)[:200])
        log_step("web_query_llm_fallback", {"reason": str(exc)[:200]})
        return fallback_queries, True


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


def _normalize_report_schema(
    report: dict,
    *,
    brief: dict,
    research_plan: dict,
    rag_findings: list[dict],
    web_findings: list[dict],
    goal_status: list[dict],
    unresolved_gaps: list[dict],
    sources_used: list[dict],
) -> dict:
    """Stabilize LLM output schema and keep cross-field consistency."""
    out = dict(report or {})

    # brief_summary should be an object for stable downstream rendering.
    if not isinstance(out.get("brief_summary"), dict):
        out["brief_summary"] = brief

    # research_plan should be dict with research_goals.
    rp = out.get("research_plan")
    if isinstance(rp, list):
        out["research_plan"] = {
            "research_objective": "Conduct structured research to support PM decision-making.",
            "research_goals": rp,
        }
    elif not isinstance(rp, dict):
        out["research_plan"] = research_plan
    elif not isinstance(rp.get("research_goals"), list):
        out["research_plan"] = research_plan

    # research_goals should not include runtime status field.
    goals = out.get("research_plan", {}).get("research_goals", [])
    if isinstance(goals, list):
        normalized_goals = []
        for g in goals:
            if not isinstance(g, dict):
                continue
            g2 = dict(g)
            g2.pop("status", None)
            normalized_goals.append(g2)
        out["research_plan"]["research_goals"] = normalized_goals

    # findings should be list[dict], otherwise fallback to deterministic findings.
    if not isinstance(out.get("rag_findings"), list):
        out["rag_findings"] = rag_findings
    if not isinstance(out.get("web_findings"), list):
        out["web_findings"] = web_findings

    out["rag_findings"] = [f for f in out.get("rag_findings", []) if isinstance(f, dict)]
    out["web_findings"] = [f for f in out.get("web_findings", []) if isinstance(f, dict)]

    # Ensure each finding has a stable finding_id.
    for i, f in enumerate(out["rag_findings"], start=1):
        if not f.get("finding_id"):
            f["finding_id"] = f"RAG_F{i}"
    for i, f in enumerate(out["web_findings"], start=1000):
        if not f.get("finding_id"):
            f["finding_id"] = f"WEB_F{i}"

    valid_evidence_ids = {
        str(f.get("finding_id"))
        for f in (out["rag_findings"] + out["web_findings"])
        if f.get("finding_id")
    }

    # Ensure each RAG finding includes original retrieved text.
    rag_ref_by_id = {
        str(f.get("finding_id")): f
        for f in rag_findings
        if isinstance(f, dict) and f.get("finding_id")
    }
    for f in out["rag_findings"]:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("finding_id", ""))
        ref = rag_ref_by_id.get(fid, {})
        if not isinstance(f.get("raw_text"), str) or not f.get("raw_text", "").strip():
            raw = ref.get("raw_text") or ref.get("finding") or ""
            if not raw:
                raw = f.get("finding") or f.get("summary") or ""
            f["raw_text"] = raw

    # goal_status should only reference evidence IDs that actually exist.
    goal_status_ref: dict[str, dict] = {
        str(gs.get("goal_id", "")): gs for gs in goal_status if isinstance(gs, dict)
    }
    if not isinstance(out.get("goal_status"), list):
        out["goal_status"] = goal_status
    else:
        fixed_goal_status = []
        for gs in out["goal_status"]:
            if not isinstance(gs, dict):
                continue
            evid = gs.get("evidence_ids", [])
            if not isinstance(evid, list):
                evid = []
            gs["evidence_ids"] = [e for e in evid if isinstance(e, str) and e in valid_evidence_ids]
            if not isinstance(gs.get("missing_information"), list):
                gs["missing_information"] = []
            if not isinstance(gs.get("resolved_answers"), list):
                gs["resolved_answers"] = []
            rea = gs.get("required_evidence_answers", [])
            if not isinstance(rea, list) or not rea:
                ref = goal_status_ref.get(str(gs.get("goal_id", "")), {})
                rea = ref.get("required_evidence_answers", []) if isinstance(ref, dict) else []
            if not isinstance(rea, list):
                rea = []
            normalized_rea = []
            for item in rea:
                if not isinstance(item, dict):
                    continue
                ev_ids = item.get("evidence_ids", [])
                if not isinstance(ev_ids, list):
                    ev_ids = []
                normalized_rea.append(
                    {
                        "required_evidence": item.get("required_evidence", ""),
                        "covered": bool(item.get("covered", False)),
                        "answer": item.get("answer", "") or "",
                        "evidence_ids": [e for e in ev_ids if isinstance(e, str) and e in valid_evidence_ids],
                    }
                )
            gs["required_evidence_answers"] = normalized_rea
            if gs.get("status") == "satisfied":
                gs["missing_information"] = []
            fixed_goal_status.append(gs)
        out["goal_status"] = fixed_goal_status if fixed_goal_status else goal_status

    # Keep research_findings as list for display consistency.
    if not isinstance(out.get("research_findings"), list):
        rf = out.get("research_findings")
        if isinstance(rf, str) and rf.strip():
            out["research_findings"] = [rf.strip()]
        else:
            out["research_findings"] = []
    # If research_findings is effectively a copy of raw findings, synthesize concise conclusions from goal answers.
    if isinstance(out.get("research_findings"), list):
        rf = out["research_findings"]
        looks_like_raw_findings = any(
            isinstance(x, dict) and str(x.get("finding_id", "")).startswith(("RAG_F", "WEB_F"))
            for x in rf
        )
        if not rf or looks_like_raw_findings:
            synthesized: list[str] = []
            for gs in out.get("goal_status", []):
                if not isinstance(gs, dict):
                    continue
                gid = gs.get("goal_id", "")
                answers = gs.get("required_evidence_answers", []) or []
                covered_answers = [
                    a.get("answer", "")
                    for a in answers
                    if isinstance(a, dict) and a.get("covered") and isinstance(a.get("answer"), str) and a.get("answer").strip()
                ]
                if covered_answers:
                    synthesized.append(f"{gid}: {covered_answers[0]}")
            out["research_findings"] = synthesized[:8]

    # unresolved_gaps should be list.
    if not isinstance(out.get("unresolved_gaps"), list):
        out["unresolved_gaps"] = unresolved_gaps

    # sources_used should include used_for mapping when possible.
    if not isinstance(out.get("sources_used"), list) or not out.get("sources_used"):
        out["sources_used"] = sources_used
    else:
        normalized_sources: list[dict] = []
        for s in out["sources_used"]:
            if not isinstance(s, dict):
                continue
            used_for = s.get("used_for", [])
            if not isinstance(used_for, list):
                used_for = []
            s["used_for"] = [x for x in used_for if isinstance(x, str)]
            normalized_sources.append(s)
        out["sources_used"] = normalized_sources if normalized_sources else sources_used

    # Guarantee required keys are present.
    out.setdefault("brief_summary", brief)
    out.setdefault("research_plan", research_plan)
    out.setdefault("rag_findings", rag_findings)
    out.setdefault("web_findings", web_findings)
    out.setdefault("goal_status", goal_status)
    out.setdefault("research_findings", [])
    out.setdefault("unresolved_gaps", unresolved_gaps)
    out.setdefault("sources_used", sources_used)
    return out


FINAL_SYSTEM = """You are the Research Agent.
Output ONLY a JSON object with keys:
- brief_summary (see template)
- research_plan
- rag_findings
- web_findings
- web_search_status
- goal_status
- research_findings
- unresolved_gaps
- sources_used

Rules:
- Use provided findings/evidence; do not hallucinate facts.
- Every key must exist; keep arrays non-empty when possible.
- sources_used: include internal_rag (source_path_or_doc_id) and web_search (source_url).
"""


class ResearchNodeState(TypedDict):
    brief: dict
    brief_validation: dict
    research_plan: dict
    rag_queries: list[dict]
    rag_results: list[dict]
    rag_findings: list[dict]
    web_findings: list[dict]
    merged_findings: list[dict]
    goal_status: list[dict]
    web_queries: list[dict]
    web_round: int
    max_web_search_rounds: int
    unresolved_gaps: list[dict]
    sources_used: list[dict]
    report: dict
    citations: list[dict]
    plan_query_fallback: bool
    web_query_fallback: bool
    web_search_status: dict


def _research_init_node(state: ResearchNodeState) -> dict:
    brief = state.get("brief") or {}
    brief_validation = validate_brief(brief)
    log_step(
        "research_agent_start",
        {
            "product_name": brief.get("product_name", ""),
            "is_brief_valid": bool(brief_validation.get("is_sufficient")),
            "missing_fields": brief_validation.get("missing_fields", []),
            "vague_fields": brief_validation.get("vague_fields", []),
        },
    )
    return {
        "brief": brief if isinstance(brief, dict) else {},
        "brief_validation": brief_validation,
        "web_round": 0,
        "max_web_search_rounds": 1,
        "web_findings": [],
        "merged_findings": [],
        "goal_status": [],
        "web_queries": [],
        "unresolved_gaps": [],
        "sources_used": [],
        "report": {},
        "citations": [],
        "web_search_status": {"attempted": False, "success": False, "failure_reasons": []},
    }


def _research_plan_node(state: ResearchNodeState) -> dict:
    brief = state.get("brief") or {}
    research_plan, rag_queries, plan_query_fallback = generate_plan_and_queries(brief)
    log_step(
        "plan_and_queries_ready",
        {
            "fallback_used": plan_query_fallback,
            "goal_count": len(research_plan.get("research_goals", []))
            if isinstance(research_plan, dict)
            else 0,
            "query_count": len(rag_queries),
        },
    )
    return {
        "research_plan": research_plan,
        "rag_queries": rag_queries,
        "plan_query_fallback": plan_query_fallback,
    }


def _research_rag_node(state: ResearchNodeState) -> dict:
    rag_queries = state.get("rag_queries", [])
    research_plan = state.get("research_plan", {})
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
    return {
        "rag_results": rag_results,
        "rag_findings": rag_findings,
        "merged_findings": merged_findings,
        "goal_status": goal_status,
        "web_findings": [],
    }


def _web_loop_router(state: ResearchNodeState) -> str:
    goal_status = state.get("goal_status", [])
    web_round = state.get("web_round", 0)
    max_rounds = state.get("max_web_search_rounds", 0)
    if web_round >= max_rounds:
        return "finalize"
    if not any(gs.get("status") in ("unsatisfied", "partially_satisfied") for gs in goal_status):
        return "finalize"
    return "web_round"


def _research_web_round_node(state: ResearchNodeState) -> dict:
    goal_status = state.get("goal_status", [])
    brief = state.get("brief", {})
    merged_findings = state.get("merged_findings", [])
    web_round = state.get("web_round", 0)
    max_web_search_rounds = state.get("max_web_search_rounds", 0)
    rag_findings = state.get("rag_findings", [])
    web_findings = state.get("web_findings", [])
    research_plan = state.get("research_plan", {})
    prev_status = state.get("web_search_status", {"attempted": False, "success": False, "failure_reasons": []})

    web_queries, web_query_fallback = generate_web_queries_with_llm(goal_status, brief, merged_findings)
    web_queries = web_queries or []
    if not web_queries:
        return {"web_round": max_web_search_rounds, "web_queries": [], "web_query_fallback": web_query_fallback}

    log_step(
        "web_round_start",
        {
            "web_round": web_round,
            "max_web_search_rounds": max_web_search_rounds,
            "fallback_used": web_query_fallback,
            "web_queries_count": len(web_queries),
            "web_queries": [q.get("query", "")[:120] for q in web_queries],
        },
    )

    unresolved_goal_ids = [
        str(gs.get("goal_id", ""))
        for gs in goal_status
        if isinstance(gs, dict) and gs.get("status") in ("unsatisfied", "partially_satisfied")
    ]
    web_result = run_web_research_agent(
        web_queries=web_queries,
        unresolved_goal_ids=[x for x in unresolved_goal_ids if x],
        round_id=web_round,
        max_open_per_query=2,
    )
    new_web_findings = web_result.get("web_findings", [])
    round_status = web_result.get("web_search_status", {})
    if not isinstance(round_status, dict):
        round_status = {"attempted": True, "success": False, "failure_reasons": ["INVALID_WEB_STATUS"]}

    merged_failures = []
    old_failures = prev_status.get("failure_reasons", []) if isinstance(prev_status, dict) else []
    new_failures = round_status.get("failure_reasons", []) if isinstance(round_status, dict) else []
    for item in (old_failures or []) + (new_failures or []):
        if isinstance(item, str) and item and item not in merged_failures:
            merged_failures.append(item)
    web_search_status = {
        "attempted": True,
        "success": bool((prev_status or {}).get("success", False)) or bool(round_status.get("success", False)),
        "failure_reasons": merged_failures[:10],
        "queries_attempted": int(round_status.get("queries_attempted", len(web_queries)) or len(web_queries)),
        "urls_opened": int(round_status.get("urls_opened", 0) or 0),
    }

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
            },
        },
    )
    return {
        "web_queries": web_queries,
        "web_query_fallback": web_query_fallback,
        "web_findings": web_findings,
        "merged_findings": merged_findings,
        "goal_status": goal_status,
        "web_round": web_round + 1,
        "web_search_status": web_search_status,
    }


def _research_finalize_node(state: ResearchNodeState) -> dict:
    brief = state.get("brief", {})
    brief_validation = state.get("brief_validation", {})
    research_plan = state.get("research_plan", {})
    rag_findings = state.get("rag_findings", [])
    web_findings = state.get("web_findings", [])
    merged_findings = state.get("merged_findings", [])
    goal_status = state.get("goal_status", [])
    web_search_status = state.get("web_search_status", {"attempted": False, "success": False, "failure_reasons": []})
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
        "web_search_status": web_search_status,
    }
    log_llm_call_start(
        "final_report_synthesis",
        {
            "rag_findings_count": len(rag_findings),
            "web_findings_count": len(web_findings),
            "goal_status_count": len(goal_status),
        },
    )
    try:
        resp = get_llm().invoke(
            [
                SystemMessage(content=FINAL_SYSTEM),
                HumanMessage(content=json.dumps(prompt_payload, ensure_ascii=False)),
            ]
        )
        log_llm_call_end(
            "final_report_synthesis",
            ok=True,
            response_chars=len(getattr(resp, "content", "") or ""),
        )
    except Exception as exc:
        log_llm_call_end("final_report_synthesis", ok=False, error=str(exc)[:200])
        raise
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
            "web_search_status": web_search_status,
        }
    report = _normalize_report_schema(
        report,
        brief=brief if isinstance(brief, dict) else {},
        research_plan=research_plan,
        rag_findings=rag_findings,
        web_findings=web_findings,
        goal_status=goal_status,
        unresolved_gaps=unresolved_gaps,
        sources_used=sources_used,
    )
    if not isinstance(report.get("web_search_status"), dict):
        report["web_search_status"] = web_search_status
    log_step(
        "llm_report_ready",
        {
            "fallback_used": fallback,
            "rag_findings_count": len(rag_findings),
            "web_findings_count": len(web_findings),
            "unresolved_gaps_count": len(unresolved_gaps),
            "final_goal_status_count": len(report.get("goal_status", [])),
        },
    )

    citations: list[dict] = []
    for gs in report.get("goal_status", []) if isinstance(report, dict) else []:
        if not isinstance(gs, dict):
            continue
        for item in gs.get("required_evidence_answers", []) or []:
            if not isinstance(item, dict):
                continue
            ev_ids = item.get("evidence_ids", [])
            if not isinstance(ev_ids, list):
                ev_ids = []
            answer = (item.get("answer") or "").strip() if isinstance(item.get("answer"), str) else ""
            if answer and ev_ids:
                citations.append(
                    {
                        "goal_id": gs.get("goal_id", ""),
                        "required_evidence": item.get("required_evidence", ""),
                        "claim": answer,
                        "source_ids": [x for x in ev_ids if isinstance(x, str)],
                    }
                )
    return {
        "unresolved_gaps": unresolved_gaps,
        "sources_used": sources_used,
        "web_search_status": web_search_status,
        "report": report,
        "citations": citations,
    }


def _build_research_subgraph():
    g = StateGraph(ResearchNodeState)
    g.add_node("init", _research_init_node)
    g.add_node("plan", _research_plan_node)
    g.add_node("rag", _research_rag_node)
    g.add_node("web_round", _research_web_round_node)
    g.add_node("finalize", _research_finalize_node)
    g.add_edge(START, "init")
    g.add_edge("init", "plan")
    g.add_edge("plan", "rag")
    g.add_conditional_edges(
        "rag",
        _web_loop_router,
        {"web_round": "web_round", "finalize": "finalize"},
    )
    g.add_conditional_edges(
        "web_round",
        _web_loop_router,
        {"web_round": "web_round", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)
    return g.compile()


_research_subgraph_app = None


def _get_research_subgraph():
    global _research_subgraph_app
    if _research_subgraph_app is None:
        _research_subgraph_app = _build_research_subgraph()
    return _research_subgraph_app


def research_agent(state: ProjectState) -> dict:
    subgraph_state = _get_research_subgraph().invoke({"brief": state.get("project_brief") or {}})
    report = subgraph_state.get("report", {})
    citations = subgraph_state.get("citations", [])
    rag_findings = report.get("rag_findings", []) if isinstance(report, dict) else []
    web_findings = report.get("web_findings", []) if isinstance(report, dict) else []
    return {
        "research_report": report,
        "citations": citations,
        "messages": [AIMessage(content=f"[Research] rag_findings={len(rag_findings)}, web_findings={len(web_findings)}")],
        "trace": append_trace(state, "research"),
    }
