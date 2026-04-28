"""Robust JSON extraction from LLM text outputs (handles ```json fences)."""

from __future__ import annotations

import json


def extract_json(text: str) -> dict:
    txt = text.strip()
    if txt.startswith("```"):
        # strip leading fence
        txt = txt.split("```", 2)[1] if txt.count("```") >= 2 else txt[3:]
        if txt.startswith("json"):
            txt = txt[4:]
        txt = txt.strip().rstrip("`").strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        # try to grab outermost {...}
        start = txt.find("{")
        end = txt.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(txt[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"_raw": text}
