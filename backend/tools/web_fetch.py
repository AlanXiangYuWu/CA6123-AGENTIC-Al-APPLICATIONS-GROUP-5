from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from typing import Any

from backend.utils.debug_logger import log_step


def _strip_html_tags(text: str) -> str:
    t = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def fetch_webpage_text(url: str, timeout_sec: int = 15) -> dict[str, Any]:
    """Fetch readable webpage text with fallback through jina.ai."""
    if not isinstance(url, str) or not url.strip():
        return {"success": False, "url": url, "error_reason": "EMPTY_URL", "text": ""}

    clean_url = url.strip()
    if clean_url.startswith("//"):
        clean_url = "https:" + clean_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    urls_to_try = [clean_url, "https://r.jina.ai/" + clean_url]
    last_error = "UNKNOWN"
    for target in urls_to_try:
        try:
            req = urllib.request.Request(target, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            lowered = raw.lower()
            if any(x in lowered for x in ["captcha", "verify you are human", "unusual traffic", "cloudflare"]):
                last_error = "CAPTCHA_OR_BOT_BLOCK"
                log_step("web_fetch_blocked", {"url": clean_url, "target": target}, level="WARN")
                continue
            text = _strip_html_tags(raw)
            if len(text) < 180:
                last_error = "TEXT_TOO_SHORT"
                continue
            return {"success": True, "url": clean_url, "error_reason": "", "text": text[:12000]}
        except Exception as exc:  # noqa: BLE001
            last_error = f"HTTP_ERROR:{str(exc)[:120]}"
    return {"success": False, "url": clean_url, "error_reason": last_error, "text": ""}


__all__ = ["fetch_webpage_text"]
