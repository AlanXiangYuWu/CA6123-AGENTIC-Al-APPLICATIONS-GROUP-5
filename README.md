# CA6123 Agentic AI Applications — Group 5

> NTU MCAAI（CA6123）课程小组作业仓库
>
> **Repo**: https://github.com/AlanXiangYuWu/CA6123-AGENTIC-Al-APPLICATIONS-GROUP-5

## 作业简介

设计并实现一个 **Agentic AI 应用**，能自主完成多步骤、目标导向的任务（不是单轮问答），清晰展示四阶段循环：

**Perceive → Reason → Action → Learn**

完整作业要求 / 选题讨论详见 [项目规划/](项目规划/) 目录：
- [CA6123 Group Project.md](项目规划/CA6123%20Group%20Project.md) — 作业核心要求 + 8 个 Bonus 方向 + 选题库
- [CA6123_Assignment详解.md](项目规划/CA6123_Assignment详解.md) — 作业细节解读
- [CA6123 项目规划（draft.md](项目规划/CA6123%20项目规划（draft.md) — 我们的内部技术规划

## 团队成员 · Team

| 成员 (按姓名拉丁字母排序) | 主要职责 |
|---|---|
| **王欣怡** Wang Xinyi | Agent编排设计 / Milvus向量数据库构建 / Customer·Research·Product Agent完整实现 / 联网搜索Agent |
| **温晏瑜** Wen Yanyu | 产品设计 · 结构设计 · 前端页面设计 / RAG数据集构建 |
| **武翔宇** Wu Xiangyu | 初版Demo实现 / Guardrails / 前后端设计 / LoRA模型微调|

> 视频中每位组员需出镜讲解自己负责的章节（总长 ≤ 12 分钟）。

## 我们的选题

**多 Agent 自动化产品设计流水线** — 用户输入一句模糊的产品想法，系统自动产出从市场调研、PRD、技术架构、代码骨架、QA 报告到完整交付包的全套产物。

**Pipeline**：`Customer → Orchestrator → Research → Product → Architect → Coder → QA → Delivery`

**为什么选这个题**：
- 天然展示 Agentic 四阶段循环（每个 agent 都有独立的 Perceive / Reason / Action）
- 多 agent 协作 → 一次性触发多个 Bonus 方向（RAG / Eval / Guardrails / A2A）
- Orchestrator + 回流机制 → 体现"目标导向、多步骤"而非单轮问答
- 输出可视化、可下载、可演示 → 视频 / Live demo 友好

## 技术栈

- **Backend**: Python 3.10+ · LangGraph · **Gemini 2.5 Flash** · ChromaDB · FastAPI
- **Frontend**: Vue 3 · Vite（打包后纯静态，可部署到 Nginx / Vercel / GitHub Pages）

## 作业 8 章节 → 代码映射

| § | 章节 | 落在哪 | 状态 |
|---|---|---|---|
| 1 | **Overview** | 本 README + [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | ✅ |
| 2 | **Perceive** | `backend/agents/customer.py`（理解用户）+ `backend/rag/`（检索增强）| ✅ |
| 3 | **Reason** | `backend/agents/orchestrator.py`（路由 + 任务拆解）+ 各 agent CoT prompt | ✅ |
| 4 | **Action** | RAG 检索 + （TODO）Tool calling / A2A | ⚠️ |
| 5 | **Learn** | Few-shot prompts + LoRA 微调 Customer Agent (Qwen2.5-3B-Instruct, 400条数据) | ✅ |
| 6 | **AI-Human** | 前端输入 / 流水线可视化 / 工件下载 + 回流确认 | ✅ |
| 7 | **Responsible AI** | `backend/guardrails/` + `agents/qa.py`（grounding）| ✅ |
| 8 | **Conclusion** | 视频 + PPT（待录制）| ⏳ |

**已触发的 Bonus 方向**：① RAG（双库 + RBAC）· ③ Evaluation（路由准确率，TODO RAGAS）· ⑤ A2A（泛化版，TODO 严格版）· ⑥ Advanced Guardrails（8/10 子项）

```
agentic_app/
├── .env                       # secrets (gitignored)
├── .env.example
├── requirements.txt → requirements/base.txt
├── backend/
│   ├── main.py                # FastAPI entry
│   ├── api/                   # REST + WebSocket routes, schemas
│   ├── core/                  # config, state, graph builder
│   ├── agents/                # 7 agents + orchestrator router
│   ├── rag/                   # ChromaDB + RBAC
│   ├── guardrails/            # injection / code-safety
│   ├── llm/                   # Gemini client wrappers
│   └── utils/                 # helpers
├── frontend/                  # Vue 3 + Vite SPA
└── scripts/run_demo.py        # CLI one-shot
```

---

## 0. 一键启动

```bash
./start.sh                # 自动建 venv、装依赖、起后端 + 前端、打开浏览器
./start.sh --no-open      # 不自动打开浏览器
./start.sh --reset        # 清掉 venv / node_modules / kb_store 重来一遍
```

按 **Ctrl+C** 同时停后端和前端。日志在 `.logs/{backend,frontend}.log`。

> 第一次启动会下载 ChromaDB 嵌入模型 (~79MB)，需要等 30-60 秒；之后启动只要几秒。

---

## 1. Backend (manual)

### 1.1 Setup

```bash
cd agentic_app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`.env` 文件已经创建（含 `GOOGLE_API_KEY`）。配置由 [backend/core/config.py](backend/core/config.py) 通过 `pydantic-settings` 自动加载。

> ⚠️ 当前 `.env` 里那个 key 在前面对话中已暴露，**演示完务必去 Google AI Studio 撤销重新生成**。

### 1.2 Run the API server

```bash
uvicorn backend.main:app --reload --port 8000
```

Open:
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### 1.3 CLI demo (no frontend needed)

```bash
python scripts/run_demo.py "I want to build an AI tutoring app for kids"
```

### 1.4 Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | service status + model name |
| POST | `/api/run` | one-shot: run full pipeline, return final state |
| POST | `/api/guardrails/injection-check` | classify a single text |
| WS | `/api/ws/run` | streaming: emits `node_done` events as agents finish |

WebSocket protocol:
```
client -> {"user_idea": "...", "thread_id": "optional"}
server -> {"event": "started", "thread_id": "..."}
server -> {"event": "node_done", "node": "research", "diff": {...}}   (xN)
server -> {"event": "final", "state": {...}}
```

---

## 2. Frontend

### 2.1 Dev mode

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to `localhost:8000`.

### 2.2 Build for static deployment

```bash
npm run build      # writes ./dist
npm run preview    # serves ./dist on :4173
```

`dist/` is a pure-static bundle — drop on Nginx, Vercel, GitHub Pages, etc. (set `VITE_API_BASE` env if backend lives elsewhere; current setup uses same-origin proxy).

### 2.3 What the UI shows

- **Pipeline** — 7 nodes light up green as each agent finishes; the next one pulses blue
- **Artifacts** — Project Brief / Research / PRD / Tech Design / Code / QA report panels populate live
- **Guardrail flags** — code-safety / injection issues surfaced inline
- **Final Package** — downloadable JSON
- **Log** — WebSocket event timeline

---

## 3. Development tips

- Reset KB: `rm -rf kb_store/` then restart (auto re-seeds)
- Add real docs to KB: write a script using `backend.rag.kb.KnowledgeBase().business.add(...)`
- Tweak the orchestrator: edit [backend/agents/orchestrator.py](backend/agents/orchestrator.py)
- Add a new agent: drop a file in `backend/agents/`, register in `backend/core/graph.py`

---

## 4. 交付物清单（按作业要求）

| 交付物 | 状态 | 备注 |
|---|---|---|
| Pre 视频（≤ 12 分钟，全员出镜）| ⏳ 待录 | 内容覆盖 8 章节 |
| PPT | ⏳ 待做 | 每人讲自己负责的部分 |
| 代码 / 项目文件 | ✅ | 本 repo + Github push |
| Colab Notebook | ⏳ | 把 `scripts/run_demo.py` 改造成 notebook |
| Live Demo（可选）| ✅ | `./start.sh` 即可 |
| Evaluation 结果（CSV / 图表）| ⏳ | 待写 `scripts/eval_ragas.py` |
| Guardrails 测试报告（注入拦截率表格）| ⏳ | 待写 `scripts/guardrails_test.py` |

---

## 5. TODO (v2)

- [x] LoRA fine-tune Customer Agent (Qwen2.5-3B-Instruct, 4-bit QLoRA, 300 train / 50 val / 50 test, eval_loss=0.103)
- [ ] RAGAS eval pipeline (`scripts/eval_ragas.py`)
- [ ] Guardrails attack-suite report
- [ ] Wrap Customer + Delivery as A2A servers (Google `a2a-sdk`)
- [ ] LangSmith / Langfuse observability
