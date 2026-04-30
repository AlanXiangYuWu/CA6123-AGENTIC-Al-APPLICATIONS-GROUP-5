#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-data/rag/exports/technical_collection_qwen3_embedding_0_6b_d1024_full.json}"
COLLECTION="${2:-}"
RECREATE_IF_DIM_MISMATCH="${RECREATE_IF_DIM_MISMATCH:-0}"

cmd=(python scripts/rag/import_milvus.py --input "${INPUT}")
if [[ -n "${COLLECTION}" ]]; then
  cmd+=(--collection "${COLLECTION}")
fi
if [[ "${RECREATE_IF_DIM_MISMATCH}" == "1" ]]; then
  cmd+=(--recreate-if-dim-mismatch)
fi

"${cmd[@]}"
