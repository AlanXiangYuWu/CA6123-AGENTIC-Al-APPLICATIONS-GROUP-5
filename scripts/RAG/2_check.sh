#!/usr/bin/env bash
set -euo pipefail

COLLECTION="${1:-business_collection_qwen3_embedding_0_6b_d1024}"
SEARCH_TEXT="${SEARCH_TEXT:-How should we prioritize product features?}"
SEARCH_MODE="${SEARCH_MODE:-hybrid}"
SEARCH_LIMIT="${SEARCH_LIMIT:-5}"

python scripts/rag/inspect_milvus.py \
  --collection "${COLLECTION}" \
  --sample-limit 5 \
  --search-text "${SEARCH_TEXT}" \
  --search-mode "${SEARCH_MODE}" \
  --search-limit "${SEARCH_LIMIT}"
