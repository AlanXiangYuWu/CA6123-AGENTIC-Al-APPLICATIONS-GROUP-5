from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from typing import Any

from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer


MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
DEFAULT_EMBED_MODEL = os.getenv("EMBED_MODEL", "Qwen/Qwen3-Embedding-0.6B")
DEFAULT_LIMIT = int(os.getenv("INSPECT_LIMIT", "5"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Milvus collections and run quick checks."
    )
    parser.add_argument(
        "--uri",
        default=MILVUS_URI,
        help=f"Milvus URI, default: {MILVUS_URI}",
    )
    parser.add_argument(
        "--collection",
        default="",
        help="Target collection name. If omitted, script only lists collections.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Sample query row limit, default: {DEFAULT_LIMIT}",
    )
    parser.add_argument(
        "--search-text",
        default="",
        help="If provided, run vector search with this query text.",
    )
    parser.add_argument(
        "--search-mode",
        choices=["dense", "hybrid"],
        default="dense",
        help="Search mode: dense (vector only) or hybrid (dense + keyword RRF).",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Vector search top-k, default: {DEFAULT_LIMIT}",
    )
    parser.add_argument(
        "--embed-model",
        default=DEFAULT_EMBED_MODEL,
        help=f"Embedding model for --search-text, default: {DEFAULT_EMBED_MODEL}",
    )
    parser.add_argument(
        "--truncate-dim",
        type=int,
        default=0,
        help="Optional truncate_dim for embedding query vector.",
    )
    parser.add_argument(
        "--hybrid-candidate-multiplier",
        type=int,
        default=5,
        help="Hybrid mode candidate multiplier (effective dense top-k = search_limit * multiplier).",
    )
    return parser.parse_args()


def extract_dim(desc: dict[str, Any]) -> int | None:
    schema = desc.get("schema", {}) if isinstance(desc, dict) else {}
    fields = schema.get("fields", []) if isinstance(schema, dict) else []
    for field in fields:
        if field.get("name") != "vector":
            continue
        params = field.get("params", {})
        dim = params.get("dim") if isinstance(params, dict) else None
        if dim is None:
            dim = field.get("dim")
        if dim is not None:
            return int(dim)
    return None


def print_collection_overview(client: MilvusClient, collection_name: str) -> None:
    desc = client.describe_collection(collection_name=collection_name)
    dim = extract_dim(desc)
    print(f"\n=== {collection_name} ===")
    print(f"dimension: {dim}")
    try:
        stats = client.get_collection_stats(collection_name=collection_name)
        print(f"stats: {stats}")
    except Exception as exc:
        print(f"stats: unavailable ({exc})")


def sample_rows(
    client: MilvusClient,
    collection_name: str,
    limit: int,
) -> None:
    print(f"\nSample rows (limit={limit}):")
    try:
        rows = client.query(
            collection_name=collection_name,
            filter="id != ''",
            output_fields=["id", "doc_id", "kb_type", "source_path"],
            limit=limit,
        )
    except Exception as exc:
        print(f"sample query failed: {exc}")
        return
    if not rows:
        print("no rows found")
        return
    for i, row in enumerate(rows, start=1):
        print(
            f"[{i}] id={row.get('id')} doc_id={row.get('doc_id')} "
            f"kb_type={row.get('kb_type')} source={row.get('source_path')}"
        )


def run_vector_search(
    client: MilvusClient,
    collection_name: str,
    search_text: str,
    search_limit: int,
    embed_model: str,
    truncate_dim: int,
) -> None:
    print(
        f"\nVector search: text='{search_text}', model='{embed_model}', topk={search_limit}"
    )
    embedder = SentenceTransformer(embed_model)
    encode_kwargs: dict[str, Any] = {"normalize_embeddings": True}
    if truncate_dim > 0:
        encode_kwargs["truncate_dim"] = truncate_dim
    qvec = embedder.encode([search_text], **encode_kwargs).tolist()[0]

    results = client.search(
        collection_name=collection_name,
        data=[qvec],
        limit=search_limit,
        output_fields=["doc_id", "kb_type", "source_path", "text"],
    )
    hits = results[0] if results else []
    if not hits:
        print("no search results")
        return
    for i, hit in enumerate(hits, start=1):
        entity = hit.get("entity", {})
        snippet = (entity.get("text") or "").replace("\n", " ").strip()
        snippet = snippet[:120] + ("..." if len(snippet) > 120 else "")
        print(
            f"[{i}] score={hit.get('distance'):.4f} "
            f"doc_id={entity.get('doc_id')} kb_type={entity.get('kb_type')} "
            f"source={entity.get('source_path')} text={snippet}"
        )


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", text.lower())


def _lexical_score(query_tokens: list[str], doc_text: str) -> float:
    # Lightweight BM25-style approximation without extra dependencies.
    if not query_tokens:
        return 0.0
    doc_tokens = _tokenize(doc_text)
    if not doc_tokens:
        return 0.0
    doc_counts = Counter(doc_tokens)
    total = len(doc_tokens)
    score = 0.0
    for token in query_tokens:
        tf = doc_counts.get(token, 0)
        if tf == 0:
            continue
        score += tf / total
    return score


def run_hybrid_search(
    client: MilvusClient,
    collection_name: str,
    search_text: str,
    search_limit: int,
    embed_model: str,
    truncate_dim: int,
    candidate_multiplier: int,
) -> None:
    candidate_limit = max(search_limit, search_limit * max(1, candidate_multiplier))
    print(
        f"\nHybrid search (RRF): text='{search_text}', model='{embed_model}', "
        f"topk={search_limit}, dense_candidates={candidate_limit}"
    )
    embedder = SentenceTransformer(embed_model)
    encode_kwargs: dict[str, Any] = {"normalize_embeddings": True}
    if truncate_dim > 0:
        encode_kwargs["truncate_dim"] = truncate_dim
    qvec = embedder.encode([search_text], **encode_kwargs).tolist()[0]

    dense_results = client.search(
        collection_name=collection_name,
        data=[qvec],
        limit=candidate_limit,
        output_fields=["doc_id", "kb_type", "source_path", "text"],
    )
    dense_hits = dense_results[0] if dense_results else []
    if not dense_hits:
        print("no dense candidates")
        return

    query_tokens = _tokenize(search_text)
    dense_rank: dict[str, int] = {}
    lexical_rank_pairs: list[tuple[str, float]] = []
    entities: dict[str, dict[str, Any]] = {}

    for idx, hit in enumerate(dense_hits, start=1):
        entity = hit.get("entity", {})
        row_id = entity.get("id") or hit.get("id") or f"row_{idx}"
        row_id = str(row_id)
        dense_rank[row_id] = idx
        entities[row_id] = {
            "entity": entity,
            "dense_score": float(hit.get("distance", 0.0)),
        }
        lex = _lexical_score(query_tokens, entity.get("text", ""))
        lexical_rank_pairs.append((row_id, lex))

    lexical_rank_pairs.sort(key=lambda x: x[1], reverse=True)
    lexical_rank = {row_id: rank for rank, (row_id, _) in enumerate(lexical_rank_pairs, 1)}

    # Reciprocal Rank Fusion (RRF): score = sum(1 / (k + rank_i))
    rrf_k = 60.0
    fused: list[tuple[str, float]] = []
    for row_id in entities:
        dr = dense_rank.get(row_id, candidate_limit + 1)
        lr = lexical_rank.get(row_id, candidate_limit + 1)
        fused_score = (1.0 / (rrf_k + dr)) + (1.0 / (rrf_k + lr))
        fused.append((row_id, fused_score))
    fused.sort(key=lambda x: x[1], reverse=True)

    top_rows = fused[:search_limit]
    for i, (row_id, fused_score) in enumerate(top_rows, start=1):
        item = entities[row_id]
        entity = item["entity"]
        snippet = (entity.get("text") or "").replace("\n", " ").strip()
        snippet = snippet[:120] + ("..." if len(snippet) > 120 else "")
        print(
            f"[{i}] fused={fused_score:.6f} dense={item['dense_score']:.4f} "
            f"doc_id={entity.get('doc_id')} kb_type={entity.get('kb_type')} "
            f"source={entity.get('source_path')} text={snippet}"
        )


def main() -> None:
    args = parse_args()
    client = MilvusClient(uri=args.uri)
    collections = client.list_collections()
    print(f"Milvus URI: {args.uri}")
    print(f"Collections ({len(collections)}):")
    for name in collections:
        print(f"- {name}")

    if not args.collection:
        return
    if args.collection not in collections:
        print(f"\nCollection not found: {args.collection}")
        return

    print_collection_overview(client, args.collection)
    sample_rows(client, args.collection, args.sample_limit)

    if args.search_text.strip():
        if args.search_mode == "hybrid":
            run_hybrid_search(
                client=client,
                collection_name=args.collection,
                search_text=args.search_text.strip(),
                search_limit=args.search_limit,
                embed_model=args.embed_model,
                truncate_dim=args.truncate_dim,
                candidate_multiplier=args.hybrid_candidate_multiplier,
            )
        else:
            run_vector_search(
                client=client,
                collection_name=args.collection,
                search_text=args.search_text.strip(),
                search_limit=args.search_limit,
                embed_model=args.embed_model,
                truncate_dim=args.truncate_dim,
            )


if __name__ == "__main__":
    main()
