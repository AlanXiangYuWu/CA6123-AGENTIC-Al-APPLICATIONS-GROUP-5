from __future__ import annotations

import contextvars
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional

_buffer_var: contextvars.ContextVar[Optional[list[str]]] = contextvars.ContextVar(
    "debug_logger_buffer",
    default=None,
)

_run_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "debug_logger_run_id",
    default=None,
)

_log_prefix_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "debug_logger_log_prefix",
    default="research",
)


def _project_root() -> Path:
    # backend/utils/debug_logger.py -> backend/utils -> backend -> project root
    return Path(__file__).resolve().parents[2]


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def set_log_buffer(buf: list[str], *, log_prefix: str = "research") -> contextvars.Token:
    """Set a per-request in-memory buffer for debug lines."""
    run_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    buf_token = _buffer_var.set(buf)
    run_token = _run_id_var.set(run_id)
    prefix = (log_prefix or "research").strip().lower().replace(" ", "_")
    prefix_token = _log_prefix_var.set(prefix)
    # Return a combined token object so caller can reset both vars.
    return (buf_token, run_token, prefix_token)  # type: ignore[return-value]


def reset_log_buffer(token: Any) -> None:
    if isinstance(token, tuple) and len(token) == 3:
        buf_token, run_token, prefix_token = token
        _buffer_var.reset(buf_token)
        _run_id_var.reset(run_token)
        _log_prefix_var.reset(prefix_token)
        return
    if isinstance(token, tuple) and len(token) == 2:
        # Backward compatibility with older 2-token callers.
        buf_token, run_token = token
        _buffer_var.reset(buf_token)
        _run_id_var.reset(run_token)
        return
    _buffer_var.reset(token)


def _short_repr(obj: Any, max_chars: int = 600) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        s = str(obj)
    if len(s) > max_chars:
        return s[:max_chars] + f"...(truncated:{len(s) - max_chars} chars)"
    return s


def _write_jsonl(path: Path, record: dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _append_pretty_json(path: Path, record: dict[str, Any]) -> None:
    """Append one record into a pretty-printed JSON array file."""
    _ensure_parent_dir(path)
    data: list[dict[str, Any]]
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                data = existing
            else:
                data = [record]
        except Exception:  # noqa: BLE001
            data = [record]
    else:
        data = []
    data.append(record)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _write_artifact_markdown(path: Path, record: dict[str, Any]) -> None:
    """Write a human-friendly markdown view for artifact logs."""
    _ensure_parent_dir(path)
    ts = record.get("ts", "")
    artifact_name = record.get("artifact_name", "")
    payload = record.get("payload", {})

    lines: list[str] = []
    lines.append(f"# Artifact Log - {artifact_name}")
    lines.append("")
    lines.append(f"- Timestamp: `{ts}`")
    if isinstance(payload, dict):
        module = payload.get("module")
        thread_id = payload.get("thread_id")
        if module:
            lines.append(f"- Module: `{module}`")
        if thread_id:
            lines.append(f"- Thread: `{thread_id}`")
    lines.append("")
    lines.append("## Payload")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    lines.append("```")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def log_step(step: str, payload: Any, *, level: str = "INFO") -> None:
    """
    Log an intermediate step.
    - Always append to `.logs/<prefix>_steps_<timestamp>.jsonl`.
    - If a buffer is set via `set_log_buffer`, also append a human-readable line.
    """
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{level}] {step} - {_short_repr(payload)}"

    buf = _buffer_var.get()
    if isinstance(buf, list):
        buf.append(line)

    root = _project_root()
    run_id = _run_id_var.get()
    if not run_id:
        run_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_prefix = _log_prefix_var.get() or "research"
    path_jsonl = root / ".logs" / f"{log_prefix}_steps_{run_id}.jsonl"
    path_pretty = root / ".logs" / f"{log_prefix}_steps_{run_id}.pretty.json"
    record = {"ts": ts, "level": level, "step": step, "payload": payload}
    try:
        _write_jsonl(path_jsonl, record)
        _append_pretty_json(path_pretty, record)
    except Exception:  # noqa: BLE001
        # Don't break the agent if logging fails.
        pass


def log_artifact(artifact_name: str, payload: Any, *, file_prefix: str = "artifacts") -> None:
    """
    Log artifacts (final structured outputs) to one file.
    Writes to `.logs/<file_prefix>_<timestamp>.json` (pretty-printed).
    """
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    root = _project_root()
    run_id = _run_id_var.get()
    if not run_id:
        run_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prefix = (file_prefix or "artifacts").strip().lower().replace(" ", "_")
    path_json = root / ".logs" / f"{safe_prefix}_{run_id}.json"
    path_md = root / ".logs" / f"{safe_prefix}_{run_id}.md"
    record = {"ts": ts, "artifact_name": artifact_name, "payload": payload}
    try:
        _append_pretty_json(path_json, record)
        _write_artifact_markdown(path_md, record)
    except Exception:  # noqa: BLE001
        pass


def log_llm_call_start(stage: str, payload: Any | None = None) -> None:
    """Standard start-event for any LLM call across agents."""
    body = {"stage": stage}
    if payload is not None:
        body["payload"] = payload
    log_step("llm_call_start", body)


def log_llm_call_end(
    stage: str,
    *,
    ok: bool,
    response_chars: int | None = None,
    error: str | None = None,
    payload: Any | None = None,
) -> None:
    """Standard end-event for any LLM call across agents."""
    body: dict[str, Any] = {"stage": stage, "ok": ok}
    if response_chars is not None:
        body["response_chars"] = response_chars
    if error:
        body["error"] = error
    if payload is not None:
        body["payload"] = payload
    log_step("llm_call_end", body, level="INFO" if ok else "WARN")


__all__ = [
    "set_log_buffer",
    "reset_log_buffer",
    "log_step",
    "log_artifact",
    "log_llm_call_start",
    "log_llm_call_end",
]

