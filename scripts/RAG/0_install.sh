#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="${NETWORK_NAME:-milvus}"
ETCD_CONTAINER="${ETCD_CONTAINER:-milvus-etcd}"
MINIO_CONTAINER="${MINIO_CONTAINER:-milvus-minio}"
MILVUS_CONTAINER="${MILVUS_CONTAINER:-milvus-standalone}"
MINIO_VOLUME="${MINIO_VOLUME:-milvus_minio_data}"

ETCD_IMAGE="${ETCD_IMAGE:-quay.io/coreos/etcd:v3.5.5}"
MINIO_IMAGE="${MINIO_IMAGE:-minio/minio:RELEASE.2023-03-20T20-16-18Z}"
MILVUS_IMAGE="${MILVUS_IMAGE:-milvusdb/milvus:v2.4.6}"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker command not found."
  echo "Please install Docker Desktop first:"
  echo "https://www.docker.com/products/docker-desktop/"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[ERROR] Docker daemon is not running."
  echo "Please start Docker Desktop, then retry."
  exit 1
fi

echo "[install] Creating Docker network '${NETWORK_NAME}'..."
docker network create "${NETWORK_NAME}" >/dev/null 2>&1 || true

echo "[install] Creating Docker volume '${MINIO_VOLUME}'..."
docker volume create "${MINIO_VOLUME}" >/dev/null

create_or_start_container() {
  local container_name="$1"
  local create_cmd="$2"

  if docker ps -a --format '{{.Names}}' | grep -Fxq "${container_name}"; then
    if docker ps --format '{{.Names}}' | grep -Fxq "${container_name}"; then
      echo "[install] Container already running: ${container_name}"
    else
      echo "[install] Starting existing container: ${container_name}"
      docker start "${container_name}" >/dev/null
    fi
  else
    echo "[install] Creating container: ${container_name}"
    eval "${create_cmd}" >/dev/null
  fi
}

create_or_start_container \
  "${ETCD_CONTAINER}" \
  "docker run -d --name ${ETCD_CONTAINER} --network ${NETWORK_NAME} ${ETCD_IMAGE} /usr/local/bin/etcd --advertise-client-urls=http://0.0.0.0:2379 --listen-client-urls=http://0.0.0.0:2379"

create_or_start_container \
  "${MINIO_CONTAINER}" \
  "docker run -d --name ${MINIO_CONTAINER} --network ${NETWORK_NAME} -p 9000:9000 -p 9001:9001 -e MINIO_ACCESS_KEY=minioadmin -e MINIO_SECRET_KEY=minioadmin -v ${MINIO_VOLUME}:/minio_data ${MINIO_IMAGE} server /minio_data --console-address ':9001'"

create_or_start_container \
  "${MILVUS_CONTAINER}" \
  "docker run -d --name ${MILVUS_CONTAINER} --network ${NETWORK_NAME} -p 19530:19530 -p 9091:9091 -e ETCD_ENDPOINTS=${ETCD_CONTAINER}:2379 -e MINIO_ADDRESS=${MINIO_CONTAINER}:9000 ${MILVUS_IMAGE} milvus run standalone"

echo "[install] Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install "pymilvus>=2.4.0" "sentence-transformers>=3.0.0"

echo
echo "[install] Milvus stack status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|${ETCD_CONTAINER}|${MINIO_CONTAINER}|${MILVUS_CONTAINER}" || true
echo
echo "[install] Done."
