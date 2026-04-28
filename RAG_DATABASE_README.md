# RAG Database Operations (Milvus)

> Prebuilt snapshot: `data/rag/exports/milvus_all.json` is the exported file of the already-built Milvus vector database in this project.
> You can use it directly for sharing or restoring collections via `scripts/rag/import_milvus.py`.

This document is the single operational guide for the Milvus-based RAG database in this repository.
It consolidates setup, indexing, validation, evaluation, export/import, and troubleshooting.

---

## 1) Scope and Scripts

This guide covers the following scripts:

- `scripts/rag/index_milvus.py` — build/update vector collections from Markdown files
- `scripts/rag/inspect_milvus.py` — inspect collections and run dense/hybrid retrieval checks
- `scripts/rag/export_milvus.py` — export one/all collections to JSON/JSONL
- `scripts/rag/import_milvus.py` — import exported JSON into Milvus
- `scripts/rag/eval_retrieval_accuracy.py` — retrieval evaluation (and optional RAGAS)

Data source directory:

- `data/rag/raw/business_kb/**.md`
- `data/rag/raw/technical_kb/**.md`

---

## 2) Prerequisites

## 2.1 Python dependencies

```bash
pip install "pymilvus>=2.4.0" "sentence-transformers>=3.0.0" "tqdm>=4.0.0"
```

Optional (only if you want to run RAGAS in evaluation):

```bash
pip install ragas datasets
```

## 2.2 Milvus service

Default URI used by scripts:

- `MILVUS_URI=http://127.0.0.1:19530`

For local Docker setup (Windows + WSL), follow `Milvus_RAG_构建指南.md`.
Daily restart pattern:

```bash
docker start milvus-etcd milvus-minio milvus-standalone
```

---

## 3) Collection Naming and Data Routing

`index_milvus.py` routes files by path:

- path contains `business` / `business_kb` / `biz` -> business collection
- path contains `technical` / `technical_kb` / `tech` -> technical collection

Collections are model/dimension-specific:

- `business_collection_<model_tag>_d<dim>`
- `technical_collection_<model_tag>_d<dim>`

Example:

- `business_collection_qwen3_embedding_0_6b_d1024`
- `technical_collection_qwen3_embedding_0_6b_d1024`

README files under KB folders are excluded from indexing.

---

## 4) Build / Update the RAG Database

## 4.1 Build both business + technical

```bash
EMBED_MODEL=Qwen/Qwen3-Embedding-0.6B python scripts/rag/index_milvus.py
```

## 4.2 Build only one KB subset

Technical only:

```bash
INDEX_KB=technical EMBED_MODEL=Qwen/Qwen3-Embedding-0.6B python scripts/rag/index_milvus.py
```

Business only:

```bash
INDEX_KB=business EMBED_MODEL=Qwen/Qwen3-Embedding-0.6B python scripts/rag/index_milvus.py
```

## 4.3 Force restart checkpoint state

```bash
FORCE_RESTART=1 EMBED_MODEL=Qwen/Qwen3-Embedding-0.6B python scripts/rag/index_milvus.py
```

## 4.4 Handle dimension mismatch automatically

If collection dim and embedding dim differ:

```bash
AUTO_RECREATE_COLLECTION=1 EMBED_MODEL=Qwen/Qwen3-Embedding-8B python scripts/rag/index_milvus.py
```

Warning: this may drop and recreate mismatched collections.

## 4.5 Useful indexing environment variables

- `MILVUS_URI` (default: `http://127.0.0.1:19530`)
- `EMBED_MODEL` (default: `Qwen/Qwen3-Embedding-8B`)
- `EMBED_BATCH_SIZE` (default: `4`)
- `EMBED_TRUNCATE_DIM` (default: `0`, disabled)
- `INDEX_KB` (`all` | `business` | `technical`)
- `FORCE_RESTART` (`0` | `1`)
- `AUTO_RECREATE_COLLECTION` (`0` | `1`)
- `COLLECTION_SUFFIX` (optional custom suffix in collection name)

---

## 4.6 One-click Bash entrypoints

- Install deps: `bash scripts/rag/0_install.sh`
- Build index: `bash scripts/rag/1_build.sh`
- Check retrieval: `bash scripts/rag/2_check.sh`
- Export collection: `bash scripts/rag/3_export.sh`
- Import collection: `bash scripts/rag/4_import.sh`

These wrappers are intentionally minimal and can be customized via environment variables.

---

## 5) Inspect and Query the Database

## 5.1 List collections

```bash
python scripts/rag/inspect_milvus.py
```

## 5.2 Inspect one collection + sample rows

```bash
python scripts/rag/inspect_milvus.py \
  --collection business_collection_qwen3_embedding_0_6b_d1024 \
  --sample-limit 10
```

## 5.3 Dense retrieval check

```bash
python scripts/rag/inspect_milvus.py \
  --collection business_collection_qwen3_embedding_0_6b_d1024 \
  --search-text "How should we prioritize product features?" \
  --search-mode dense \
  --search-limit 5
```

## 5.4 Hybrid retrieval check (RRF fusion)

```bash
python scripts/rag/inspect_milvus.py \
  --collection business_collection_qwen3_embedding_0_6b_d1024 \
  --search-text "How should we prioritize product features?" \
  --search-mode hybrid \
  --search-limit 5 \
  --hybrid-candidate-multiplier 5
```

---

## 6) Retrieval Evaluation Workflow

Dataset:

- `data/rag/eval/ragas_business_testset.json`

Test categories in the dataset:

- `standard`
- `query_variant`
- `reasoning`
- `corner_case` (manual review)

## 6.1 Retrieval-only evaluation (recommended default)

```bash
python scripts/rag/eval_retrieval_accuracy.py \
  --collection business_collection_qwen3_embedding_0_6b_d1024 \
  --search-mode hybrid \
  --search-limit 5
```

## 6.2 Save top-1 results for manual review

This creates a JSON with testset-like records plus top-1 retrieval fields.

```bash
python scripts/rag/eval_retrieval_accuracy.py \
  --collection business_collection_qwen3_embedding_0_6b_d1024 \
  --search-mode hybrid \
  --search-limit 5 \
  --save-top1-json data/rag/eval/results/top1_for_manual_review.json
```

## 6.3 Optional RAGAS layer

Disabled by default; enable only when needed:

```bash
python scripts/rag/eval_retrieval_accuracy.py \
  --collection business_collection_qwen3_embedding_0_6b_d1024 \
  --search-mode hybrid \
  --search-limit 5 \
  --run-ragas \
  --ragas-output data/rag/eval/results/ragas_hybrid_top5.json
```

---

## 7) Export Collections

## 7.1 Export one collection to JSON

```bash
python scripts/rag/export_milvus.py \
  --collection technical_collection_qwen3_embedding_0_6b_d1024 \
  --output data/rag/exports/technical_0_6b.json \
  --format json
```

## 7.2 Full export with vectors

```bash
python scripts/rag/export_milvus.py \
  --collection technical_collection_qwen3_embedding_0_6b_d1024 \
  --output data/rag/exports/technical_0_6b_full.json \
  --format json \
  --include-vector
```

## 7.3 Export all collections

```bash
python scripts/rag/export_milvus.py \
  --all-collections \
  --output data/rag/exports/milvus_all.json \
  --format json
```

---

## 8) Import from Export File

`import_milvus.py` expects single-collection JSON export (`meta + data[]` format).

## 8.1 Import using source collection name from metadata

```bash
python scripts/rag/import_milvus.py \
  --input data/rag/exports/technical_0_6b_full.json \
  --uri http://127.0.0.1:19530
```

## 8.2 Import into a specific collection name

```bash
python scripts/rag/import_milvus.py \
  --input data/rag/exports/technical_0_6b_full.json \
  --collection technical_collection_qwen3_embedding_0_6b_d1024 \
  --uri http://127.0.0.1:19530
```

## 8.3 Recreate collection on dim mismatch

```bash
python scripts/rag/import_milvus.py \
  --input data/rag/exports/technical_0_6b_full.json \
  --recreate-if-dim-mismatch \
  --uri http://127.0.0.1:19530
```

---

## 9) Operational Checklist

Before indexing:

- Milvus is reachable at `MILVUS_URI`
- `RAG_RAW_materials` contains expected Markdown files
- embedding model is decided (`0.6B` for speed, `8B` for quality)

After indexing:

- run `inspect_milvus.py --collection ... --sample-limit 5`
- run one retrieval query (`dense` or `hybrid`)
- run evaluation script and save top1 review JSON

Before sharing database snapshot:

- export with `--include-vector` if the receiver should import without re-embedding
- provide collection name, model name, and dimension in your handoff note

---

## 10) Troubleshooting

## 10.1 Progress bar appears stuck at 0%

Common with large models (especially `Qwen3-Embedding-8B`): progress updates per batch completion, not per token.
Check GPU/CPU utilization before assuming a hang.

## 10.2 Milvus insert dim mismatch

Example: expected `384`, actual `4096`.

Fix options:

- use matching `EMBED_TRUNCATE_DIM`
- use a model with the expected dimension
- use `AUTO_RECREATE_COLLECTION=1` (indexing) or `--recreate-if-dim-mismatch` (import)

## 10.3 `git push` asks username/password and fails

This is unrelated to Milvus; switch Git remote to SSH (`git@github.com:...`) instead of HTTPS password auth.

## 10.4 Export pagination error on old pymilvus

Upgrade `pymilvus` so `MilvusClient.query(..., offset=...)` is available.

---

## 11) Reference Documents

- `Milvus_RAG_构建指南.md` (Chinese, setup background and deployment notes)
- `README.md` (project-level overview)

