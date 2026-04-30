#!/usr/bin/env bash
set -euo pipefail

COLLECTION="${1:-technical_collection_qwen3_embedding_0_6b_d1024}"
OUT="${2:-data/rag/exports/${COLLECTION}_full.json}"
INCLUDE_VECTOR="${INCLUDE_VECTOR:-1}"

mkdir -p data/rag/exports

if [[ "${INCLUDE_VECTOR}" == "1" ]]; then
  python scripts/rag/export_milvus.py \
    --collection "${COLLECTION}" \
    --output "${OUT}" \
    --format json \
    --include-vector
else
  python scripts/rag/export_milvus.py \
    --collection "${COLLECTION}" \
    --output "${OUT}" \
    --format json
fi
