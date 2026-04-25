"""Customer Agent: turn vague user idea into a structured Project Brief."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.utils.json_parse import extract_json

SYSTEM = """You are the Customer Agent. Your sole task: turn the user's idea
into a structured Project Brief immediately.

Output ONLY a JSON object, wrapped in <BRIEF>...</BRIEF> tags. No prose, no
clarifying questions, no preamble. If the user idea is vague, fill missing
fields with reasonable assumptions and mark them in `assumptions` field.

Required JSON schema:
{
  "product_name": string,
  "target_users": string,
  "core_problem": string,
  "must_have_features": [string, ...],
  "platform": string,
  "success_criteria": [string, ...],
  "assumptions": [string, ...]
}"""


FALLBACK_BRIEF_PROMPT = """Extract a Project Brief JSON from the user idea below.
Use reasonable defaults for missing fields. Output ONLY raw JSON (no fences,
no tags, no prose) with keys: product_name, target_users, core_problem,
must_have_features (list), platform, success_criteria (list), assumptions (list).

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
    if "<BRIEF>" in text and "</BRIEF>" in text:
        brief_str = text.split("<BRIEF>", 1)[1].split("</BRIEF>", 1)[0]
        brief = extract_json(brief_str)
    elif "{" in text and "}" in text:
        # Tag missing but JSON present
        brief = extract_json(text)

    # Hard fallback: force a brief on second pass to break recursion loops.
    if not brief or "_raw" in brief:
        idea = _user_idea_text(state)
        forced = get_llm().invoke(FALLBACK_BRIEF_PROMPT.format(idea=idea))
        forced_text = forced.content if isinstance(forced.content, str) else str(forced.content)
        brief = extract_json(forced_text)
        if "_raw" in brief:
            brief = {
                "product_name": "Unnamed",
                "target_users": "general",
                "core_problem": idea[:200],
                "must_have_features": [],
                "platform": "web",
                "success_criteria": [],
                "assumptions": ["fallback-generated"],
                "_raw": forced_text[:500],
            }

    update["project_brief"] = brief
    return update
