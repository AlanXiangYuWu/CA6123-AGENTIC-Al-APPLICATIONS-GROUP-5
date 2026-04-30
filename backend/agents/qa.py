"""QA Agent: tool-using reviewer with deterministic scoring.

This agent does NOT do "hallucination detection" in the strict sense — it
performs internal consistency checks (verifying claims against upstream
artifacts: brief, research, code preview). True external-knowledge fact
checking would require RAG or web access.
"""
from __future__ import annotations
import json

from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, ToolMessage,
)

from backend.core.state import ProjectState, append_trace
from backend.llm.gemini import get_llm_strict
from backend.utils.json_parse import extract_json
from backend.tools.qa_tools import QA_TOOLS

def _reconstruct_tool_evidence(messages: list) -> dict:
    """Walk the message history and pull the REAL tool outputs.

    Why: LLM sometimes fabricates content in its final tool_evidence. By
    reading from the actual ToolMessage objects, we guarantee tool_evidence
    matches what the tools really returned.

    Maps tool names to their canonical evidence keys:
        coverage_check          -> coverage_check
        design_prd_alignment    -> design_prd_alignment
        code_static_check       -> code_static_check
        grounding_check (1st)   -> grounding_check_prd
        grounding_check (2nd+)  -> grounding_check_tech_design
        generate_test_cases     -> generate_test_cases
        pytest_sandbox          -> pytest_sandbox
    """
    evidence = {}
    grounding_calls = 0  # first call = PRD, second = tech_design

    # Walk pairs of (AIMessage with tool_calls) -> (ToolMessage with result)
    pending_tool_calls = {}  # tool_call_id -> tool_name
    for msg in messages:
        # Collect tool_call ids and their names from AIMessages
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for call in msg.tool_calls:
                pending_tool_calls[call["id"]] = call["name"]
        # When we hit a ToolMessage, look up which tool it answered
        if isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None)
            tool_name = pending_tool_calls.get(tool_call_id)
            if not tool_name:
                continue
            try:
                content = msg.content
                if isinstance(content, str):
                    result = json.loads(content)
                elif isinstance(content, dict):
                    result = content
                else:
                    result = {"_raw": str(content)}
            except Exception:
                result = {"_unparseable": str(msg.content)[:500]}

            # Map to canonical evidence key
            if tool_name == "grounding_check":
                # Trust the tool's own _target marker rather than call order.
                # Falls back to call-order if marker is missing (older tool versions).
                target = (result.get("_target") if isinstance(result, dict) else None)
                if target == "tech_design":
                    key = "grounding_check_tech_design"
                elif target == "prd":
                    key = "grounding_check_prd"
                else:
                    key = "grounding_check_prd" if grounding_calls == 0 else "grounding_check_tech_design"
                grounding_calls += 1
            else:
                key = tool_name

            # Don't overwrite if already set (in case of retries)
            if key not in evidence:
                evidence[key] = result

    return evidence

def _content_to_text(content) -> str:
    """Normalize LangChain message content (str OR list of blocks) to plain str."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(json.dumps(item, default=str))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content) if content is not None else ""


def _compute_score(tool_evidence: dict) -> tuple[float, bool, dict]:
    """Deterministic scoring from tool outputs.

    Weights:
      coverage_ratio          : 20%
      alignment_ratio         : 15%
      code_quality            : 20%
      grounded_ratio_factual  : 10%
      commitment_supported    : 10%
      test_pass_rate          : 25%

    Hard fail: any syntax error -> passed=False regardless of score.
    Soft fail: score < 0.7      -> passed=False.

    Note on code_quality:
      - If artifact has files but none are checkable (e.g. all .js while
        static_check is Python-only), give 0.5 ("unverifiable") rather than
        a free 1.0. This prevents non-Python projects from gaming the score.
    """
    breakdown = {}

    cov = tool_evidence.get("coverage_check", {}) or {}
    coverage_ratio = float(cov.get("coverage_ratio", 0.0))
    breakdown["coverage"] = round(coverage_ratio, 3)

    align = tool_evidence.get("design_prd_alignment", {}) or {}
    alignment_ratio = float(align.get("alignment_ratio", 0.0))
    breakdown["alignment"] = round(alignment_ratio, 3)

    static = tool_evidence.get("code_static_check", {}) or {}
    syntax_errors = len(static.get("syntax_errors", []) or [])
    files_checked = static.get("files_checked", 0) or 0
    total_files = static.get("total_files_in_artifact", files_checked) or 0

    if total_files == 0:
        # No files at all in artifact -> can't claim quality
        code_quality = 0.0
        breakdown["code_quality_note"] = "no files in artifact"
    elif files_checked == 0:
        # Files exist but none could be statically checked (e.g. all are .js).
        # Don't give free points — half credit reflects "unverified".
        code_quality = 0.5
        breakdown["code_quality_note"] = (
            f"{total_files} file(s) present but none Python-checkable; "
            "static analysis not applicable"
        )
    else:
        code_quality = max(0.0, 1.0 - (syntax_errors / files_checked))
        breakdown["code_quality_note"] = (
            f"{files_checked}/{total_files} file(s) statically checked"
        )

    breakdown["code_quality"] = round(code_quality, 3)
    breakdown["syntax_errors_count"] = syntax_errors

    g_prd = tool_evidence.get("grounding_check_prd", {}) or {}
    factual_ratio = float(g_prd.get("grounded_ratio_factual", 1.0))
    breakdown["grounded_factual"] = round(factual_ratio, 3)

    cs = len(g_prd.get("commitment_supported", []) or [])
    cu = len(g_prd.get("commitment_unsupported", []) or [])
    commitment_ratio = cs / (cs + cu) if (cs + cu) > 0 else 1.0
    breakdown["commitment_supported"] = round(commitment_ratio, 3)

    pytest_out = tool_evidence.get("pytest_sandbox", {}) or {}
    test_pass_rate = float(pytest_out.get("pass_rate", 0.0))
    tests_run = int(pytest_out.get("tests_run", 0) or 0)
    breakdown["test_pass_rate"] = round(test_pass_rate, 3)
    breakdown["tests_run"] = tests_run
    if tests_run == 0:
        breakdown["test_pass_rate_note"] = (
            "no tests generated (likely non-Python or untestable artifact)"
        )

    score = (
        0.20 * coverage_ratio
        + 0.15 * alignment_ratio
        + 0.20 * code_quality
        + 0.10 * factual_ratio
        + 0.10 * commitment_ratio
        + 0.25 * test_pass_rate
    )
    score = round(score, 3)

    has_critical_syntax = syntax_errors > 0
    passed = (score >= 0.7) and (not has_critical_syntax)

    breakdown["final_score"] = score
    breakdown["passed"] = passed
    breakdown["passed_reason"] = (
        "score>=0.7 and no syntax errors" if passed
        else f"score={score}, syntax_errors={syntax_errors}"
    )

    return score, passed, breakdown


SYSTEM = """You are the QA Agent. Verify artifacts using TOOLS rather than
your own knowledge. Note: you do internal consistency checks (verifying
claims against upstream artifacts), not external fact verification.

You will receive a JSON payload from the user containing FIVE keys:
- brief             : the project brief (string)
- prd_json          : the full PRD serialized as JSON string
- tech_design_json  : the full tech design serialized as JSON string
- code_artifact_json: the full code artifact serialized as JSON string
- sources_json      : sources for grounding (JSON string)

You MUST call ALL these tools. For each tool argument, COPY THE ENTIRE
VALUE from the payload — never use empty strings or short placeholders.

Required calls:
1) coverage_check(
       brief_full_text = <copy entire brief>,
       prd_full_json_string = <copy entire prd_json>
   )
2) design_prd_alignment(
       prd_full_json_string = <copy entire prd_json>,
       tech_design_full_json_string = <copy entire tech_design_json>
   )
3) code_static_check(
       code_artifact_json = <copy entire code_artifact_json>
   )
4) grounding_check(
       claims_full_text = <copy entire prd_json>,
       sources_full_json_string = <copy entire sources_json>,
       target = "prd"
   )
5) grounding_check(
       claims_full_text = <copy entire tech_design_json>,
       sources_full_json_string = <copy entire sources_json>,
       target = "tech_design"
   )
6) generate_test_cases(
       code_artifact_full_json_string = <copy entire code_artifact_json>,
       prd_full_json_string = <copy entire prd_json>
   )
7) pytest_sandbox(
       test_code = <test_code returned from step 6>,
       code_artifact_json = <copy entire code_artifact_json>
   )

After all tool calls, output ONLY a JSON object with keys:
  issues (list)         — [{type, target, description, severity}]
  test_cases (list)     — [{name, input, expected, code}]
  tool_evidence (object)— Map of tool name to raw output. Keys MUST be:
    coverage_check, design_prd_alignment, code_static_check,
    grounding_check_prd (the call on PRD),
    grounding_check_tech_design (the call on tech design),
    generate_test_cases, pytest_sandbox.

Issue type guidance (use precise terms):
- "coverage_gap"            : brief requirement missing from PRD
- "design_misalignment"     : PRD feature has no matching tech_design component
- "syntax_error"            : found by ast.parse
- "lint_warning"            : found by pyflakes
- "security_warning"        : found by bandit
- "consistency_issue"       : claim not supported by upstream artifacts
                               (do NOT call this "hallucination" — we don't
                                check external knowledge)
- "unsupported_commitment"  : SLA/perf promise without code/test evidence
- "test_failure"            : pytest_sandbox reported failures
- "incomplete_implementation": feature in PRD but missing from code
- "untestable_artifact"     : code can't be tested (wrong language, etc.)

DO NOT output 'passed' or 'score' — code computes those.
"""

MAX_TOOL_ITERATIONS = 8


def qa_agent(state: ProjectState) -> dict:
    brief = state["project_brief"]
    prd = state["prd"]
    tech_design = state["tech_design"]
    code_artifact = state["code_artifact"] or {"files": []}

    sources = {
        "brief": brief,
        "research": state.get("research", {}),
        "code_files_preview": [
            {
                "path": f.get("path", ""),
                "preview": (f.get("content") or "")[:800],
            }
            for f in code_artifact.get("files", [])
        ],
    }
    payload = {
        "brief": brief,
        "prd_json": json.dumps(prd, ensure_ascii=False),
        "tech_design_json": json.dumps(tech_design, ensure_ascii=False),
        "code_artifact_json": json.dumps(code_artifact, ensure_ascii=False),
        "sources_json": json.dumps(sources, ensure_ascii=False),
    }

    llm = get_llm_strict().bind_tools(QA_TOOLS)
    tool_map = {t.name: t for t in QA_TOOLS}
    messages = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
    ]

    last_resp = None
    for _ in range(MAX_TOOL_ITERATIONS):
        resp = llm.invoke(messages)
        messages.append(resp)
        last_resp = resp
        tool_calls = getattr(resp, "tool_calls", None) or []
        if not tool_calls:
            break
        for call in tool_calls:
            name = call["name"]
            args = call.get("args", {}) or {}
            try:
                if name not in tool_map:
                    result = {"_error": f"unknown tool: {name}"}
                else:
                    result = tool_map[name].invoke(args)
            except Exception as e:
                result = {"_error": f"tool {name} crashed: {e}"}
            messages.append(ToolMessage(
                content=json.dumps(result, ensure_ascii=False, default=str),
                tool_call_id=call["id"],
            ))

    final_text = (
        _content_to_text(last_resp.content) if last_resp is not None else ""
    )
    parsed = extract_json(final_text) or {}

    issues = parsed.get("issues", []) or []
    test_cases = parsed.get("test_cases", []) or []

    # CRITICAL: Reconstruct tool_evidence from REAL tool execution results,
    # not from LLM's self-reported version. LLMs sometimes fabricate "passing"
    # tool outputs when their narrative requires them. We trust only what the
    # tools actually returned.
    tool_evidence = _reconstruct_tool_evidence(messages)

    # Deterministic scoring — overrides any LLM-suggested score
    score, passed, breakdown = _compute_score(tool_evidence)

    qa_report = {
        "passed": passed,
        "score": score,
        "score_breakdown": breakdown,
        "issues": issues,
        "test_cases": test_cases,
        "tool_evidence": tool_evidence,
    }

    return {
        "qa_report": qa_report,
        "messages": [AIMessage(content=f"[QA] done. score={score}, passed={passed}")],
        "trace": append_trace(state, "qa"),
    }