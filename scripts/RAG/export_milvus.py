"""Export Milvus collection rows to a local JSON / JSONL file (batch query).

Milvus has no single-file "dump entire server" in the Python client; this script
pulls all rows via repeated ``query`` calls and writes one output file.

By default vectors are omitted (large). Use ``--include-vector`` for a full backup.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pymilvus import MilvusClient


DEFAULT_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
DEFAULT_BATCH = int(os.getenv("MILVUS_EXPORT_BATCH", "256"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export Milvus collection(s) to JSON/JSONL.")
    p.add_argument("--uri", default=DEFAULT_URI, help=f"Milvus URI (default: {DEFAULT_URI})")
    p.add_argument(
        "--collection",
        default="",
        help="Single collection name to export. Ignored if --all-collections is set.",
    )
    p.add_argument(
        "--all-collections",
        action="store_true",
        help="Export every collection on the instance into one file (see --format).",
    )
    p.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output file path, e.g. data/rag/exports/milvus_backup.json",
    )
    p.add_argument(
        "--format",
        choices=("json", "jsonl"),
        default="json",
        help="json: one object (single coll) or {name: rows} (multi). jsonl: one row per line.",
    )
    p.add_argument("--batch-size", type=int, default=DEFAULT_BATCH, help="Rows per query page.")
    p.add_argument(
        "--include-vector",
        action="store_true",
        help="Include float vector field (much larger file).",
    )
    p.add_argument(
        "--filter",
        default='id != ""',
        help='Milvus filter expression for query (default: all rows with non-empty id).',
    )
    return p.parse_args()


def default_output_fields(include_vector: bool) -> list[str]:
    base = ["id", "text", "source_path", "doc_id", "kb_type"]
    if include_vector:
        return ["id", "vector", "text", "source_path", "doc_id", "kb_type"]
    return base


def query_all_rows(
    client: MilvusClient,
    collection_name: str,
    output_fields: list[str],
    batch_size: int,
    filter_expr: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        try:
            batch = client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields,
                limit=batch_size,
                offset=offset,
            )
        except TypeError:
            # Older pymilvus without offset: single-page export only.
            if offset != 0:
                raise RuntimeError(
                    "Paged export requires pymilvus MilvusClient.query(..., offset=...). "
                    "Upgrade pymilvus or use Milvus Backup / smaller batch."
                ) from None
            batch = client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields,
                limit=batch_size,
            )
            if len(batch) >= batch_size:
                raise RuntimeError(
                    "Milvus client does not support query offset; exported only the first "
                    f"{batch_size} rows. Upgrade pymilvus or increase --batch-size."
                )
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += len(batch)
    return rows


def main() -> None:
    args = parse_args()
    client = MilvusClient(uri=args.uri)
    names = client.list_collections()
    if args.all_collections:
        target_names = sorted(names)
    else:
        if not args.collection:
            raise SystemExit("Pass --collection NAME or use --all-collections.")
        if args.collection not in names:
            raise SystemExit(
                f"Collection not found: {args.collection}. Available: {names}"
            )
        target_names = [args.collection]

    output_fields = default_output_fields(args.include_vector)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "jsonl":
        with args.output.open("w", encoding="utf-8") as f:
            for coll in target_names:
                rows = query_all_rows(
                    client,
                    coll,
                    output_fields,
                    args.batch_size,
                    args.filter,
                )
                for row in rows:
                    line = {"collection": coll, **row}
                    f.write(json.dumps(line, ensure_ascii=False) + "\n")
        print(
            f"Wrote JSONL: {args.output.resolve()} "
            f"({len(target_names)} collection(s), vectors={'on' if args.include_vector else 'off'})"
        )
        return

    # json
    if len(target_names) == 1:
        coll = target_names[0]
        payload = query_all_rows(
            client,
            coll,
            output_fields,
            args.batch_size,
            args.filter,
        )
    else:
        payload = {}
        for coll in target_names:
            payload[coll] = query_all_rows(
                client,
                coll,
                output_fields,
                args.batch_size,
                args.filter,
            )

    meta = {
        "milvus_uri": args.uri,
        "collections": target_names,
        "include_vector": args.include_vector,
        "row_counts": (
            {target_names[0]: len(payload)}
            if len(target_names) == 1
            else {k: len(v) for k, v in payload.items()}
        ),
    }
    out_obj = {"meta": meta, "data": payload}
    args.output.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote JSON: {args.output.resolve()} "
        f"({len(target_names)} collection(s), vectors={'on' if args.include_vector else 'off'})"
    )


if __name__ == "__main__":
    main()
