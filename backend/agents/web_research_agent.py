from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm.gemini import get_llm
from backend.tools.web_fetch import fetch_webpage_text
from backend.tools.web_search import web_search
from backend.utils.debug_logger import log_llm_call_end, log_llm_call_start, log_step
from backend.utils.json_parse import extract_json

OPEN_DECISION_SYSTEM = """You are deciding whether to open a search result page for research.
Return JSON only: {"should_open": boolean, "reason": string, "related_goal_ids": [string, ...]}.
Rules:
- Prefer sources that can provide concrete evidence for unresolved goals.
- Skip obvious irrelevant/low-value pages.
- Keep related_goal_ids within unresolved_goal_ids.
"""

PAGE_SUMMARY_SYSTEM = """Summarize webpage text as one structured finding.
Return JSON only:
{
  "finding": string,
  "related_goal_ids": [string, ...],
  "confidence": "low" | "medium" | "high",
  "limitations": string
}
Rules:
- Use only provided page_text.
- Keep finding concise and factual.
"""


def run_web_research_agent(
    *,
    web_queries: list[dict[str, Any]],
    unresolved_goal_ids: list[str],
    round_id: int,
    max_open_per_query: int = 2,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    failure_reasons: list[str] = []
    opened_urls = 0

    for q in web_queries:
        query = q.get("query", "")
        if not isinstance(query, str) or not query.strip():
            continue
        results = web_search(query, limit=5)
        if not results:
            failure_reasons.append("SERP_PARSE_FAILED_OR_NO_RESULTS")
            log_step("web_research_no_results", {"query": query, "round": round_id}, level="WARN")
            continue

        opened_for_query = 0
        for r in results:
            if opened_for_query >= max_open_per_query:
                break
            source_url = r.get("source_url", "")
            source_name = r.get("source_name", "") or source_url
            snippet = r.get("content", "")
            if not source_url:
                continue

            decision = {"should_open": True, "reason": "default_open", "related_goal_ids": q.get("target_goal_ids", [])}
            try:
                payload = {
                    "query": query,
                    "result": {"title": source_name, "url": source_url, "snippet": snippet},
                    "unresolved_goal_ids": unresolved_goal_ids,
                }
                log_llm_call_start("web_open_decision", {"query": query[:120], "url": source_url[:200]})
                resp = get_llm().invoke(
                    [SystemMessage(content=OPEN_DECISION_SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
                )
                log_llm_call_end("web_open_decision", ok=True, response_chars=len(getattr(resp, "content", "") or ""))
                parsed = extract_json(resp.content)
                if isinstance(parsed, dict):
                    decision = parsed
            except Exception as exc:  # noqa: BLE001
                log_llm_call_end("web_open_decision", ok=False, error=str(exc)[:200])

            if not bool(decision.get("should_open", False)):
                continue

            fetched = fetch_webpage_text(source_url)
            if not fetched.get("success"):
                reason = fetched.get("error_reason", "FETCH_FAILED")
                if isinstance(reason, str) and reason:
                    failure_reasons.append(reason)
                log_step("web_fetch_failed", {"url": source_url, "reason": reason}, level="WARN")
                continue

            page_text = fetched.get("text", "")
            if not isinstance(page_text, str) or not page_text.strip():
                failure_reasons.append("EMPTY_PAGE_TEXT")
                continue

            summary = {
                "finding": page_text[:500],
                "related_goal_ids": q.get("target_goal_ids", []),
                "confidence": "medium",
                "limitations": "",
            }
            try:
                payload = {
                    "query": query,
                    "source": {"name": source_name, "url": source_url},
                    "related_goal_ids": decision.get("related_goal_ids", q.get("target_goal_ids", [])),
                    "page_text": page_text,
                }
                log_llm_call_start("web_page_summary", {"query": query[:120], "url": source_url[:200]})
                resp = get_llm().invoke(
                    [SystemMessage(content=PAGE_SUMMARY_SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
                )
                log_llm_call_end("web_page_summary", ok=True, response_chars=len(getattr(resp, "content", "") or ""))
                parsed = extract_json(resp.content)
                if isinstance(parsed, dict):
                    summary = parsed
            except Exception as exc:  # noqa: BLE001
                log_llm_call_end("web_page_summary", ok=False, error=str(exc)[:200])

            fid = f"WEB_F{1000 + len(findings)}"
            related = summary.get("related_goal_ids", q.get("target_goal_ids", []))
            if not isinstance(related, list):
                related = q.get("target_goal_ids", [])
            findings.append(
                {
                    "finding_id": fid,
                    "source_type": "web_search",
                    "source_name": source_name,
                    "source_url": source_url,
                    "source_path": "",
                    "related_goal_ids": [x for x in related if isinstance(x, str)],
                    "finding": str(summary.get("finding", ""))[:800],
                    "confidence": summary.get("confidence", "medium"),
                    "limitations": str(summary.get("limitations", ""))[:240],
                }
            )
            opened_for_query += 1
            opened_urls += 1

    status = {
        "attempted": True,
        "success": len(findings) > 0,
        "failure_reasons": sorted(list({x for x in failure_reasons if isinstance(x, str) and x}))[:10],
        "queries_attempted": len(web_queries),
        "urls_opened": opened_urls,
    }
    return {"web_findings": findings, "web_search_status": status}


__all__ = ["run_web_research_agent"]
