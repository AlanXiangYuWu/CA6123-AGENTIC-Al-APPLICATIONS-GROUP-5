from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pymilvus import DataType, MilvusClient


DEFAULT_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
DEFAULT_BATCH = int(os.getenv("MILVUS_IMPORT_BATCH", "256"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import exported Milvus JSON/JSONL file.")
    p.add_argument("--uri", default=DEFAULT_URI, help=f"Milvus URI (default: {DEFAULT_URI})")
    p.add_argument("--input", required=True, type=Path, help="Export file path")
    p.add_argument(
        "--collection",
        default="",
        help="Target collection name. If empty, use name from export meta.",
    )
    p.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    p.add_argument(
        "--recreate-if-dim-mismatch",
        action="store_true",
        help="Drop and recreate target collection if vector dim mismatches.",
    )
    return p.parse_args()


def load_export(path: Path) -> tuple[str, list[dict[str, Any]]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or "data" not in obj:
        raise ValueError("Invalid export format: expected top-level object with key 'data'.")
    rows = obj["data"]
    if not isinstance(rows, list):
        raise ValueError("This importer expects single-collection export where data is a list.")
    meta = obj.get("meta", {})
    cols = meta.get("collections", []) if isinstance(meta, dict) else []
    src_collection = cols[0] if cols else ""
    if not rows:
        raise ValueError("Export file contains 0 rows.")
    return src_collection, rows


def get_dim(rows: list[dict[str, Any]]) -> int:
    vec = rows[0].get("vector")
    if not isinstance(vec, list) or not vec:
        raise ValueError("Missing vector field in export rows; cannot infer dimension.")
    return len(vec)


def ensure_collection(client: MilvusClient, name: str, dim: int, recreate: bool) -> None:
    if client.has_collection(name):
        info = client.describe_collection(collection_name=name)
        existing_dim = _extract_vector_dim(info)
        if existing_dim is None:
            raise RuntimeError(f"Cannot infer vector dim from existing collection: {name}")
        if existing_dim != dim:
            if not recreate:
                raise RuntimeError(
                    f"Collection {name} dim mismatch: existing={existing_dim}, import={dim}. "
                    "Use --recreate-if-dim-mismatch or import to a different --collection."
                )
            client.drop_collection(collection_name=name)
        else:
            return

    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=64)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field("text", DataType.VARCHAR, max_length=65535)
    schema.add_field("source_path", DataType.VARCHAR, max_length=1024)
    schema.add_field("doc_id", DataType.VARCHAR, max_length=128)
    schema.add_field("kb_type", DataType.VARCHAR, max_length=32)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")
    client.create_collection(collection_name=name, schema=schema, index_params=index_params)


def _extract_vector_dim(collection_info: dict[str, Any]) -> int | None:
    schema = collection_info.get("schema") if isinstance(collection_info, dict) else None
    if isinstance(schema, dict):
        for field in schema.get("fields", []):
            if field.get("name") != "vector":
                continue
            dim = field.get("params", {}).get("dim")
            if dim is None:
                dim = field.get("dim")
            if dim is not None:
                return int(dim)
    for field in collection_info.get("fields", []) if isinstance(collection_info, dict) else []:
        if field.get("name") != "vector":
            continue
        dim = field.get("params", {}).get("dim")
        if dim is None:
            dim = field.get("dim")
        if dim is not None:
            return int(dim)
    return None


def import_rows(client: MilvusClient, collection: str, rows: list[dict[str, Any]], batch_size: int) -> None:
    total = len(rows)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        client.insert(collection_name=collection, data=rows[start:end])
        print(f"inserted {end}/{total}")
    client.flush(collection_name=collection)


def main() -> None:
    args = parse_args()
    src_collection, rows = load_export(args.input.resolve())
    target_collection = args.collection or src_collection
    if not target_collection:
        raise SystemExit("No collection name available. Pass --collection explicitly.")

    dim = get_dim(rows)
    client = MilvusClient(uri=args.uri)
    ensure_collection(
        client=client,
        name=target_collection,
        dim=dim,
        recreate=args.recreate_if_dim_mismatch,
    )
    import_rows(client, target_collection, rows, args.batch_size)
    print(f"Import complete: {target_collection} ({len(rows)} rows, dim={dim})")


if __name__ == "__main__":
    main()
