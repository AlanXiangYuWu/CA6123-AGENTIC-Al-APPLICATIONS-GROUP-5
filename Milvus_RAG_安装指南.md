# Milvus RAG 构建指南

## 0. 先理解 3 种操作（避免冲突）

你只需要记住这三种，不要混用：

1. **首次部署（create）**：机器上第一次搭 Milvus，执行 `docker run ... --name ...`
2. **日常启动（start）**：重启电脑后继续用，执行 `docker start ...`，**不要再 run**
3. **重建环境（recreate）**：删旧容器后重新 `docker run`


---

## 1. 环境准备（Windows + WSL）

## 1.1 安装 Docker

Windows下载并安装 Docker Desktop：  
   [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

验证

```bash
docker --version
docker run --rm hello-world
```

---

## 2. 首次部署 Milvus

## 2.1 创建网络

```bash
docker network create milvus 2>/dev/null || true
```

## 2.2 启动 etcd

```bash
docker run -d --name milvus-etcd --network milvus \
  quay.io/coreos/etcd:v3.5.5 \
  /usr/local/bin/etcd \
  --advertise-client-urls=http://0.0.0.0:2379 \
  --listen-client-urls=http://0.0.0.0:2379
```

## 2.3 启动 MinIO（带持久化 volume）

```bash
docker volume create milvus_minio_data

docker run -d --name milvus-minio --network milvus \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  -v milvus_minio_data:/minio_data \
  minio/minio:RELEASE.2023-03-20T20-16-18Z \
  server /minio_data --console-address ":9001"
```

## 2.4 启动 Milvus Standalone

```bash
docker run -d --name milvus-standalone --network milvus \
  -p 19530:19530 -p 9091:9091 \
  -e ETCD_ENDPOINTS=milvus-etcd:2379 \
  -e MINIO_ADDRESS=milvus-minio:9000 \
  milvusdb/milvus:v2.4.6 milvus run standalone
```

## 2.5 启动验证

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker logs -f milvus-standalone
```

日志出现 `Proxy successfully started` 可用。

---

## 3. 重启服务器后怎么再启动（日常使用）

只需执行：

```bash
docker start milvus-etcd milvus-minio milvus-standalone
docker ps
```

---

## 4. 需要重建时（彻底清理后重装）

当容器损坏、配置改错、或你想重来一遍时：

```bash
docker rm -f milvus-standalone milvus-minio milvus-etcd
docker network rm milvus 2>/dev/null || true
```

然后回到本文 `第 2 节` 重新首次部署。

---

## 5. Python 依赖安装

```bash
pip install "pymilvus>=2.4.0" "sentence-transformers>=3.0.0"
```

（可选）沿用你项目里的 Gemini：

```bash
pip install "langchain-google-genai>=2.0.0"
```

## 6. Docker 常用操作

#### 查看全部容器状态

```bash
docker ps -a
```

#### 查看 Milvus 日志

```bash
docker logs -f milvus-standalone
```

#### 停止容器

```bash
docker stop milvus-standalone milvus-etcd milvus-minio
```

#### 启动已有容器

```bash
docker start milvus-etcd milvus-minio milvus-standalone
```

#### 删除容器（重建环境时）

```bash
docker rm -f milvus-standalone milvus-etcd milvus-minio
```

#### 删除网络

```bash
docker network rm milvus
```

---