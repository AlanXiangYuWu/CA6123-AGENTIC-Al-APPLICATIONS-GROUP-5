"""QA Agent tools: real verification, not LLM self-judgment."""
from __future__ import annotations
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

from backend.llm.gemini import get_llm_strict


def _llm_json(system: str, user: str) -> dict:
    """Call LLM, parse JSON from response. Returns {} on failure."""
    try:
        resp = get_llm_strict().invoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
        text = resp.content if hasattr(resp, "content") else str(resp)
        if isinstance(text, list):
            text = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in text
            )
        m = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(m.group(0)) if m else {}
    except Exception as e:
        return {"_error": str(e)}


@tool
def coverage_check(brief_full_text: str, prd_full_json_string: str) -> dict:
    """Check whether the PRD covers each requirement implied by the brief.

    IMPORTANT: brief_full_text must be the ENTIRE project brief content.
    prd_full_json_string must be the ENTIRE PRD serialized as JSON.

    Returns: {coverage_ratio, matched, missing, total_requirements}.
    """
    system = (
        "You extract atomic requirements from a project brief and check coverage "
        "against a PRD. Output ONLY JSON with keys: requirements (list of short "
        "strings), matched (list of requirements found in PRD), missing (list)."
    )
    user = f"BRIEF:\n{brief_full_text}\n\nPRD:\n{prd_full_json_string}"
    result = _llm_json(system, user)
    reqs = result.get("requirements", []) or []
    matched = result.get("matched", []) or []
    missing = result.get("missing", []) or []
    ratio = len(matched) / len(reqs) if reqs else 0.0
    return {
        "coverage_ratio": round(ratio, 2),
        "matched": matched,
        "missing": missing,
        "total_requirements": len(reqs),
    }


@tool
def design_prd_alignment(prd_full_json_string: str,
                          tech_design_full_json_string: str) -> dict:
    """Check whether each PRD feature has a matching component in tech design.

    IMPORTANT: Both arguments must be FULL JSON strings.

    Returns: {alignment_ratio, aligned, unaligned_features, total_features}.
    """
    system = (
        "You verify alignment between a PRD and a technical design. "
        "A 'matching component' must be an actual service/module/component in "
        "tech_design.components or .system_components. Pure data models do NOT "
        "count as components for feature alignment.\n"
        "Output ONLY JSON with keys: features (list of PRD features), "
        "aligned (list with matching component), unaligned_features (list)."
    )
    user = (f"PRD:\n{prd_full_json_string}\n\n"
            f"TECH_DESIGN:\n{tech_design_full_json_string}")
    result = _llm_json(system, user)
    features = result.get("features", []) or []
    aligned = result.get("aligned", []) or []
    unaligned = result.get("unaligned_features", []) or []
    ratio = len(aligned) / len(features) if features else 0.0
    return {
        "alignment_ratio": round(ratio, 2),
        "aligned": aligned,
        "unaligned_features": unaligned,
        "total_features": len(features),
    }


@tool
def code_static_check(code_artifact_json: str) -> dict:
    """Run real static analysis: ast syntax + pyflakes lint + bandit security.

    Currently checks Python files only. Other languages are reported as
    unchecked but counted in total_files_in_artifact so the scorer can
    distinguish "Python project, all clean" from "non-Python project, untested".

    Returns: {files_checked, total_files_in_artifact, syntax_errors,
              lint_warnings, security_warnings, skipped_files}.
    """
    try:
        artifact = json.loads(code_artifact_json)
    except Exception as e:
        return {"_error": f"bad json: {e}"}

    files = artifact.get("files", []) or []
    syntax_errors = []
    lint_warnings = []
    security_warnings = []
    skipped_files = []
    checked = 0

    for f in files:
        path = f.get("path", "<unknown>")
        content = f.get("content", "")
        if not path.endswith(".py") or not content:
            skipped_files.append({
                "path": path,
                "reason": "non-Python or empty content",
            })
            continue
        checked += 1
        try:
            ast.parse(content)
        except SyntaxError as e:
            syntax_errors.append({"file": path, "line": e.lineno, "msg": e.msg})
            continue

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", suffix=".py", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            r = subprocess.run(
                [sys.executable, "-m", "pyflakes", tmp_path],
                capture_output=True, text=True, timeout=10,
            )
            if r.stdout.strip():
                for line in r.stdout.strip().splitlines():
                    lint_warnings.append({"file": path, "msg": line})
        except FileNotFoundError:
            pass
        except Exception as e:
            lint_warnings.append({"file": path, "msg": f"pyflakes failed: {e}"})

        if tmp_path:
            try:
                r = subprocess.run(
                    ["bandit", "-q", "-f", "json", tmp_path],
                    capture_output=True, text=True, timeout=15,
                )
                if r.stdout.strip():
                    report = json.loads(r.stdout)
                    for issue in report.get("results", []):
                        security_warnings.append({
                            "file": path,
                            "severity": issue.get("issue_severity"),
                            "msg": issue.get("issue_text"),
                        })
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            except Exception as e:
                security_warnings.append({"file": path, "msg": f"bandit failed: {e}"})

    return {
        "files_checked": checked,
        "total_files_in_artifact": len(files),
        "syntax_errors": syntax_errors,
        "lint_warnings": lint_warnings[:20],
        "security_warnings": security_warnings,
        "skipped_files": skipped_files,
    }


@tool
def grounding_check(claims_full_text: str, sources_full_json_string: str,
                    target: str = "prd") -> dict:
    """Internal consistency check: extract claims from text, classify them, and
    verify against upstream artifacts (brief, research, code preview).

    NOTE: This is NOT external fact-checking. We can't detect a claim like
    'COPPA requires X' being factually wrong — only whether it appears in our
    sources.

    Three claim types:
    - factual: external facts (compliance, market data). Grounded only if
      cited in sources.
    - design: internal design decisions (tech stack, architecture). Grounded
      if internally consistent.
    - commitment: performance/UX promises (SLAs). Grounded only if there's
      evidence in code or test plans.

    IMPORTANT: claims_full_text must be the ENTIRE text to fact-check.
    sources_full_json_string must be the ENTIRE sources JSON.
    target must be either "prd" or "tech_design" to label which artifact
    is being checked (used downstream to disambiguate the two calls).
    """

    system = (
        "You are a strict but fair internal-consistency checker. Extract claims "
        "from the TEXT and CLASSIFY each claim:\n"
        "- factual: external facts (market, compliance like COPPA, third-party). "
        "MUST appear in SOURCES to be grounded.\n"
        "- design: internal design (tech stack, architecture). Considered grounded "
        "if internally consistent.\n"
        "- commitment: performance/UX promises. Considered grounded ONLY if there's "
        "evidence in code or test plans.\n\n"
        "Output ONLY JSON with keys:\n"
        "  factual_grounded, factual_ungrounded, design_consistent, "
        "design_inconsistent, commitment_supported, commitment_unsupported."
    )
    user = f"TEXT:\n{claims_full_text}\n\nSOURCES:\n{sources_full_json_string}"
    result = _llm_json(system, user)

    fg = result.get("factual_grounded", []) or []
    fu = result.get("factual_ungrounded", []) or []
    dc = result.get("design_consistent", []) or []
    di = result.get("design_inconsistent", []) or []
    cs = result.get("commitment_supported", []) or []
    cu = result.get("commitment_unsupported", []) or []
    total_factual = len(fg) + len(fu)
    factual_ratio = len(fg) / total_factual if total_factual else 1.0

    return {
        "grounded_ratio_factual": round(factual_ratio, 2),
        "factual_grounded": fg,
        "factual_ungrounded": fu,
        "design_consistent": dc,
        "design_inconsistent": di,
        "commitment_supported": cs,
        "commitment_unsupported": cu,
        "total_claims": len(fg) + len(fu) + len(dc) + len(di) + len(cs) + len(cu),
        "_target": target,
    }


@tool
def generate_test_cases(code_artifact_full_json_string: str,
                          prd_full_json_string: str) -> dict:
    """Generate executable pytest code for the artifact.

    IMPORTANT: Both arguments must be FULL JSON strings.

    Returns: {test_code, target_files, num_tests, untestable_reason}.
    """
    system = (
        "You generate REAL EXECUTABLE pytest code testing the provided artifact "
        "against PRD acceptance criteria.\n\n"
        "STRICT RULES:\n"
        "1) ONLY test functions that exist in the artifact.\n"
        "2) Each test starts with `def test_<name>():`.\n"
        "3) Use plain assert. Imports must match artifact paths.\n"
        "4) Skip criteria that can't be tested. No infinite loops.\n"
        "5) NO MOCKING the code under test. Do NOT redefine functions you "
        "are testing. Do NOT use MagicMock to replace artifact code.\n"
        "6) If the artifact is in a non-Python language (.js/.ts/.java) or "
        "cannot be imported with plain `from X import Y`, output empty "
        "test_code with num_tests=0 and explain in 'untestable_reason'. "
        "DO NOT mock-rewrite the artifact code to make tests pass.\n"
        "7) External dependencies (DB, network, file I/O outside tempfile) "
        "may be mocked — but the artifact's own functions must be imported "
        "from the artifact, not redefined.\n\n"
        "Output ONLY JSON with keys: test_code (str), target_files (list), "
        "num_tests (int), untestable_reason (str, optional)."
    )
    user = (f"CODE_ARTIFACT:\n{code_artifact_full_json_string}\n\n"
            f"PRD:\n{prd_full_json_string}")
    result = _llm_json(system, user)
    return {
        "test_code": result.get("test_code", "") or "",
        "target_files": result.get("target_files", []) or [],
        "num_tests": int(result.get("num_tests", 0) or 0),
        "untestable_reason": result.get("untestable_reason", "") or "",
    }


@tool
def pytest_sandbox(test_code: str, code_artifact_json: str) -> dict:
    """Run pytest on test_code against the artifact in a temp sandbox.

    Refuses to run if test_code is empty OR if it doesn't actually import
    anything from the artifact (e.g. trivial 'assert True' placeholders).
    This prevents LLM from gaming pass_rate by feeding fake tests.

    Returns: {pass_rate, tests_run, tests_passed, tests_failed, failures, raw_output}.
    """
    if not test_code or not test_code.strip():
        return {
            "pass_rate": 0.0,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "raw_output": "no test_code provided",
            "_skipped": True,
        }

    try:
        artifact = json.loads(code_artifact_json)
    except Exception as e:
        return {"_error": f"bad json: {e}"}

    # Validate that test_code actually tests THIS artifact, not a trivial
    # placeholder. Required: at least one import that references an artifact
    # file path stem.
    artifact_files = artifact.get("files", []) or []
    artifact_module_names = set()
    for f in artifact_files:
        path = f.get("path", "")
        if not path:
            continue
        # 'backend/missions.py' -> 'missions', 'backend.missions'
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem and stem != "__init__":
            artifact_module_names.add(stem)
        # also 'backend.missions' style
        dotted = (
            os.path.splitext(path)[0]
            .replace(os.sep, ".")
            .replace("/", ".")
            .lstrip(".")
        )
        if dotted:
            artifact_module_names.add(dotted)

    has_artifact_import = False
    for name in artifact_module_names:
        if not name:
            continue
        # Look for `from <name>` or `import <name>` referencing the artifact
        if (re.search(rf"\bfrom\s+{re.escape(name)}\b", test_code)
                or re.search(rf"\bimport\s+{re.escape(name)}\b", test_code)):
            has_artifact_import = True
            break

    if not has_artifact_import:
        return {
            "pass_rate": 0.0,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "raw_output": (
                "test_code rejected: does not import any artifact module. "
                f"Expected import referencing one of: "
                f"{sorted(artifact_module_names)}. "
                "This prevents placeholder tests from gaming pass_rate."
            ),
            "_skipped": True,
            "_rejection_reason": "no_artifact_import",
        }

    tmpdir = tempfile.mkdtemp(prefix="qa_pytest_")
    try:
        for f in artifact.get("files", []) or []:
            rel_path = f.get("path", "").lstrip("/")
            content = f.get("content", "")
            if not rel_path or not content:
                continue
            full_path = os.path.join(tmpdir, rel_path)
            os.makedirs(os.path.dirname(full_path) or tmpdir, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as out:
                out.write(content)
            parent = os.path.dirname(full_path)
            while parent and parent.startswith(tmpdir) and parent != tmpdir:
                init_p = os.path.join(parent, "__init__.py")
                if not os.path.exists(init_p):
                    open(init_p, "w").close()
                parent = os.path.dirname(parent)

        test_file = os.path.join(tmpdir, "test_qa_generated.py")
        with open(test_file, "w", encoding="utf-8") as out:
            out.write(test_code)

        try:
            env = os.environ.copy()
            existing_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (
                tmpdir + os.pathsep + existing_pp if existing_pp else tmpdir
            )
            r = subprocess.run(
                [sys.executable, "-m", "pytest", test_file,
                 "--tb=short", "-v", "--no-header",
                 "-p", "no:cacheprovider"],
                capture_output=True, text=True, timeout=30,
                cwd=tmpdir, env=env,
            )
            stdout = r.stdout or ""
            stderr = r.stderr or ""
        except subprocess.TimeoutExpired:
            return {
                "pass_rate": 0.0, "tests_run": 0, "tests_passed": 0,
                "tests_failed": 0,
                "failures": [{"test": "<timeout>", "msg": "30s"}],
                "raw_output": "TIMEOUT", "_timeout": True,
            }

        out = stdout + "\n" + stderr
        passed = len(re.findall(r"PASSED", out))
        failed = len(re.findall(r"FAILED", out))
        errors = len(re.findall(r"ERROR", out))
        total = passed + failed + errors

        failures = []
        for m in re.finditer(
            r"FAILED\s+([^\s]+)::([^\s]+).*?(?=PASSED|FAILED|ERROR|=====|$)",
            out, re.DOTALL,
        ):
            failures.append({"test": m.group(2), "msg": m.group(0)[:300].strip()})
        for m in re.finditer(
            r"ERROR\s+([^\s]+)::([^\s]+).*?(?=PASSED|FAILED|ERROR|=====|$)",
            out, re.DOTALL,
        ):
            failures.append({
                "test": m.group(2),
                "msg": "ERROR: " + m.group(0)[:300].strip(),
            })

        pass_rate = passed / total if total else 0.0
        return {
            "pass_rate": round(pass_rate, 2),
            "tests_run": total,
            "tests_passed": passed,
            "tests_failed": failed + errors,
            "failures": failures[:10],
            "raw_output": out[-2000:],
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


QA_TOOLS = [
    coverage_check,
    design_prd_alignment,
    code_static_check,
    grounding_check,
    generate_test_cases,
    pytest_sandbox,
]