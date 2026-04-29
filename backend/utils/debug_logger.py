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


def _project_root() -> Path:
    # backend/utils/debug_logger.py -> backend/utils -> backend -> project root
    return Path(__file__).resolve().parents[2]


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def set_log_buffer(buf: list[str]) -> contextvars.Token:
    """Set a per-request in-memory buffer for debug lines."""
    run_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    buf_token = _buffer_var.set(buf)
    run_token = _run_id_var.set(run_id)
    # Return a combined token object so caller can reset both vars.
    return (buf_token, run_token)  # type: ignore[return-value]


def reset_log_buffer(token: Any) -> None:
    if isinstance(token, tuple) and len(token) == 2:
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


def log_step(step: str, payload: Any, *, level: str = "INFO") -> None:
    """
    Log an intermediate step.
    - Always append to `.logs/research_steps_<timestamp>.jsonl`.
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
    path = root / ".logs" / f"research_steps_{run_id}.jsonl"
    record = {"ts": ts, "level": level, "step": step, "payload": payload}
    try:
        _write_jsonl(path, record)
    except Exception:  # noqa: BLE001
        # Don't break the agent if logging fails.
        pass


def log_artifact(artifact_name: str, payload: Any) -> None:
    """
    Log artifacts (final structured outputs) to one file.
    Writes to `.logs/artifacts_<timestamp>.jsonl`.
    """
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    root = _project_root()
    run_id = _run_id_var.get()
    if not run_id:
        run_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = root / ".logs" / f"artifacts_{run_id}.jsonl"
    record = {"ts": ts, "artifact_name": artifact_name, "payload": payload}
    try:
        _write_jsonl(path, record)
    except Exception:  # noqa: BLE001
        pass


__all__ = ["set_log_buffer", "reset_log_buffer", "log_step", "log_artifact"]

