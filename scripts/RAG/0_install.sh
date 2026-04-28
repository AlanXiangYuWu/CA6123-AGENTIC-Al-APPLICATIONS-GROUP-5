#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install "pymilvus>=2.4.0" "sentence-transformers>=3.0.0" "tqdm>=4.0.0"

echo "RAG runtime dependencies installed."
