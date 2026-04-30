# Bootstrap Milvus DB (Teammates)

## Prerequisites

- Docker Desktop installed and running
- Python 3 available in terminal
- Python deps installed once:

```bash
bash scripts/rag/0_install.sh
```

## Start DB + Auto Import

Before running bootstrap, place:
- `data/rag/exports/milvus_all.json`

under:
- `data/rag/exports/`

```bash
bash scripts/rag/6_bootstrap_db_with_import.sh
```

What it does:
- starts persistent Milvus containers (`etcd`, `minio`, `milvus-standalone`)
- checks whether Milvus already has data
- if empty, imports all JSON files from `data/rag/exports`

## Optional env vars

- `MILVUS_URI` (default: `http://127.0.0.1:19530`)
- `EXPORT_DIR` (default: `data/rag/exports`)
- `RECREATE_IF_DIM_MISMATCH=1` to recreate collection on vector-dim mismatch
