from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any

from backend.utils.debug_logger import log_step


def web_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Lightweight best-effort web search (no API keys).

    Implementation uses DuckDuckGo HTML endpoint and extracts result titles/links/snippets.
    If network is blocked, returns an empty list.
    """

    if not query.strip():
        return []

    q = urllib.parse.quote_plus(query.strip())
    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    url_html = f"https://duckduckgo.com/html/?q={q}"
    url_lite = f"https://duckduckgo.com/lite/?q={q}"
    # Fallback proxy: can bypass some anti-bot behaviors by fetching through jina.ai.
    url_jina_lite = f"https://r.jina.ai/https://duckduckgo.com/lite/?q={q}"

    endpoints: list[tuple[str, str]] = [
        ("ddg_html", url_html),
        ("ddg_lite", url_lite),
        ("ddg_jina_lite", url_jina_lite),
    ]

    a_pat = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    s_pat = re.compile(
        r'class="result__snippet"[^>]*>(?P<snippet>.*?)</',
        re.IGNORECASE | re.DOTALL,
    )
    # More permissive extraction: don't rely on `result__a` class.
    a_fallback_pat = re.compile(
        r'<a[^>]*href="(?P<href>[^"]*(?:/l/\?uddg=|duckduckgo\.com/l/\?uddg=)[^"]*)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    def _normalize_href(h: str) -> str:
        h2 = html.unescape(h or "").strip()
        # ddg sometimes returns schemeless //duckduckgo.com/...
        if h2.startswith("/l/?uddg="):
            return "//duckduckgo.com" + h2
        return h2

    def _clean_text(t: str) -> str:
        # Remove tags/entities, collapse whitespace.
        t2 = re.sub(r"<[^>]+>", " ", t or "")
        t2 = html.unescape(t2)
        t2 = re.sub(r"\s+", " ", t2).strip()
        return t2

    def _parse_raw(raw: str) -> list[dict[str, Any]]:
        titles: list[str] = []
        hrefs: list[str] = []
        snippets: list[str] = []

        for m in a_pat.finditer(raw):
            hrefs.append(m.group("href"))
            titles.append(m.group("title"))
            if len(hrefs) >= limit * 2:
                break

        if not hrefs:
            for m in a_fallback_pat.finditer(raw):
                hrefs.append(m.group("href"))
                titles.append(m.group("title"))
                if len(hrefs) >= limit * 2:
                    break

        for m in s_pat.finditer(raw):
            snippet_html = m.group("snippet")
            snippet_txt = _clean_text(snippet_html)
            if snippet_txt:
                snippets.append(snippet_txt)
            if len(snippets) >= limit * 2:
                break

        n = min(limit, len(hrefs))
        out: list[dict[str, Any]] = []
        for i in range(n):
            title = _clean_text(titles[i]) if i < len(titles) else ""
            href = _normalize_href(hrefs[i]) if i < len(hrefs) else ""
            snippet = snippets[i] if i < len(snippets) else ""
            # Ensure `content` is non-empty so downstream summarizer doesn't drop it.
            content = snippet or title or href
            if not content:
                continue
            out.append(
                {
                    "source_name": title or href,
                    "source_url": href,
                    "content": content,
                    "published_date": "",
                }
            )
        return out

    for attempt in range(3):
        for endpoint_name, endpoint_url in endpoints:
            try:
                req = urllib.request.Request(endpoint_url, headers=base_headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:  # noqa: BLE001
                log_step(
                    "web_search_http_error",
                    {"query": query, "endpoint": endpoint_name, "error": str(e)},
                    level="ERROR",
                )
                continue

            raw_lower = raw.lower()
            signals = []
            for s in [
                "captcha",
                "unusual traffic",
                "detected unusual",
                "verify you are human",
                "sorry",
                "cloudflare",
                "robot",
            ]:
                if s in raw_lower:
                    signals.append(s)
            if signals:
                log_step(
                    "web_search_block_signals",
                    {"query": query, "endpoint": endpoint_name, "signals": signals, "raw_head": raw[:600]},
                    level="WARN",
                )

            parsed = _parse_raw(raw)
            if parsed:
                log_step(
                    "web_search_success",
                    {"query": query, "endpoint": endpoint_name, "attempt": attempt, "results_count": len(parsed)},
                )
                return parsed

            log_step(
                "web_search_parse_failed",
                {
                    "query": query,
                    "endpoint": endpoint_name,
                    "attempt": attempt,
                    "raw_len": len(raw),
                    "raw_head": raw[:400],
                },
                level="WARN",
            )
        time.sleep(1.0 + attempt * 0.5)

    return []


__all__ = ["web_search"]

