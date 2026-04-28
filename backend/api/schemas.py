"""Pydantic request/response models for the REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    user_idea: str = Field(..., min_length=10, max_length=4000)
    thread_id: str | None = None


class GuardrailFlag(BaseModel):
    type: str
    target: str | None = None
    file: str | None = None
    issue: str | None = None
    description: str | None = None


class RunResponse(BaseModel):
    thread_id: str
    trace: list[str]
    revision_round: int
    project_brief: dict | None = None
    research_report: dict | None = None
    prd: dict | None = None
    tech_design: dict | None = None
    code_artifact: dict | None = None
    qa_report: dict | None = None
    final_package: dict | None = None
    citations: list[dict] = []
    guardrail_flags: list[dict] = []


class InjectionCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class HealthResponse(BaseModel):
    status: str
    model: str
