# Milvus RAG 构建指南（WSL 版本，按正确顺序）

本文档是**去重 + 去冲突**后的版本，只保留可执行主流程。  
目标流程：

`RAG_RAW_materials/*.md -> 读取 Markdown -> 切分 chunk -> 生成 embedding -> 写入 Milvus -> business_collection / technical_collection`

---

## 0. 先理解 3 种操作（避免冲突）

你只需要记住这三种，不要混用：

1. **首次部署（create）**：机器上第一次搭 Milvus，执行 `docker run ... --name ...`
2. **日常启动（start）**：重启电脑后继续用，执行 `docker start ...`，**不要再 run**
3. **重建环境（recreate）**：删旧容器后重新 `docker run`

你之前遇到的报错（容器名冲突）就是把第 1 种和第 2 种混用了。

---

## 1. 环境准备（Windows + WSL）

## 1.1 安装 Docker Desktop（Windows）

1. 下载并安装 Docker Desktop：  
   [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. 启动 Docker Desktop，确认状态为 `Engine running`
3. 打开 `Settings -> Resources -> WSL Integration`
4. 勾选你使用的发行版（例如 Ubuntu）

## 1.2 在 WSL 里验证

在 WSL（Ubuntu）终端执行：

```bash
docker --version
docker run --rm hello-world
```

若 `hello-world` 正常输出，说明环境可用。

---

## 2. 首次部署 Milvus（只执行一次）

> 仅当你机器上还没有 `milvus-etcd / milvus-minio / milvus-standalone` 这三个容器时执行。

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

日志出现 `Proxy successfully started` 基本可用。

---

## 3. 重启电脑后怎么再启动（日常使用）

只需执行：

```bash
docker start milvus-etcd milvus-minio milvus-standalone
docker ps
```

**不要执行 `docker run --name milvus-minio ...` 这类首次创建命令**，否则会冲突。

---

## 4. 需要重建时（彻底清理后重装）

当容器损坏、配置改错、或你想重来一遍时：

```bash
docker rm -f milvus-standalone milvus-minio milvus-etcd
docker network rm milvus 2>/dev/null || true
```

然后回到本文 `第 2 节` 重新首次部署。

---

## 5. 常见错误与正确处理

## 5.1 容器名冲突

报错示例：

`The container name "/milvus-minio" is already in use`

原因：同名容器已存在，你又执行了 `docker run --name milvus-minio ...`

处理：

- 日常使用：`docker start milvus-minio`
- 重建：`docker rm -f milvus-minio` 后再 `docker run ...`

## 5.2 WSL 下 `-e: command not found`

原因：用了 PowerShell 续行符 `` ` ``。  
WSL/bash 必须用 `\`。

---

## 6. RAG 数据目录约定

```text
RAG_RAW_materials/
├── business/
│   ├── market_report_001.md
│   └── prd_template_001.md
└── technical/
    ├── fastapi_notes_001.md
    └── langgraph_notes_001.md
```

分流规则：

- `business/` -> 写入 `business_collection`
- `technical/` -> 写入 `technical_collection`

---

## 7. Python 依赖安装

```bash
pip install "pymilvus>=2.4.0" "sentence-transformers>=3.0.0"
```

（可选）沿用你项目里的 Gemini：

```bash
pip install "langchain-google-genai>=2.0.0"
```

---

## 8. 索引脚本（Markdown -> Chunk -> Embedding -> Milvus）

建议新建：`scripts/index_milvus.py`

```python
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable

from pymilvus import MilvusClient, DataType
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "RAG_RAW_materials"
MILVUS_URI = "http://127.0.0.1:19530"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

BUSINESS_COLLECTION = "business_collection"
TECHNICAL_COLLECTION = "technical_collection"


def iter_markdown_files() -> Iterable[Path]:
    yield from RAW_DIR.rglob("*.md")


def infer_kb_type(path: Path) -> str:
    s = str(path).replace("\\", "/").lower()
    if "/business/" in s:
        return "business"
    if "/technical/" in s:
        return "technical"
    raise ValueError(f"Cannot infer kb type from path: {path}")


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


def main() -> None:
    client = MilvusClient(uri=MILVUS_URI)
    embedder = SentenceTransformer(EMBED_MODEL)
    dim = embedder.get_sentence_embedding_dimension()

    ensure_collection(client, BUSINESS_COLLECTION, dim)
    ensure_collection(client, TECHNICAL_COLLECTION, dim)

    business_rows = []
    technical_rows = []

    for md_path in iter_markdown_files():
        kb_type = infer_kb_type(md_path)
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        chunks = split_text(text)
        if not chunks:
            continue
        vectors = embedder.encode(chunks, normalize_embeddings=True).tolist()
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
            business_rows.extend(rows)
        else:
            technical_rows.extend(rows)

    if business_rows:
        client.insert(collection_name=BUSINESS_COLLECTION, data=business_rows)
    if technical_rows:
        client.insert(collection_name=TECHNICAL_COLLECTION, data=technical_rows)

    client.flush(collection_name=BUSINESS_COLLECTION)
    client.flush(collection_name=TECHNICAL_COLLECTION)

    print(f"business inserted: {len(business_rows)}")
    print(f"technical inserted: {len(technical_rows)}")


if __name__ == "__main__":
    main()
```

---

## 9. 执行顺序（一次看懂）

1. 按 `第 1 节` 配好 Docker Desktop + WSL  
2. 按 `第 2 节` 首次部署 Milvus（只做一次）  
3. 准备 `RAG_RAW_materials/business` 与 `technical` Markdown  
4. 安装 Python 依赖  
5. 运行：

```bash
python scripts/index_milvus.py
```

6. 检索验证：

```python
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

client = MilvusClient(uri="http://127.0.0.1:19530")
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
qv = embedder.encode(["product requirement for student job app"], normalize_embeddings=True).tolist()[0]
res = client.search(
    collection_name="business_collection",
    data=[qv],
    output_fields=["text", "doc_id", "source_path"],
    limit=3,
)
print(res)
```

---

## 10. 接入你当前项目（Chroma -> Milvus）

你当前 `backend/rag/kb.py` 是 Chroma。迁移建议：

1. 新增 `backend/rag/kb_milvus.py`
2. 对外接口保持一致：`retrieve(query, agent, k=3)`
3. 配置增加：
   - `MILVUS_URI`
   - `BUSINESS_COLLECTION`
   - `TECHNICAL_COLLECTION`
   - `EMBEDDING_MODEL`
4. 在 `get_kb()` 切换到 Milvus 实现

这样可以不改 `Research/Architect/QA` 的调用代码。

# Milvus 双库 RAG 构建指南（Markdown -> Chunk -> Embedding -> Milvus）

本文档按以下目标流程编写，并提供可执行步骤：

`RAG_RAW_materials/*.md -> 读取 Markdown -> 切分 chunk -> 生成 embedding -> 写入 Milvus -> 建立 business_collection / technical_collection`

---

## 1. 目录约定

建议在项目根目录采用如下结构：

```text
CA6123-AGENTIC-Al-APPLICATIONS-GROUP-5/
├── RAG_RAW_materials/
│   ├── business/
│   │   ├── market_report_001.md
│   │   └── prd_template_001.md
│   └── technical/
│       ├── fastapi_notes_001.md
│       └── langgraph_notes_001.md
├── scripts/
│   └── index_milvus.py
└── Milvus_RAG_构建指南.md
```

说明：

- `business/` 放业务知识（市场、竞品、PRD 模板、商业模型等）
- `technical/` 放技术知识（框架文档、架构模式、安全实践等）
- 也可把全部文件放在 `RAG_RAW_materials/` 根目录，然后通过文件名规则分流（不推荐，易混淆）

---

## 2. Milvus 安装步骤

以下给两种常见方式：Docker（推荐）与 Zilliz Cloud（托管版）。

## 2.0 Docker 安装（WSL 版本）

本文档默认你在 **Windows + WSL(Ubuntu)** 中执行命令。

### 2.0.1 Windows 侧安装 Docker Desktop

1. 下载并安装 Docker Desktop：  
   [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. 启动 Docker Desktop，确认状态为 `Engine running`
3. 打开 `Settings -> Resources -> WSL Integration`
4. 勾选你正在使用的 WSL 发行版（如 Ubuntu）

### 2.0.2 WSL 内自检（在 Ubuntu 终端执行）

```bash
docker --version
docker run --rm hello-world
```

如果 `hello-world` 能正常输出欢迎信息，说明 Docker 可用。

## 2.0.3 为什么 WSL 场景推荐 Docker Desktop 集成

Milvus 本身依赖多个组件，直接在本机裸装通常会遇到依赖版本和环境配置问题。  
使用 Docker 可以把运行环境与依赖统一封装，部署成本更低，团队协作也更稳定。

Docker 方案优势：

- **部署快**：拉镜像后即可启动
- **隔离好**：不污染本机系统环境
- **可复现**：组员机器上更容易保持一致
- **易维护**：重启、清理、重建简单

推荐场景：

- 课程项目开发与演示
- 多人协作统一环境
- 需要频繁重建或切换实验环境

## 2.1 本地 Docker 启动 Milvus（推荐开发环境）

前置条件：

- 已安装 Docker Desktop
- 机器可正常拉取镜像

### 步骤 A：拉取并运行 Milvus Standalone

可使用官方 `milvus-standalone`（包含 etcd/minio 依赖容器）方式。  
如果你已有官方 compose 文件，直接启动即可。

示例（WSL/bash）：

```bash
docker network create milvus 2>/dev/null || true

docker run -d --name milvus-etcd --network milvus \
  quay.io/coreos/etcd:v3.5.5 \
  /usr/local/bin/etcd \
  --advertise-client-urls=http://0.0.0.0:2379 \
  --listen-client-urls=http://0.0.0.0:2379

docker run -d --name milvus-minio --network milvus -p 9000:9000 -p 9001:9001 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  minio/minio:RELEASE.2023-03-20T20-16-18Z \
  server /minio_data --console-address ":9001"

docker run -d --name milvus-standalone --network milvus -p 19530:19530 -p 9091:9091 \
  -e ETCD_ENDPOINTS=milvus-etcd:2379 \
  -e MINIO_ADDRESS=milvus-minio:9000 \
  milvusdb/milvus:v2.4.6 milvus run standalone
```

> 如果你偏好一键方式，可用官方 `docker-compose.yml` 启动 standalone。


启动命令
docker start milvus-etcd milvus-minio milvus-standalone
docker ps
docker logs -f milvus-standalone


### 步骤 B：检查服务是否正常

```bash
docker ps
```

确认以下端口可用：

- `19530`：Milvus gRPC
- `9091`：健康/监控端口（版本可能不同）

### 步骤 C：Docker 常用操作

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

#### 删除网络（可选）

```bash
docker network rm milvus
```

### 步骤 D：数据持久化（建议）

如果不挂载 volume，删除容器后数据可能丢失。  
建议至少给 MinIO 增加数据卷挂载。

示例（MinIO 挂载 volume）：

```bash
docker volume create milvus_minio_data

docker run -d --name milvus-minio --network milvus -p 9000:9000 -p 9001:9001 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  -v milvus_minio_data:/minio_data \
  minio/minio:RELEASE.2023-03-20T20-16-18Z \
  server /minio_data --console-address ":9001"
```

团队实践建议：

- 在仓库中维护统一 `docker-compose.yml`
- 固定镜像版本，避免“同命令不同结果”

---

## 2.2 使用 Zilliz Cloud（生产/团队协作推荐）

1. 注册并创建集群  
2. 获取 `URI`、`TOKEN`（或用户名密码）  
3. Python 连接时改用云端 URI

优点：

- 不需要本地维护 Milvus 依赖
- 高可用与监控更完整

---

## 3. Python 依赖安装

在项目虚拟环境中安装：

```bash
pip install pymilvus>=2.4.0 sentence-transformers>=3.0.0 markdown-it-py>=3.0.0
```

可选（若你想沿用当前项目 Gemini）：

```bash
pip install langchain-google-genai>=2.0.0
```

---

## 4. 数据处理流程设计

## 4.1 读取 Markdown

目标：读取 `RAG_RAW_materials/**/*.md`，提取纯文本并保留元数据。

建议元数据：

- `source_path`
- `kb_type`（business / technical）
- `doc_id`
- `title`（可从首行 `#` 提取）

## 4.2 切分 Chunk

推荐参数（中文英文混合文档可用）：

- `chunk_size = 800`（字符）
- `chunk_overlap = 120`

切分原则：

- 优先按标题段落切，再做长度切分
- 避免将代码块/表格硬截断在中间

## 4.3 生成 Embedding

常见选择：

- 本地开源：`sentence-transformers/all-MiniLM-L6-v2`（384 维）
- 云端模型：Gemini/OpenAI 等（维度随模型变化）

**关键点：同一个 collection 必须使用同维度向量。**

## 4.4 写入 Milvus

每条 chunk 作为一条向量记录写入，通常字段包括：

- `id`（主键，建议字符串 UUID）
- `vector`（FLOAT_VECTOR）
- `text`（原文 chunk）
- `source_path`
- `doc_id`
- `kb_type`

## 4.5 双 Collection

- `business_collection`
- `technical_collection`

分库策略：

- 来源目录在 `RAG_RAW_materials/business/` -> `business_collection`
- 来源目录在 `RAG_RAW_materials/technical/` -> `technical_collection`

---

## 5. 参考实现脚本（`scripts/index_milvus.py`）

下面是一个可直接改造的示例（最小可用版）：

```python
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable

from pymilvus import (
    MilvusClient,
    DataType,
)
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "RAG_RAW_materials"
MILVUS_URI = "http://127.0.0.1:19530"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

BUSINESS_COLLECTION = "business_collection"
TECHNICAL_COLLECTION = "technical_collection"


def iter_markdown_files() -> Iterable[Path]:
    yield from RAW_DIR.rglob("*.md")


def infer_kb_type(path: Path) -> str:
    s = str(path).replace("\\", "/").lower()
    if "/business/" in s:
        return "business"
    if "/technical/" in s:
        return "technical"
    raise ValueError(f"Cannot infer kb type from path: {path}")


def split_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start += step
    return chunks


def ensure_collection(client: MilvusClient, name: str, dim: int) -> None:
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


def main() -> None:
    client = MilvusClient(uri=MILVUS_URI)
    embedder = SentenceTransformer(EMBED_MODEL)
    dim = embedder.get_sentence_embedding_dimension()

    ensure_collection(client, BUSINESS_COLLECTION, dim)
    ensure_collection(client, TECHNICAL_COLLECTION, dim)

    business_rows = []
    technical_rows = []

    for md_path in iter_markdown_files():
        kb_type = infer_kb_type(md_path)
        raw_text = md_path.read_text(encoding="utf-8", errors="ignore")
        chunks = split_text(raw_text)
        if not chunks:
            continue

        vectors = embedder.encode(chunks, normalize_embeddings=True).tolist()
        doc_id = md_path.stem
        rows = []
        for chunk, vec in zip(chunks, vectors):
            rows.append(
                {
                    "id": uuid.uuid4().hex,
                    "vector": vec,
                    "text": chunk,
                    "source_path": str(md_path),
                    "doc_id": doc_id,
                    "kb_type": kb_type,
                }
            )

        if kb_type == "business":
            business_rows.extend(rows)
        else:
            technical_rows.extend(rows)

    if business_rows:
        client.insert(collection_name=BUSINESS_COLLECTION, data=business_rows)
    if technical_rows:
        client.insert(collection_name=TECHNICAL_COLLECTION, data=technical_rows)

    client.flush(collection_name=BUSINESS_COLLECTION)
    client.flush(collection_name=TECHNICAL_COLLECTION)

    print(f"business inserted: {len(business_rows)}")
    print(f"technical inserted: {len(technical_rows)}")


if __name__ == "__main__":
    main()
```

---

## 6. 运行步骤（端到端）

1. 准备 Markdown 原始资料到 `RAG_RAW_materials/business` 和 `RAG_RAW_materials/technical`
2. 启动 Milvus（本地 Docker 或云端）
3. 安装依赖（`pymilvus`, `sentence-transformers` 等）
4. 新建并运行 `scripts/index_milvus.py`

```bash
python scripts/index_milvus.py
```

5. 观察输出条数，确认双 collection 都写入成功

---

## 7. 检索验证示例

你可以用下面示例快速验证：

```python
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

client = MilvusClient(uri="http://127.0.0.1:19530")
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

q = "How to design a PRD and validate user pain points?"
qv = embedder.encode([q], normalize_embeddings=True).tolist()[0]

res = client.search(
    collection_name="business_collection",
    data=[qv],
    output_fields=["text", "doc_id", "source_path"],
    limit=3,
)
print(res)
```

---

## 8. 接入当前项目的建议改造

当前项目 `backend/rag/kb.py` 使用的是 ChromaDB。若切换到 Milvus：

1. 新增 Milvus 版 KB 实现（如 `backend/rag/kb_milvus.py`）
2. 保持对外接口不变：`retrieve(query, agent, k=3)`
3. 在配置中增加：
   - `MILVUS_URI`
   - `BUSINESS_COLLECTION`
   - `TECHNICAL_COLLECTION`
   - `EMBEDDING_MODEL`
4. 将 `get_kb()` 指向 Milvus 版实现

这样可以避免影响 `Research/Architect/QA` agent 现有调用代码。

---

## 9. 常见问题（FAQ）

### Q1: `collection vector dim mismatch`

原因：索引时和检索时 embedding 维度不一致。  
解决：固定同一个 embedding 模型，或重建 collection。

### Q2: 中文检索结果不准确

可尝试：

- 使用更适合中文的 embedding 模型
- 减小 chunk 大小到 500~700
- 增加 overlap 到 120~180
- 在 metadata 加标题、领域标签并做过滤

### Q3: 插入报 `max_length` 超限

`VARCHAR` 字段长度不足。  
解决：调大 `text/source_path` 的 `max_length`，或缩短 chunk。

### Q4: Docker 启动后连接失败

排查顺序：

1. `docker ps` 确认容器在运行
2. 检查 `19530` 端口映射
3. 检查防火墙/代理
4. 确认 URI 使用 `http://127.0.0.1:19530`

---

## 10. 推荐下一步

- 增加 `metadata` 字段：`title`, `section`, `language`, `source_url`
- 建立增量索引机制（按文件 hash 更新）
- 增加离线评估脚本（检索召回率、top-k 命中率）
- 与你现有 Agent 流水线打通：按角色路由到 business/technical collection

