from __future__ import annotations

import gc
import json
import os
import re
import uuid
from pathlib import Path
from typing import Iterable

from pymilvus import MilvusClient, DataType
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm

try:
    import torch
except Exception:  # pragma: no cover
    torch = None

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "RAG_RAW_materials"
MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
# Qwen3 embedding models:
# - Qwen/Qwen3-Embedding-0.6B (1024 dim, best for local)
# - Qwen/Qwen3-Embedding-4B   (2560 dim)
# - Qwen/Qwen3-Embedding-8B   (4096 dim)
EMBED_MODEL = os.getenv("EMBED_MODEL", "Qwen/Qwen3-Embedding-8B")
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "4"))
# Optional Matryoshka truncation dimension (Qwen3 supports custom output dims).
# Set to 0 to disable, e.g. EMBED_TRUNCATE_DIM=768
EMBED_TRUNCATE_DIM = int(os.getenv("EMBED_TRUNCATE_DIM", "0"))
CHECKPOINT_PATH = ROOT / ".rag_index_checkpoint.json"
FORCE_RESTART = os.getenv("FORCE_RESTART", "0") == "1"
AUTO_RECREATE_COLLECTION = os.getenv("AUTO_RECREATE_COLLECTION", "0") == "1"
COLLECTION_SUFFIX = os.getenv("COLLECTION_SUFFIX", "").strip()
# Index subset: all | business | technical (default: all).
INDEX_KB = os.getenv("INDEX_KB", "all").strip().lower()

BUSINESS_COLLECTION = "business_collection"
TECHNICAL_COLLECTION = "technical_collection"
EXCLUDED_FILES = {
    (RAW_DIR / "business_kb" / "README.md").resolve(),
    (RAW_DIR / "technical_kb" / "README.md").resolve()
}


def iter_markdown_files() -> Iterable[Path]:
    for path in RAW_DIR.rglob("*.md"):
        if path.resolve() in EXCLUDED_FILES:
            continue
        yield path


def infer_kb_type(path: Path) -> str:
    s = str(path).replace("\\", "/").lower()
    if any(token in s for token in ("/business/", "/business_kb/", "/biz/")):
        return "business"
    if any(token in s for token in ("/technical/", "/technical_kb/", "/tech/")):
        return "technical"
    raise ValueError(
        "Cannot infer kb type from path: "
        f"{path}. Expected folder names like business/business_kb or "
        "technical/technical_kb."
    )


def filter_md_by_index_kb(paths: list[Path]) -> list[Path]:
    if INDEX_KB in ("", "all"):
        return paths
    if INDEX_KB == "business":
        return [p for p in paths if infer_kb_type(p) == "business"]
    if INDEX_KB == "technical":
        return [p for p in paths if infer_kb_type(p) == "technical"]
    raise ValueError(
        f"Invalid INDEX_KB={INDEX_KB!r}. Use all, business, or technical."
    )


def split_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    i = 0
    while i < len(text):
        chunks.append(text[i : i + chunk_size])
        i += step
    return chunks


def ensure_collection(client: MilvusClient, name: str, dim: int) -> None:
    if client.has_collection(name):
        info = client.describe_collection(collection_name=name)
        existing_dim = _extract_vector_dim(info)
        if existing_dim is None:
            raise RuntimeError(
                f"Collection {name} exists but vector dim cannot be inferred. "
                "Please inspect schema manually."
            )
        if existing_dim != dim:
            if not AUTO_RECREATE_COLLECTION:
                raise RuntimeError(
                    f"Collection {name} dim mismatch: existing={existing_dim}, new={dim}. "
                    "Use one of: "
                    "1) set EMBED_TRUNCATE_DIM to match existing dim, "
                    "2) switch to model output with same dim, "
                    "3) set AUTO_RECREATE_COLLECTION=1 to drop and recreate collection."
                )
            print(
                f"Collection {name} dim mismatch: existing={existing_dim}, new={dim}. "
                "AUTO_RECREATE_COLLECTION=1 -> dropping and recreating."
            )
            client.drop_collection(collection_name=name)
        else:
            return
    if client.has_collection(name):
        return
    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=64)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field("text", DataType.VARCHAR, max_length=65535)
    schema.add_field("source_path", DataType.VARCHAR, max_length=1024)
    schema.add_field("doc_id", DataType.VARCHAR, max_length=128)
    schema.add_field("kb_type", DataType.VARCHAR, max_length=32)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )
    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
    )
    print(f"Collection ready: {name}, dim={dim}")


def sanitize_name_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned.lower() or "default"


def build_run_tag(dim: int) -> str:
    model_tag = EMBED_MODEL.split("/")[-1]
    model_tag = sanitize_name_part(model_tag)
    if COLLECTION_SUFFIX:
        suffix = sanitize_name_part(COLLECTION_SUFFIX)
        return f"{model_tag}_{suffix}_d{dim}"
    return f"{model_tag}_d{dim}"


def resolve_collection_names(dim: int) -> tuple[str, str]:
    tag = build_run_tag(dim)
    return f"{BUSINESS_COLLECTION}_{tag}", f"{TECHNICAL_COLLECTION}_{tag}"


def resolve_checkpoint_path(dim: int) -> Path:
    tag = build_run_tag(dim)
    return ROOT / f".rag_index_checkpoint_{tag}.json"


def _extract_vector_dim(collection_info: dict) -> int | None:
    schema = collection_info.get("schema") if isinstance(collection_info, dict) else None
    if isinstance(schema, dict):
        fields = schema.get("fields", [])
        for field in fields:
            if field.get("name") != "vector":
                continue
            dim = field.get("params", {}).get("dim")
            if dim is None:
                dim = field.get("dim")
            if dim is not None:
                return int(dim)
    # Fallback for alternative describe format
    fields = collection_info.get("fields", []) if isinstance(collection_info, dict) else []
    for field in fields:
        if field.get("name") != "vector":
            continue
        dim = field.get("params", {}).get("dim")
        if dim is None:
            dim = field.get("dim")
        if dim is not None:
            return int(dim)
    return None


def load_checkpoint(total_files: int, checkpoint_path: Path) -> dict:
    if FORCE_RESTART and checkpoint_path.exists():
        checkpoint_path.unlink()
        print(f"FORCE_RESTART=1, removed checkpoint: {checkpoint_path}")
    if not checkpoint_path.exists():
        return {
            "completed_files": [],
            "business_files": 0,
            "technical_files": 0,
            "total_chunks": 0,
            "skipped_empty": 0,
            "total_files": total_files,
            "embed_model": EMBED_MODEL,
            "truncate_dim": EMBED_TRUNCATE_DIM,
        }
    try:
        state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        state.setdefault("completed_files", [])
        state.setdefault("business_files", 0)
        state.setdefault("technical_files", 0)
        state.setdefault("total_chunks", 0)
        state.setdefault("skipped_empty", 0)
        state["total_files"] = total_files
        if (
            state.get("embed_model") != EMBED_MODEL
            or state.get("truncate_dim") != EMBED_TRUNCATE_DIM
        ):
            print(
                "Checkpoint model settings differ from current env, "
                "starting fresh run state."
            )
            return {
                "completed_files": [],
                "business_files": 0,
                "technical_files": 0,
                "total_chunks": 0,
                "skipped_empty": 0,
                "total_files": total_files,
                "embed_model": EMBED_MODEL,
                "truncate_dim": EMBED_TRUNCATE_DIM,
            }
        return state
    except Exception:
        print(f"Failed to parse checkpoint, recreate: {checkpoint_path}")
        return {
            "completed_files": [],
            "business_files": 0,
            "technical_files": 0,
            "total_chunks": 0,
            "skipped_empty": 0,
            "total_files": total_files,
            "embed_model": EMBED_MODEL,
            "truncate_dim": EMBED_TRUNCATE_DIM,
        }


def save_checkpoint(state: dict, checkpoint_path: Path) -> None:
    state["embed_model"] = EMBED_MODEL
    state["truncate_dim"] = EMBED_TRUNCATE_DIM
    checkpoint_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def clear_cuda_cache() -> None:
    if torch is None:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def encode_chunks_with_progress(
    embedder: SentenceTransformer,
    chunks: list[str],
    batch_size: int,
    truncate_dim: int,
    file_label: str,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    encode_kwargs = {
        "normalize_embeddings": True,
        "show_progress_bar": False,
    }
    if truncate_dim > 0:
        encode_kwargs["truncate_dim"] = truncate_dim

    chunk_bar = tqdm(
        total=len(chunks),
        desc=f"chunks {file_label}",
        unit="chunk",
        leave=False,
        dynamic_ncols=True,
    )
    for start in range(0, len(chunks), batch_size):
        end = min(start + batch_size, len(chunks))
        batch_chunks = chunks[start:end]
        with torch.inference_mode() if torch is not None else _nullcontext():
            batch_vec = embedder.encode(batch_chunks, **encode_kwargs).tolist()
        vectors.extend(batch_vec)
        chunk_bar.update(len(batch_chunks))
        chunk_bar.set_postfix_str(f"batch={len(batch_chunks)}")
    chunk_bar.close()
    return vectors


class _nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def main() -> None:
    client = MilvusClient(uri=MILVUS_URI)
    embedder = SentenceTransformer(EMBED_MODEL)
    print(f"Using embedding model: {EMBED_MODEL}")
    print(f"INDEX_KB={INDEX_KB} (subset of markdown files to index)")
    if EMBED_TRUNCATE_DIM > 0:
        print(f"Using truncate dim: {EMBED_TRUNCATE_DIM}")

    # Determine runtime output dim by probing one sample. This is important when
    # using Qwen3 with truncate_dim (MRL), because output dim can differ from
    # model's default embedding dimension.
    probe_kwargs = {"normalize_embeddings": True}
    if EMBED_TRUNCATE_DIM > 0:
        probe_kwargs["truncate_dim"] = EMBED_TRUNCATE_DIM
    probe_vec = embedder.encode(["dimension probe"], **probe_kwargs)
    dim = len(probe_vec[0])
    business_collection_name, technical_collection_name = resolve_collection_names(dim)
    checkpoint_path = resolve_checkpoint_path(dim)

    ensure_collection(client, business_collection_name, dim)
    ensure_collection(client, technical_collection_name, dim)

    all_md = list(iter_markdown_files())
    md_files = filter_md_by_index_kb(all_md)
    total_files = len(md_files)
    if total_files == 0:
        print(
            f"No markdown files to index under: {RAW_DIR} "
            f"(INDEX_KB={INDEX_KB}, scanned={len(all_md)} md files)."
        )
        return

    state = load_checkpoint(total_files=total_files, checkpoint_path=checkpoint_path)
    completed_files = set(state.get("completed_files", []))
    pending_files = [p for p in md_files if str(p) not in completed_files]

    print(
        f"Found {total_files} markdown files. "
        f"completed={len(completed_files)}, pending={len(pending_files)}"
    )
    print(f"Business collection: {business_collection_name}")
    print(f"Technical collection: {technical_collection_name}")
    print(f"Checkpoint file: {checkpoint_path}")

    file_bar = tqdm(
        total=len(pending_files),
        desc="files",
        unit="file",
        dynamic_ncols=True,
    )

    for md_path in pending_files:
        kb_type = infer_kb_type(md_path)
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        chunks = split_text(text)
        if not chunks:
            state["skipped_empty"] = int(state.get("skipped_empty", 0)) + 1
            state["completed_files"].append(str(md_path))
            save_checkpoint(state, checkpoint_path)
            file_bar.update(1)
            file_bar.set_postfix_str("skip empty")
            continue

        file_bar.set_postfix_str(
            f"{kb_type} {md_path.name} chunks={len(chunks)}"
        )
        vectors = encode_chunks_with_progress(
            embedder=embedder,
            chunks=chunks,
            batch_size=EMBED_BATCH_SIZE,
            truncate_dim=EMBED_TRUNCATE_DIM,
            file_label=md_path.name,
        )
        doc_id = md_path.stem
        rows = [
            {
                "id": uuid.uuid4().hex,
                "vector": vec,
                "text": chunk,
                "source_path": str(md_path),
                "doc_id": doc_id,
                "kb_type": kb_type,
            }
            for chunk, vec in zip(chunks, vectors)
        ]
        if kb_type == "business":
            client.insert(collection_name=business_collection_name, data=rows)
            state["business_files"] = int(state.get("business_files", 0)) + 1
            client.flush(collection_name=business_collection_name)
        else:
            client.insert(collection_name=technical_collection_name, data=rows)
            state["technical_files"] = int(state.get("technical_files", 0)) + 1
            client.flush(collection_name=technical_collection_name)
        state["total_chunks"] = int(state.get("total_chunks", 0)) + len(chunks)
        state["completed_files"].append(str(md_path))
        save_checkpoint(state, checkpoint_path)

        del text, chunks, vectors, rows
        gc.collect()
        clear_cuda_cache()
        file_bar.update(1)

    file_bar.close()

    print(
        "Indexing complete. "
        f"business_files={state.get('business_files', 0)}, "
        f"technical_files={state.get('technical_files', 0)}, "
        f"total_chunks={state.get('total_chunks', 0)}, "
        f"skipped_empty={state.get('skipped_empty', 0)}, "
        f"completed={len(state.get('completed_files', []))}/{total_files}"
    )
    print(f"Checkpoint saved at: {checkpoint_path}")


if __name__ == "__main__":
    main()