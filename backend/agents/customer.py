"""Customer Agent wrapper: delegates loop to standalone module."""

from __future__ import annotations

from typing import Any
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm
from backend.tools.brief_gap_checker import check_brief_gaps
from backend.utils.json_parse import extract_json

"""Standalone customer loop module (Reasoning -> Action -> Observation)."""
MAX_CUSTOMER_ROUNDS = 3
MAX_QUESTIONS = 5



def customer_agent(state: ProjectState) -> dict:
    update: dict[str, Any] = {
        "trace": append_trace(state, "customer"),
    }
    update["project_brief"] = run_customer_loop(state)
    return update

_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "prompts" / "customer_brief_template.json"
_DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "prompts" / "customer_brief_defaults.json"


REASONING_SYSTEM = """You are the Reasoning stage of Customer Agent.

Task:
1) Read all user messages plus previous brief.
2) Update and refine the brief with only supported information.
3) Keep unknown fields as empty values; do not hallucinate facts.
4) If user says to "use default configuration", apply default assumptions ONLY to fields that were already asked in prior clarification questions (question scope). Do NOT treat it as approval to default every missing field.
5) For missing fields outside the asked scope, keep them empty so they can still be asked in later rounds.

Output format:
- Output ONLY <BRIEF>...</BRIEF>
- Content inside <BRIEF> must be valid JSON and match this template shape:
{schema}
"""

OBSERVATION_SYSTEM = """You are the Observation stage of Customer Agent.
You will receive missing brief fields.
Generate concise natural-language questions for the user.

Rules:
- Ask at most {max_questions} questions.
- Each question can cover one or multiple related fields.
- Keep wording user-friendly and concrete.

Output ONLY JSON:
{{
  "questions": [string, ...]
}}
"""


def _load_brief_template() -> dict:
    return json.loads(_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _load_brief_defaults() -> dict:
    return json.loads(_DEFAULTS_PATH.read_text(encoding="utf-8"))


BRIEF_TEMPLATE = _load_brief_template()
BRIEF_DEFAULTS = _load_brief_defaults()
BRIEF_TEMPLATE_STR = json.dumps(BRIEF_TEMPLATE, ensure_ascii=False, indent=2)
DEFAULT_CONFIG_MARKERS = (
    "use the default configuration",
    "use default configuration",
    "use default config",
    "default configuration",
    "默认配置",
)


def _extract_brief_from_state(state: ProjectState) -> tuple[dict, int]:
    current = state.get("project_brief")
    if not isinstance(current, dict):
        return {}, 0
    if current.get("status") == "needs_clarification":
        return current.get("brief", {}), int(current.get("round", 0))
    return current, int(current.get("_meta_round", 0))


def _reasoning_stage(state: ProjectState, prior_brief: dict) -> dict:
    prior_customer_state = state.get("project_brief")
    resp = get_llm().invoke(
        [
            SystemMessage(content=REASONING_SYSTEM.format(schema=BRIEF_TEMPLATE_STR)),
            HumanMessage(content=f"PREVIOUS_BRIEF:\n{json.dumps(prior_brief, ensure_ascii=False)}"),
            HumanMessage(content=f"PRIOR_CUSTOMER_STATE:\n{json.dumps(prior_customer_state, ensure_ascii=False)}"),
            *state["messages"],
        ]
    )
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    if "<BRIEF>" in text and "</BRIEF>" in text:
        text = text.split("<BRIEF>", 1)[1].split("</BRIEF>", 1)[0]
    brief = extract_json(text)
    return brief if isinstance(brief, dict) and "_raw" not in brief else prior_brief


def _apply_defaults(brief: dict, template: dict) -> dict:
    if isinstance(template, dict):
        out: dict[str, Any] = {}
        for key, sub_template in template.items():
            value = brief.get(key) if isinstance(brief, dict) else None
            out[key] = _apply_defaults(value, sub_template)
        return out
    if isinstance(template, list):
        if isinstance(brief, list):
            return brief
        return list(template)
    if brief is None:
        return template
    if isinstance(brief, str) and brief.strip() == "":
        return template
    return brief


def _observation_stage(brief: dict, missing_fields: list[str]) -> list[str]:
    obs_resp = get_llm().invoke(
        [
            SystemMessage(content=OBSERVATION_SYSTEM.format(max_questions=MAX_QUESTIONS)),
            HumanMessage(content=json.dumps({"brief": brief, "missing_fields": missing_fields}, ensure_ascii=False)),
        ]
    )
    payload = extract_json(obs_resp.content if isinstance(obs_resp.content, str) else str(obs_resp.content))
    questions = payload.get("questions", []) if isinstance(payload, dict) else []
    return [q for q in questions if isinstance(q, str)][:MAX_QUESTIONS]


def _latest_user_text(state: ProjectState) -> str:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            content = getattr(msg, "content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def _user_accepts_default_config(state: ProjectState) -> bool:
    text = _latest_user_text(state).strip().lower()
    return bool(text) and any(marker in text for marker in DEFAULT_CONFIG_MARKERS)


def _get_by_path(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set_by_path(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur: Any = data
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _apply_defaults_for_prompted_fields(brief: dict, field_paths: list[str]) -> dict:
    updated = json.loads(json.dumps(brief or {}, ensure_ascii=False))
    for path in field_paths:
        current = _get_by_path(updated, path)
        if not _is_empty_value(current):
            continue
        default = _get_by_path(BRIEF_DEFAULTS, path)
        if default is None:
            continue
        _set_by_path(updated, path, default)
    return updated


def run_customer_loop(state: ProjectState) -> dict:
    """Run customer loop inside one standalone module."""
    prior_brief, round_no = _extract_brief_from_state(state)
    working_brief = prior_brief

    if round_no >= MAX_CUSTOMER_ROUNDS:
        forced = _apply_defaults(working_brief, BRIEF_DEFAULTS)
        forced["_meta_round"] = round_no
        forced["assumptions"] = list(
            dict.fromkeys((forced.get("assumptions") or []) + ["default-filled-after-max-rounds"])
        )
        return forced

    round_no += 1
    working_brief = _reasoning_stage(state, working_brief)

    prior_customer_state = state.get("project_brief")
    if (
        _user_accepts_default_config(state)
        and isinstance(prior_customer_state, dict)
        and prior_customer_state.get("status") == "needs_clarification"
    ):
        prompted = prior_customer_state.get("prompted_missing_fields", [])
        if isinstance(prompted, list) and prompted:
            working_brief = _apply_defaults_for_prompted_fields(working_brief, prompted)
            working_brief["assumptions"] = list(
                dict.fromkeys((working_brief.get("assumptions") or []) + ["user-approved-default-for-prompted-fields"])
            )

    missing_fields = check_brief_gaps(working_brief, BRIEF_TEMPLATE)
    if not missing_fields:
        finalized = _apply_defaults(working_brief, BRIEF_DEFAULTS)
        finalized["_meta_round"] = round_no
        return finalized

    # Need new user info before continuing the next turn (via next API call).
    questions = _observation_stage(working_brief, missing_fields)
    return {
        "status": "needs_clarification",
        "round": round_no,
        "brief": working_brief,
        "missing_fields": missing_fields,
        "questions": questions,
        "prompted_missing_fields": missing_fields[:MAX_QUESTIONS],
    }
