"""Multi-fixture QA agent test.

Usage:
    .venv/bin/python scripts/test_qa.py              # run all 4 fixtures
    .venv/bin/python scripts/test_qa.py kids_app     # run one fixture
    .venv/bin/python scripts/test_qa.py perfect

Robustness check:
    - PERFECT fixture should yield HIGH score (>0.8) and passed=True.
    - BROKEN  fixture should yield VERY LOW score and passed=False.
    - Different domains (fitness vs kids_app) should both produce coherent output.
If these expectations hold, the QA agent generalizes and is not over-fit.
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from scripts.qa_fixtures import ALL_FIXTURES
from backend.agents.qa import qa_agent


def run_one(name: str, state: dict) -> dict:
    print()
    print("=" * 70)
    print(f"  Fixture: {name}")
    print("=" * 70)
    print(f"  product_name: {state['project_brief'].get('product_name')}")
    print(f"  features in PRD: {len(state['prd'].get('features', []))}")
    print(f"  code files: {[f['path'] for f in state['code_artifact'].get('files', [])]}")
    print()
    print("  Running QA agent...")

    try:
        result = qa_agent(state)
    except Exception as e:
        print(f"  ❌ CRASHED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"_crashed": str(e)}

    qa_report = result.get("qa_report") or {}
    score = qa_report.get("score")
    passed = qa_report.get("passed")
    issues = qa_report.get("issues", []) or []
    breakdown = qa_report.get("score_breakdown", {}) or {}

    print()
    print(f"  RESULT: passed={passed}, score={score}")
    print(f"  Breakdown: {json.dumps(breakdown, indent=2)}")
    print(f"  Issues found: {len(issues)}")
    for i, issue in enumerate(issues[:5], 1):
        sev = issue.get("severity", "?")
        typ = issue.get("type", "?")
        desc = issue.get("description", "")[:120]
        print(f"    [{i}] [{sev}] {typ}: {desc}")

    # Print full tool_evidence for debugging
    tool_evidence = qa_report.get("tool_evidence", {}) or {}
    print()
    print("  --- tool_evidence (which tools actually ran) ---")
    if not tool_evidence:
        print("  ⚠️  tool_evidence is EMPTY — LLM did not record any tool output")
    else:
        print(f"  Tool keys present: {list(tool_evidence.keys())}")
        for tool_name, output in tool_evidence.items():
            print(f"\n  [{tool_name}]")
            print(json.dumps(output, indent=4, ensure_ascii=False)[:1500])

    return {
        "name": name,
        "score": score,
        "passed": passed,
        "issues_count": len(issues),
        "breakdown": breakdown,
    }


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg and arg in ALL_FIXTURES:
        run_one(arg, ALL_FIXTURES[arg])
        return
    elif arg:
        print(f"Unknown fixture '{arg}'. Available: {list(ALL_FIXTURES.keys())}")
        sys.exit(1)

    summaries = []
    for name, state in ALL_FIXTURES.items():
        s = run_one(name, state)
        summaries.append(s)

    print()
    print("=" * 70)
    print("  CROSS-FIXTURE SUMMARY")
    print("=" * 70)
    print(f"{'Fixture':<12} {'Passed':<8} {'Score':<8} {'Issues':<8}")
    print("-" * 40)
    for s in summaries:
        if "_crashed" in s:
            print(f"{s.get('name','?'):<12} CRASHED")
            continue
        print(f"{s['name']:<12} {str(s['passed']):<8} "
              f"{s['score']!s:<8} {s['issues_count']:<8}")

    print()
    print("Robustness expectations:")
    print("  - perfect  -> high score (>0.8), passed=True")
    print("  - broken   -> very low score, passed=False, many issues")
    print("  - kids_app -> low/mid score, passed=False (has known bugs)")
    print("  - fitness  -> coherent output (proves cross-domain works)")


if __name__ == "__main__":
    main()