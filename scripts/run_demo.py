"""Quick CLI demo: run the full pipeline once and dump the final package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `python scripts/run_demo.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core.graph import get_app  # noqa: E402
from backend.core.state import initial_state  # noqa: E402
from backend.guardrails.injection import detect_prompt_injection  # noqa: E402


def main() -> None:
    idea = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "I want to build an AI coding companion app for kids aged 6-12 "
            "that teaches Python through gamified missions. Please produce "
            "a full plan."
        )
    )
    inj = detect_prompt_injection(idea)
    if inj.get("is_injection") and inj.get("confidence", 0) > 0.7:
        print("Blocked by injection guardrail:", inj)
        return

    app = get_app()
    config = {"configurable": {"thread_id": "cli-demo"}, "recursion_limit": 50}
    final = app.invoke(initial_state(idea), config=config)

    print("\n=== TRACE ===")
    print(" -> ".join(final.get("trace", [])))
    print("\n=== GUARDRAIL FLAGS ===")
    for f in final.get("guardrail_flags", []):
        print(f)
    print("\n=== FINAL PACKAGE keys ===")
    for k in (final.get("final_package") or {}):
        print(f"- {k}")

    out = Path("final_package.json")
    out.write_text(
        json.dumps(
            {
                "trace": final.get("trace"),
                "revision_round": final.get("revision_round"),
                "guardrail_flags": final.get("guardrail_flags"),
                "citations": final.get("citations"),
                "final_package": final.get("final_package"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()
