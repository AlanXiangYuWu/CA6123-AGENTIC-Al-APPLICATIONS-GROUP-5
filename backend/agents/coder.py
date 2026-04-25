"""Coder Agent: generate code skeleton from tech design."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.core.state import ProjectState, append_trace
from backend.guardrails.code_safety import code_safety_scan
from backend.llm.gemini import get_llm
from backend.utils.json_parse import extract_json

SYSTEM = """You are the Coder Agent. Generate a runnable code skeleton based on
the technical design. NEVER hardcode API keys; always read from os.environ.
Output ONLY a JSON object with keys:
  files (list of {path, content}),
  entry_point (string),
  run_instructions (list of strings)."""


def coder_agent(state: ProjectState) -> dict:
    resp = get_llm().invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"TECH DESIGN:\n{json.dumps(state['tech_design'])}"),
        ]
    )
    artifact = extract_json(resp.content)
    flags: list[dict] = []
    for f in artifact.get("files", []):
        for issue in code_safety_scan(f.get("content", "")):
            flags.append(
                {"type": "code_safety", "file": f.get("path"), "issue": issue}
            )
    return {
        "code_artifact": artifact,
        "guardrail_flags": state.get("guardrail_flags", []) + flags,
        "messages": [
            AIMessage(content=f"[Coder] {len(artifact.get('files', []))} files")
        ],
        "trace": append_trace(state, "coder"),
    }
