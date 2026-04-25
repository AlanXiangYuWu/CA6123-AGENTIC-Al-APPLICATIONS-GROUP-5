"""REST + WebSocket endpoints."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from backend.api.schemas import (
    HealthResponse,
    InjectionCheckRequest,
    RunRequest,
    RunResponse,
)
from backend.core.config import get_settings
from backend.core.graph import get_app
from backend.core.state import initial_state
from backend.guardrails.injection import detect_prompt_injection

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model=get_settings().llm_model)


@router.post("/guardrails/injection-check")
async def injection_check(req: InjectionCheckRequest) -> dict:
    return await asyncio.to_thread(detect_prompt_injection, req.text)


@router.post("/run", response_model=RunResponse)
async def run_pipeline(req: RunRequest) -> RunResponse:
    """One-shot: run the full pipeline and return the final state."""
    inj = await asyncio.to_thread(detect_prompt_injection, req.user_idea)
    if inj.get("is_injection") and inj.get("confidence", 0) > 0.7:
        raise HTTPException(status_code=400, detail={"blocked_by": "injection_guardrail", "evidence": inj})

    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    app = get_app()
    final = await asyncio.to_thread(app.invoke, initial_state(req.user_idea), config)

    return RunResponse(
        thread_id=thread_id,
        trace=final.get("trace", []),
        revision_round=final.get("revision_round", 0),
        project_brief=final.get("project_brief"),
        research_report=final.get("research_report"),
        prd=final.get("prd"),
        tech_design=final.get("tech_design"),
        code_artifact=final.get("code_artifact"),
        qa_report=final.get("qa_report"),
        final_package=final.get("final_package"),
        citations=final.get("citations", []),
        guardrail_flags=final.get("guardrail_flags", []),
    )


def _diff_node_update(values: dict) -> dict:
    """Strip langchain Message objects from streamed state values."""
    out = {}
    for k, v in values.items():
        if k == "messages":
            out[k] = [
                {"type": m.type, "content": getattr(m, "content", str(m))}
                for m in (v or [])
            ]
        else:
            out[k] = v
    return out


@router.websocket("/ws/run")
async def ws_run(ws: WebSocket) -> None:
    """Streaming pipeline run.

    Client -> server (first message): {"user_idea": "...", "thread_id": "..."}
    Server -> client: stream of {"event": "node_start"|"node_done"|"final"|"error", ...}
    """
    await ws.accept()
    try:
        first = await ws.receive_text()
        payload = json.loads(first)
        user_idea = payload.get("user_idea", "")
        thread_id = payload.get("thread_id") or str(uuid.uuid4())

        if len(user_idea) < 10:
            await ws.send_json({"event": "error", "message": "user_idea too short"})
            await ws.close()
            return

        inj = await asyncio.to_thread(detect_prompt_injection, user_idea)
        if inj.get("is_injection") and inj.get("confidence", 0) > 0.7:
            await ws.send_json(
                {"event": "blocked", "guardrail": "injection", "evidence": inj}
            )
            await ws.close()
            return

        await ws.send_json({"event": "started", "thread_id": thread_id})

        app = get_app()
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
        state = initial_state(user_idea)

        # Stream node updates as they complete.
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def producer() -> None:
            try:
                for chunk in app.stream(state, config, stream_mode="updates"):
                    # chunk = {"<node_name>": {<state diff>}}
                    for node_name, diff in chunk.items():
                        loop.call_soon_threadsafe(
                            queue.put_nowait,
                            {
                                "event": "node_done",
                                "node": node_name,
                                "diff": _diff_node_update(diff or {}),
                            },
                        )
                # Final snapshot
                snapshot = app.get_state(config).values
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"event": "final", "state": _diff_node_update(snapshot)},
                )
            except Exception as e:  # noqa: BLE001
                loop.call_soon_threadsafe(
                    queue.put_nowait, {"event": "error", "message": str(e)}
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        asyncio.create_task(asyncio.to_thread(producer))

        while True:
            item = await queue.get()
            if item is None:
                break
            await ws.send_json(item)

        await ws.close()
    except WebSocketDisconnect:
        return
    except Exception as e:  # noqa: BLE001
        try:
            await ws.send_json({"event": "error", "message": str(e)})
            await ws.close()
        except Exception:  # noqa: BLE001
            pass
