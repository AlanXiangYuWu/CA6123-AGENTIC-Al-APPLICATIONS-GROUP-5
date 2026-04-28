from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TESTSET = ROOT / "data" / "rag" / "eval" / "ragas_business_testset.json"
DEFAULT_COLLECTION = "business_collection_qwen3_embedding_0_6b_d1024"
DEFAULT_MODE = "hybrid"
DEFAULT_TOPK = 5
DEFAULT_MILVUS_URI = "http://127.0.0.1:19530"
DEFAULT_EMBED_MODEL = "Qwen/Qwen3-Embedding-0.6B"

SCORED_TYPES = {"standard", "query_variant", "reasoning"}
CORNER_TYPE = "corner_case"


@dataclass
class RetrievalHit:
    rank: int
    doc_id: str
    score: float
    source_path: str
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval accuracy on ragas_business_testset.json."
    )
    parser.add_argument("--testset", default=str(DEFAULT_TESTSET))
    parser.add_argument("--milvus-uri", default=DEFAULT_MILVUS_URI)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--search-mode", choices=["dense", "hybrid"], default=DEFAULT_MODE)
    parser.add_argument("--search-limit", type=int, default=DEFAULT_TOPK)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--truncate-dim", type=int, default=0)
    parser.add_argument(
        "--hybrid-candidate-multiplier",
        type=int,
        default=5,
        help="Only used in hybrid mode; candidate_size = search_limit * multiplier.",
    )
    parser.add_argument(
        "--save-details",
        default="",
        help="Optional path to save per-case JSON result.",
    )
    parser.add_argument(
        "--save-top1-json",
        default="",
        help=(
            "Optional path to save top1 retrieval file for manual review. "
            "Output keeps testset-like structure and appends top1 fields."
        ),
    )
    parser.add_argument(
        "--run-ragas",
        action="store_true",
        help="Run an additional RAGAS evaluation layer for standard/query_variant/reasoning.",
    )
    parser.add_argument(
        "--ragas-output",
        default="",
        help="Optional path to save RAGAS summary JSON.",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", text.lower())


def lexical_score(query_tokens: list[str], doc_text: str) -> float:
    if not query_tokens:
        return 0.0
    tokens = tokenize(doc_text)
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    n = len(tokens)
    score = 0.0
    for token in query_tokens:
        tf = counts.get(token, 0)
        if tf:
            score += tf / n
    return score


def encode_query(
    embedder: SentenceTransformer,
    question: str,
    truncate_dim: int,
) -> list[float]:
    kwargs: dict[str, Any] = {"normalize_embeddings": True}
    if truncate_dim > 0:
        kwargs["truncate_dim"] = truncate_dim
    return embedder.encode([question], **kwargs).tolist()[0]


def dense_search(
    client: MilvusClient,
    collection: str,
    query_vec: list[float],
    topk: int,
) -> list[RetrievalHit]:
    results = client.search(
        collection_name=collection,
        data=[query_vec],
        limit=topk,
        output_fields=["doc_id", "source_path", "text"],
    )
    hits = results[0] if results else []
    out: list[RetrievalHit] = []
    for rank, hit in enumerate(hits, start=1):
        entity = hit.get("entity", {})
        out.append(
            RetrievalHit(
                rank=rank,
                doc_id=str(entity.get("doc_id") or ""),
                score=float(hit.get("distance", 0.0)),
                source_path=str(entity.get("source_path") or ""),
                text=str(entity.get("text") or ""),
            )
        )
    return out


def hybrid_search(
    client: MilvusClient,
    collection: str,
    query_text: str,
    query_vec: list[float],
    topk: int,
    candidate_multiplier: int,
) -> list[RetrievalHit]:
    candidate_k = max(topk, topk * max(1, candidate_multiplier))
    dense_hits = dense_search(client, collection, query_vec, candidate_k)
    if not dense_hits:
        return []
    query_tokens = tokenize(query_text)
    rrf_k = 60.0

    indexed_dense_hits = list(enumerate(dense_hits, start=1))
    dense_rank = {idx: idx for idx, _ in indexed_dense_hits}
    lexical_order = sorted(
        indexed_dense_hits,
        key=lambda pair: lexical_score(query_tokens, pair[1].text),
        reverse=True,
    )
    lexical_rank = {dense_idx: rank for rank, (dense_idx, _) in enumerate(lexical_order, 1)}

    fused: list[tuple[float, RetrievalHit]] = []
    for dense_idx, h in indexed_dense_hits:
        dr = dense_rank.get(dense_idx, candidate_k + 1)
        lr = lexical_rank.get(dense_idx, candidate_k + 1)
        score = (1.0 / (rrf_k + dr)) + (1.0 / (rrf_k + lr))
        fused.append((score, h))
    fused.sort(key=lambda x: x[0], reverse=True)

    out: list[RetrievalHit] = []
    for rank, (score, h) in enumerate(fused[:topk], start=1):
        out.append(
            RetrievalHit(
                rank=rank,
                doc_id=h.doc_id,
                score=score,
                source_path=h.source_path,
                text=h.text,
            )
        )
    return out


def evaluate_case(
    case: dict[str, Any],
    hits: list[RetrievalHit],
) -> dict[str, Any]:
    expected = set(case.get("expected_doc_ids", []))
    retrieved_doc_ids = [h.doc_id for h in hits]
    retrieved_set = set(retrieved_doc_ids)

    matched = sorted(expected.intersection(retrieved_set))
    hit = bool(matched) if expected else False
    recall = (len(matched) / len(expected)) if expected else None

    mrr = 0.0
    if expected:
        for idx, doc_id in enumerate(retrieved_doc_ids, start=1):
            if doc_id in expected:
                mrr = 1.0 / idx
                break

    return {
        "id": case["id"],
        "type": case["type"],
        "agent": case.get("agent", ""),
        "question": case["question"],
        "ground_truth": case.get("ground_truth", ""),
        "expected_doc_ids": sorted(expected),
        "retrieved_doc_ids": retrieved_doc_ids,
        "matched_doc_ids": matched,
        "hit_at_k": hit,
        "recall_at_k": recall,
        "mrr": mrr,
        "retrieved_contexts": [h.text for h in hits],
        "retrieved_items": [
            {
                "rank": h.rank,
                "doc_id": h.doc_id,
                "score": h.score,
                "source_path": h.source_path,
                "text": h.text,
            }
            for h in hits
        ],
        "raw_case": case,
    }


def print_summary(rows: list[dict[str, Any]], topk: int) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["type"]].append(row)

    print("\n=== Retrieval Accuracy Summary ===")
    for group_name in ["standard", "query_variant", "reasoning", "corner_case"]:
        group = groups.get(group_name, [])
        if not group:
            continue
        scored_group = [x for x in group if x["type"] in SCORED_TYPES]
        if scored_group:
            hit_rate = sum(1 for x in scored_group if x["hit_at_k"]) / len(scored_group)
            recall_vals = [x["recall_at_k"] for x in scored_group if x["recall_at_k"] is not None]
            mrr_vals = [x["mrr"] for x in scored_group]
            avg_recall = sum(recall_vals) / len(recall_vals) if recall_vals else 0.0
            avg_mrr = sum(mrr_vals) / len(mrr_vals) if mrr_vals else 0.0
            print(
                f"- {group_name:<13} n={len(scored_group):<3} "
                f"hit@{topk}={hit_rate:.3f} recall@{topk}={avg_recall:.3f} mrr={avg_mrr:.3f}"
            )
        else:
            print(
                f"- {group_name:<13} n={len(group):<3} manual_review_only "
                "(corner case)"
            )

    scored_rows = [x for x in rows if x["type"] in SCORED_TYPES]
    if scored_rows:
        overall_hit = sum(1 for x in scored_rows if x["hit_at_k"]) / len(scored_rows)
        overall_recall = sum(x["recall_at_k"] or 0.0 for x in scored_rows) / len(scored_rows)
        overall_mrr = sum(x["mrr"] for x in scored_rows) / len(scored_rows)
        print(
            f"- {'overall(scored)':<13} n={len(scored_rows):<3} "
            f"hit@{topk}={overall_hit:.3f} recall@{topk}={overall_recall:.3f} mrr={overall_mrr:.3f}"
        )


def print_failures(rows: list[dict[str, Any]], topk: int) -> None:
    failed = [r for r in rows if r["type"] in SCORED_TYPES and not r["hit_at_k"]]
    print(f"\n=== Misses (hit@{topk}=0) ===")
    if not failed:
        print("No misses in scored sets.")
        return
    for row in failed:
        print(
            f"- {row['id']} [{row['type']}] expected={row['expected_doc_ids']} "
            f"retrieved={row['retrieved_doc_ids']}"
        )


def print_corner_review(rows: list[dict[str, Any]]) -> None:
    corner = [r for r in rows if r["type"] == CORNER_TYPE]
    if not corner:
        return
    print("\n=== Corner Case Manual Review ===")
    for row in corner:
        top_docs = row["retrieved_doc_ids"][:3]
        print(
            f"- {row['id']}: top_docs={top_docs} "
            f"(expected_behavior in dataset, review manually)"
        )


def run_ragas_pipeline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Keep corner_case outside automatic scoring, as requested.
    ragas_rows = [r for r in rows if r["type"] in SCORED_TYPES]
    if not ragas_rows:
        return {"status": "skipped", "reason": "no scored rows"}

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import context_precision, context_recall
    except Exception as exc:
        return {
            "status": "unavailable",
            "reason": (
                "RAGAS dependencies not ready. "
                "Please install: pip install ragas datasets"
            ),
            "error": str(exc),
        }

    ragas_samples = [
        {
            "question": r["question"],
            "contexts": r["retrieved_contexts"],
            "ground_truth": r["ground_truth"],
        }
        for r in ragas_rows
    ]
    dataset = Dataset.from_list(ragas_samples)

    try:
        result = evaluate(dataset=dataset, metrics=[context_precision, context_recall])
    except Exception as exc:
        return {
            "status": "failed",
            "reason": "RAGAS evaluate() execution failed",
            "error": str(exc),
            "sample_size": len(ragas_rows),
        }

    result_dict = {}
    try:
        result_dict = result.to_pandas().mean(numeric_only=True).to_dict()
    except Exception:
        # Fallback for different ragas versions
        try:
            result_dict = dict(result)
        except Exception:
            result_dict = {"raw_result": str(result)}

    return {
        "status": "ok",
        "sample_size": len(ragas_rows),
        "metrics": result_dict,
    }


def build_top1_review_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        case = dict(row.get("raw_case", {}))
        retrieved_items = row.get("retrieved_items", [])
        top1 = retrieved_items[0] if retrieved_items else {}

        # Keep testset-style fields and append retrieval outcome for manual review.
        case["retrieved_top1_doc_ids"] = [top1["doc_id"]] if top1.get("doc_id") else []
        case["retrieved_top1_score"] = top1.get("score")
        case["retrieved_top1_source_path"] = top1.get("source_path")
        case["retrieved_top1_text"] = top1.get("text")
        out.append(case)
    return out


def main() -> None:
    args = parse_args()
    testset_path = Path(args.testset).resolve()
    cases = load_cases(testset_path)

    client = MilvusClient(uri=args.milvus_uri)
    collections = client.list_collections()
    if args.collection not in collections:
        raise RuntimeError(
            f"Collection not found: {args.collection}. Available: {collections}"
        )
    embedder = SentenceTransformer(args.embed_model)

    print(f"Testset: {testset_path}")
    print(f"Collection: {args.collection}")
    print(f"Search mode: {args.search_mode}, topk={args.search_limit}")
    print(f"Embed model: {args.embed_model}")
    print(f"Total cases: {len(cases)}")

    rows: list[dict[str, Any]] = []
    for case in cases:
        q = case["question"]
        qvec = encode_query(embedder, q, args.truncate_dim)
        if args.search_mode == "hybrid":
            hits = hybrid_search(
                client=client,
                collection=args.collection,
                query_text=q,
                query_vec=qvec,
                topk=args.search_limit,
                candidate_multiplier=args.hybrid_candidate_multiplier,
            )
        else:
            hits = dense_search(
                client=client,
                collection=args.collection,
                query_vec=qvec,
                topk=args.search_limit,
            )
        rows.append(evaluate_case(case, hits))

    print_summary(rows, args.search_limit)
    print_failures(rows, args.search_limit)
    print_corner_review(rows)

    if args.run_ragas:
        print("\n=== RAGAS (scored types only) ===")
        ragas_result = run_ragas_pipeline(rows)
        print(json.dumps(ragas_result, ensure_ascii=False, indent=2))
        if args.ragas_output:
            ragas_path = Path(args.ragas_output).resolve()
            ragas_path.parent.mkdir(parents=True, exist_ok=True)
            ragas_path.write_text(
                json.dumps(ragas_result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved RAGAS result: {ragas_path}")

    if args.save_details:
        out_path = Path(args.save_details).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved detailed result: {out_path}")

    if args.save_top1_json:
        top1_path = Path(args.save_top1_json).resolve()
        top1_path.parent.mkdir(parents=True, exist_ok=True)
        top1_rows = build_top1_review_rows(rows)
        top1_path.write_text(
            json.dumps(top1_rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Saved top1 review JSON: {top1_path}")


if __name__ == "__main__":
    main()
