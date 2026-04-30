#!/usr/bin/env bash
set -euo pipefail

# Start (or bootstrap) Milvus standalone stack for local RAG.
# - Reuse existing containers when present.
# - Create missing pieces on first run.

NETWORK_NAME="${NETWORK_NAME:-milvus}"
ETCD_CONTAINER="${ETCD_CONTAINER:-milvus-etcd}"
MINIO_CONTAINER="${MINIO_CONTAINER:-milvus-minio}"
MILVUS_CONTAINER="${MILVUS_CONTAINER:-milvus-standalone}"
MINIO_VOLUME="${MINIO_VOLUME:-milvus_minio_data}"

ETCD_IMAGE="${ETCD_IMAGE:-quay.io/coreos/etcd:v3.5.5}"
MINIO_IMAGE="${MINIO_IMAGE:-minio/minio:RELEASE.2023-03-20T20-16-18Z}"
MILVUS_IMAGE="${MILVUS_IMAGE:-milvusdb/milvus:v2.4.6}"

MUST_HAVE_CMDS=(docker)
for cmd in "${MUST_HAVE_CMDS[@]}"; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "[ERROR] Missing command: ${cmd}"
    exit 1
  fi
done

ensure_docker_daemon() {
  if docker info >/dev/null 2>&1; then
    return 0
  fi

  echo "[start-db] Docker daemon is not running, trying to start Docker Desktop..."

  # If running inside WSL, try launching Docker Desktop on Windows host.
  if grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
    powershell.exe -NoProfile -Command \
      "Start-Process -FilePath '\$(\$Env:ProgramFiles)\\Docker\\Docker\\Docker Desktop.exe'" \
      >/dev/null 2>&1 || true
  fi

  # Wait up to ~2 minutes for Docker daemon to become healthy.
  local wait_seconds=120
  local elapsed=0
  while (( elapsed < wait_seconds )); do
    if docker info >/dev/null 2>&1; then
      echo "[start-db] Docker daemon is ready."
      return 0
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done

  echo "[ERROR] Docker daemon is not running."
  echo "Please start Docker Desktop first, then retry."
  return 1
}

ensure_docker_daemon

echo "[start-db] Ensuring Docker network '${NETWORK_NAME}'..."
docker network create "${NETWORK_NAME}" >/dev/null 2>&1 || true

ensure_container_running() {
  local container_name="$1"
  local run_cmd="$2"

  if docker ps -a --format '{{.Names}}' | grep -Fxq "${container_name}"; then
    # Container exists; start if not running.
    if ! docker ps --format '{{.Names}}' | grep -Fxq "${container_name}"; then
      echo "[start-db] Starting existing container: ${container_name}"
      docker start "${container_name}" >/dev/null
    else
      echo "[start-db] Container already running: ${container_name}"
    fi
  else
    echo "[start-db] Creating container: ${container_name}"
    eval "${run_cmd}"
  fi
}

echo "[start-db] Ensuring volume '${MINIO_VOLUME}'..."
docker volume create "${MINIO_VOLUME}" >/dev/null 2>&1 || true

ensure_container_running \
  "${ETCD_CONTAINER}" \
  "docker run -d --name ${ETCD_CONTAINER} --network ${NETWORK_NAME} ${ETCD_IMAGE} /usr/local/bin/etcd --advertise-client-urls=http://0.0.0.0:2379 --listen-client-urls=http://0.0.0.0:2379 >/dev/null"

ensure_container_running \
  "${MINIO_CONTAINER}" \
  "docker run -d --name ${MINIO_CONTAINER} --network ${NETWORK_NAME} -p 9000:9000 -p 9001:9001 -e MINIO_ACCESS_KEY=minioadmin -e MINIO_SECRET_KEY=minioadmin -v ${MINIO_VOLUME}:/minio_data ${MINIO_IMAGE} server /minio_data --console-address ':9001' >/dev/null"

ensure_container_running \
  "${MILVUS_CONTAINER}" \
  "docker run -d --name ${MILVUS_CONTAINER} --network ${NETWORK_NAME} -p 19530:19530 -p 9091:9091 -e ETCD_ENDPOINTS=${ETCD_CONTAINER}:2379 -e MINIO_ADDRESS=${MINIO_CONTAINER}:9000 ${MILVUS_IMAGE} milvus run standalone >/dev/null"

echo
echo "[start-db] Current Milvus stack status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|${ETCD_CONTAINER}|${MINIO_CONTAINER}|${MILVUS_CONTAINER}" || true
echo
echo "[start-db] Done. Expected Milvus endpoint: http://127.0.0.1:19530"
