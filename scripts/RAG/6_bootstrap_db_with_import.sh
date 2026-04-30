#!/usr/bin/env bash
set -euo pipefail

# One-shot bootstrap for teammates:
# 1) Start persistent Milvus stack
# 2) If current Milvus is empty, import JSON exports from data/rag/exports

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${PROJECT_ROOT}"

MILVUS_URI="${MILVUS_URI:-http://127.0.0.1:19530}"
EXPORT_DIR="${EXPORT_DIR:-data/rag/exports}"
RECREATE_IF_DIM_MISMATCH="${RECREATE_IF_DIM_MISMATCH:-0}"

echo "[bootstrap] Project root: ${PROJECT_ROOT}"
echo "[bootstrap] Milvus URI: ${MILVUS_URI}"
echo "[bootstrap] Export dir: ${EXPORT_DIR}"

if [[ ! -x "scripts/rag/5_start_db.sh" ]]; then
  echo "[ERROR] Missing script: scripts/rag/5_start_db.sh"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "[ERROR] python is required."
  exit 1
fi

# Verify pymilvus exists (installed by scripts/rag/0_install.sh).
if ! python -c "import pymilvus" >/dev/null 2>&1; then
  echo "[ERROR] Missing python dependency: pymilvus"
  echo "Run: bash scripts/rag/0_install.sh"
  exit 1
fi

echo "[bootstrap] Starting Milvus stack..."
bash "scripts/rag/5_start_db.sh"

echo "[bootstrap] Checking whether Milvus already has data..."
HAS_DATA="$(python - <<'PY'
import os
from pymilvus import MilvusClient

uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
client = MilvusClient(uri=uri)

def collection_has_rows(name: str) -> bool:
    # Try official collection stats first.
    try:
        stats = client.get_collection_stats(collection_name=name)
        n = int(stats.get("row_count", "0"))
        return n > 0
    except Exception:
        pass
    # Fallback: if a collection exists but stats API is unavailable,
    # treat as non-empty to avoid duplicate imports.
    return True

try:
    names = client.list_collections() or []
except Exception:
    print("0")
    raise SystemExit(0)

has_data = any(collection_has_rows(n) for n in names)
print("1" if has_data else "0")
PY
)"

if [[ "${HAS_DATA}" == "1" ]]; then
  echo "[bootstrap] Milvus already contains data. Skip import."
  exit 0
fi

if [[ ! -d "${EXPORT_DIR}" ]]; then
  echo "[ERROR] Export directory not found: ${EXPORT_DIR}"
  echo "Place exported JSON files under ${EXPORT_DIR} and re-run."
  exit 1
fi

mapfile -t EXPORT_FILES < <(ls "${EXPORT_DIR}"/*.json 2>/dev/null || true)
if [[ ${#EXPORT_FILES[@]} -eq 0 ]]; then
  echo "[ERROR] No JSON export files found under: ${EXPORT_DIR}"
  exit 1
fi

echo "[bootstrap] Milvus is empty. Importing ${#EXPORT_FILES[@]} export file(s)..."
for f in "${EXPORT_FILES[@]}"; do
  echo "[bootstrap] Import -> ${f}"
  cmd=(python scripts/rag/import_milvus.py --uri "${MILVUS_URI}" --input "${f}")
  if [[ "${RECREATE_IF_DIM_MISMATCH}" == "1" ]]; then
    cmd+=(--recreate-if-dim-mismatch)
  fi
  "${cmd[@]}"
done

echo "[bootstrap] Done. Milvus started and exports imported."
