"""Static checks on generated code (draft 5.5)."""

from __future__ import annotations

SECRET_PATTERNS = ("AIza", "sk-", "AKIA", "ghp_", "xoxb-", "xoxp-")


def code_safety_scan(code: str) -> list[str]:
    flags: list[str] = []
    for pat in SECRET_PATTERNS:
        if pat in code:
            flags.append(f"Possible leaked secret prefix: {pat}")
    if "API_KEY" in code.upper() and "os.environ" not in code and "getenv" not in code:
        flags.append("API key referenced without env-var lookup")
    if "eval(" in code or "exec(" in code:
        flags.append("Dangerous eval/exec call")
    return flags
