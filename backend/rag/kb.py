"""Milvus-backed RAG with two knowledge scopes (business, technical) and RBAC."""

from __future__ import annotations

from functools import lru_cache
import os
import re

from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

from backend.rag.access_control import AGENT_KB_ACCESS

_OVERRIDE_BUSINESS_COLLECTION: str | None = None
_OVERRIDE_TECHNICAL_COLLECTION: str | None = None


class KnowledgeBase:
    def __init__(self) -> None:
        self.milvus_uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
        self.embed_model_name = os.getenv("EMBED_MODEL", "Qwen/Qwen3-Embedding-0.6B")
        # Default to the validated 0.6B/1024 setup unless caller overrides via env.
        self.embed_truncate_dim = int(os.getenv("EMBED_TRUNCATE_DIM", "1024") or "1024")
        self.default_k = int(os.getenv("RAG_TOP_K", "3") or "3")
        # Query-time instruct options (enabled by default for retrieval models).
        self.enable_query_instruct = (
            os.getenv("RAG_ENABLE_QUERY_INSTRUCT", "1").strip() not in ("0", "false", "False")
        )
        self.query_prompt_name = os.getenv("RAG_QUERY_PROMPT_NAME", "query").strip() or "query"
        self.query_instruction = os.getenv(
            "RAG_QUERY_INSTRUCTION",
            "Given a user query, retrieve relevant passages from the knowledge base.",
        ).strip()

        # Runtime override for exact collection names.
        self.business_collection_override = (
            _OVERRIDE_BUSINESS_COLLECTION
            if _OVERRIDE_BUSINESS_COLLECTION is not None
            else os.getenv("BUSINESS_COLLECTION", "").strip()
        )
        self.technical_collection_override = (
            _OVERRIDE_TECHNICAL_COLLECTION
            if _OVERRIDE_TECHNICAL_COLLECTION is not None
            else os.getenv("TECHNICAL_COLLECTION", "").strip()
        )

        self.client = MilvusClient(uri=self.milvus_uri)
        self.collections = self._resolve_collections()

    def _resolve_collections(self) -> dict[str, str]:
        names = set(self.client.list_collections())
        resolved: dict[str, str] = {}

        if self.business_collection_override:
            if self.business_collection_override not in names:
                raise RuntimeError(
                    f"BUSINESS_COLLECTION={self.business_collection_override!r} not found in Milvus."
                )
            resolved["business"] = self.business_collection_override
        else:
            resolved["business"] = self._pick_latest_collection(
                names, base_prefix="business_collection_"
            )

        if self.technical_collection_override:
            if self.technical_collection_override not in names:
                raise RuntimeError(
                    f"TECHNICAL_COLLECTION={self.technical_collection_override!r} not found in Milvus."
                )
            resolved["technical"] = self.technical_collection_override
        else:
            resolved["technical"] = self._pick_latest_collection(
                names, base_prefix="technical_collection_"
            )
        return resolved

    @staticmethod
    def _pick_latest_collection(all_names: set[str], base_prefix: str) -> str:
        # Prefer the validated 0.6B + d1024 collection when available.
        preferred = f"{base_prefix}qwen3_embedding_0_6b_d1024"
        if preferred in all_names:
            return preferred

        candidates = sorted(n for n in all_names if n.startswith(base_prefix))
        if candidates:
            return candidates[-1]

        # Backward-compatible plain name fallback.
        plain_name = base_prefix.rstrip("_")
        if plain_name in all_names:
            return plain_name

        raise RuntimeError(
            f"No Milvus collection found for prefix {base_prefix!r}. "
            "Please run scripts/rag/index_milvus.py first or set "
            "BUSINESS_COLLECTION/TECHNICAL_COLLECTION explicitly."
        )

    @lru_cache(maxsize=1)
    def _embedder(self) -> SentenceTransformer:
        return SentenceTransformer(self.embed_model_name)

    def _embed_query(self, query: str) -> list[float]:
        kwargs: dict = {"normalize_embeddings": True}
        if self.embed_truncate_dim > 0:
            kwargs["truncate_dim"] = self.embed_truncate_dim
        embedder = self._embedder()

        # Prefer retrieval-instruct style query embeddings when supported by model.
        if self.enable_query_instruct:
            try:
                vec = embedder.encode(
                    [query],
                    prompt_name=self.query_prompt_name,
                    **kwargs,
                ).tolist()[0]
                return vec
            except TypeError:
                # Some model wrappers may not support prompt_name.
                pass
            except Exception:
                # Fallback to plain encoding below.
                pass
            try:
                vec = embedder.encode(
                    [query],
                    prompt=f"Instruct: {self.query_instruction}\nQuery: ",
                    **kwargs,
                ).tolist()[0]
                return vec
            except TypeError:
                pass
            except Exception:
                pass

        vec = embedder.encode([query], **kwargs).tolist()[0]
        return vec

    def retrieve(self, query: str, agent: str, k: int = 3) -> list[dict]:
        allowed = AGENT_KB_ACCESS.get(agent, [])
        out: list[dict] = []

        if not query.strip():
            return out

        qvec = self._embed_query(query)
        topk = k or self.default_k

        for kb_name in allowed:
            collection_name = self.collections.get(kb_name)
            if not collection_name:
                continue
            try:
                res = self.client.search(
                    collection_name=collection_name,
                    data=[qvec],
                    limit=topk,
                    output_fields=["id", "doc_id", "kb_type", "source_path", "text"],
                )
            except Exception:
                continue

            hits = res[0] if res else []
            for hit in hits:
                entity = hit.get("entity", {}) if isinstance(hit, dict) else {}
                text = entity.get("text", "")
                if not isinstance(text, str) or not text.strip():
                    continue
                doc_id = (
                    entity.get("doc_id")
                    or entity.get("id")
                    or self._source_to_doc_id(entity.get("source_path", ""))
                )
                out.append(
                    {
                        "doc": text,
                        "source_doc_id": str(doc_id or ""),
                        "kb": kb_name,
                    }
                )
        return out

    @staticmethod
    def _source_to_doc_id(source_path: str) -> str:
        if not source_path:
            return ""
        # Convert ".../name.md" -> "name"
        m = re.search(r"([^/\\]+)\.md$", str(source_path), re.IGNORECASE)
        if m:
            return m.group(1)
        return str(source_path)


@lru_cache(maxsize=1)
def get_kb() -> KnowledgeBase:
    return KnowledgeBase()


def configure_kb_collections(
    business_collection: str | None = None,
    technical_collection: str | None = None,
) -> dict[str, str]:
    """Set runtime collection overrides and refresh cached KB instance."""
    global _OVERRIDE_BUSINESS_COLLECTION, _OVERRIDE_TECHNICAL_COLLECTION
    _OVERRIDE_BUSINESS_COLLECTION = (business_collection or "").strip() or None
    _OVERRIDE_TECHNICAL_COLLECTION = (technical_collection or "").strip() or None
    get_kb.cache_clear()
    kb = get_kb()
    return kb.collections


def get_kb_runtime_status() -> dict:
    """Return active Milvus/collection runtime info for debugging."""
    kb = get_kb()
    return {
        "milvus_uri": kb.milvus_uri,
        "embed_model": kb.embed_model_name,
        "embed_truncate_dim": kb.embed_truncate_dim,
        "enable_query_instruct": kb.enable_query_instruct,
        "query_prompt_name": kb.query_prompt_name,
        "active_collections": kb.collections,
        "overrides": {
            "business": _OVERRIDE_BUSINESS_COLLECTION,
            "technical": _OVERRIDE_TECHNICAL_COLLECTION,
        },
    }
