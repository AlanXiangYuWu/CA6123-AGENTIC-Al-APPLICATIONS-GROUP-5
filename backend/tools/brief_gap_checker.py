"""Action-stage tool: compare brief vs template and list missing fields."""

from __future__ import annotations

from typing import Any


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _walk(template: Any, brief: Any, prefix: str, out: list[str]) -> None:
    if isinstance(template, dict):
        brief_dict = brief if isinstance(brief, dict) else {}
        for key, sub_template in template.items():
            path = f"{prefix}.{key}" if prefix else key
            _walk(sub_template, brief_dict.get(key), path, out)
        return
    if isinstance(template, list):
        if _is_empty(brief):
            out.append(prefix)
        return
    if _is_empty(brief):
        out.append(prefix)


def check_brief_gaps(brief: dict, template: dict) -> list[str]:
    """Return a list of dotted paths that are still missing in `brief`."""
    missing: list[str] = []
    _walk(template, brief, "", missing)
    return missing
