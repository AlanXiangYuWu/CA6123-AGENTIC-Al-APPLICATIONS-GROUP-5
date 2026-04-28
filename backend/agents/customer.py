"""Customer Agent: turn vague user idea into a structured Project Brief."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.utils.json_parse import extract_json

_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "prompts" / "customer_brief_template.json"


def _load_brief_template() -> dict:
    return json.loads(_TEMPLATE_PATH.read_text(encoding="utf-8"))


BRIEF_TEMPLATE = _load_brief_template()
BRIEF_TEMPLATE_STR = json.dumps(BRIEF_TEMPLATE, ensure_ascii=False, indent=2)

SYSTEM = """You are the Customer Agent. Your job is to collect enough product
requirements before handing off to downstream agents.

Decision rule:
1) If key information is sufficient, output a final project brief.
2) If key information is missing/ambiguous, ask concise follow-up questions
   first (max 3), and do NOT fabricate all missing fields.

Final brief schema (must match exactly the same top-level keys and nested keys):
""" + BRIEF_TEMPLATE_STR + """

Clarification payload schema (separate from output-format rules):
{
  "questions": [string, ...],      // max 3
  "known_info": object,            // best-effort known fields from user input
  "missing_fields": [string, ...]
}

Output format (strict):
- If clarification is needed: output ONLY <CLARIFY>...</CLARIFY>
- If information is sufficient: output ONLY <BRIEF>...</BRIEF>
- The content inside <BRIEF> must follow the template schema above exactly.

Never output prose outside these tags."""


FALLBACK_BRIEF_PROMPT = """Extract a Project Brief JSON from the user idea below.
Use reasonable defaults for missing fields. Output ONLY raw JSON (no fences,
no tags, no prose) and follow this exact JSON schema:
{schema}

USER IDEA:
{idea}"""


def _user_idea_text(state: ProjectState) -> str:
    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def customer_agent(state: ProjectState) -> dict:
    msgs = [SystemMessage(content=SYSTEM), *state["messages"]]
    resp = get_llm().invoke(msgs)
    update: dict[str, Any] = {
        "messages": [resp],
        "trace": append_trace(state, "customer"),
    }
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    brief: dict | None = None
    if "<CLARIFY>" in text and "</CLARIFY>" in text:
        clarify_str = text.split("<CLARIFY>", 1)[1].split("</CLARIFY>", 1)[0]
        clarify = extract_json(clarify_str)
        update["project_brief"] = {
            "status": "needs_clarification",
            "questions": clarify.get("questions", []),
            "missing_fields": clarify.get("missing_fields", []),
            "known_info": clarify.get("known_info", {}),
        }
        return update
    if "<BRIEF>" in text and "</BRIEF>" in text:
        brief_str = text.split("<BRIEF>", 1)[1].split("</BRIEF>", 1)[0]
        brief = extract_json(brief_str)
    elif "{" in text and "}" in text:
        # Tag missing but JSON present
        brief = extract_json(text)

    # Hard fallback: force a brief on second pass to break recursion loops.
    if not brief or "_raw" in brief:
        idea = _user_idea_text(state)
        forced = get_llm().invoke(
            FALLBACK_BRIEF_PROMPT.format(
                idea=idea,
                schema=BRIEF_TEMPLATE_STR,
            )
        )
        forced_text = forced.content if isinstance(forced.content, str) else str(forced.content)
        brief = extract_json(forced_text)
        if "_raw" in brief:
            brief = {
                "product_name": "Unnamed",
                "one_sentence_summary": "",
                "target_users": [],
                "user_scenario": "",
                "core_problem": idea[:200],
                "proposed_solution": "",
                "must_have_features": [],
                "nice_to_have_features": [],
                "platform": "web",
                "business_model": "",
                "constraints": {
                    "budget": "",
                    "timeline": "",
                    "region": "",
                    "compliance": [],
                },
                "success_criteria": [],
                "assumptions": ["fallback-generated"],
                "open_questions": [],
                "_raw": forced_text[:500],
            }

    update["project_brief"] = brief
    return update
