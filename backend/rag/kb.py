"""ChromaDB-backed RAG with two collections (business, technical) and RBAC."""

from __future__ import annotations

from functools import lru_cache

import chromadb

from backend.core.config import get_settings
from backend.rag.access_control import AGENT_KB_ACCESS


class KnowledgeBase:
    def __init__(self, persist_dir: str | None = None) -> None:
        path = persist_dir or get_settings().kb_store_path
        self.client = chromadb.PersistentClient(path=path)
        self.business = self.client.get_or_create_collection("business")
        self.technical = self.client.get_or_create_collection("technical")
        self._seed_if_empty()

    def _seed_if_empty(self) -> None:
        if self.business.count() == 0:
            self.business.add(
                ids=["prd_template_001", "market_template_001", "user_research_001"],
                documents=[
                    "PRD template: 1.Product positioning 2.User personas 3.User flows "
                    "4.Functional requirements 5.Non-functional requirements 6.Success metrics.",
                    "Market research template: competitor matrix, user pain points, "
                    "TAM/SAM/SOM, opportunity sizing, pricing benchmarks.",
                    "User research methods: jobs-to-be-done, persona interviews, "
                    "behavioural cohort analysis, NPS surveys.",
                ],
                metadatas=[
                    {"type": "prd_template"},
                    {"type": "market_template"},
                    {"type": "research_method"},
                ],
            )
        if self.technical.count() == 0:
            self.technical.add(
                ids=["langgraph_001", "fastapi_001", "rag_pattern_001"],
                documents=[
                    "LangGraph StateGraph builds a stateful, multi-actor app. "
                    "Use add_conditional_edges for routing; checkpointer for persistence.",
                    "FastAPI: async Python web framework. Use pydantic models for "
                    "request/response validation; uvicorn as ASGI server.",
                    "RAG pattern: chunk(800,overlap=100) -> embed -> vector store -> "
                    "retrieve top-k -> LLM with citation prompt.",
                ],
                metadatas=[
                    {"type": "framework_doc"},
                    {"type": "framework_doc"},
                    {"type": "pattern"},
                ],
            )

    def retrieve(self, query: str, agent: str, k: int = 3) -> list[dict]:
        allowed = AGENT_KB_ACCESS.get(agent, [])
        out: list[dict] = []
        for kb_name in allowed:
            col = getattr(self, kb_name)
            res = col.query(query_texts=[query], n_results=k)
            if not res["documents"] or not res["documents"][0]:
                continue
            for doc, doc_id in zip(res["documents"][0], res["ids"][0]):
                out.append({"doc": doc, "source_doc_id": doc_id, "kb": kb_name})
        return out


@lru_cache(maxsize=1)
def get_kb() -> KnowledgeBase:
    return KnowledgeBase()
