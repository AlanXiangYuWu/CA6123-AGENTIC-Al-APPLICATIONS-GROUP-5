# `agentic_app` 项目说明

> 配套文档：[README.md](README.md)（运行说明）· [../IMPLEMENTATION.md](../IMPLEMENTATION.md)（按 draft 逐点说明）

---

## 1. 项目是什么

一个**多 Agent 自动化产品设计流水线**：用户给一句模糊想法 → 系统自动产出完整交付物（市场调研 / PRD / 技术架构 / 代码骨架 / 测试报告 / Demo 脚本 / Roadmap）。

**类比**：相当于一个浓缩的"AI 创业团队"。
- Customer Agent = 产品经理跟客户沟通
- Research Agent = 市场分析师
- Product Agent = 产品负责人写 PRD
- Architect Agent = 架构师选型 + 设计
- Coder Agent = 工程师写骨架
- QA Agent = 测试工程师
- Delivery Agent = 项目经理打包交付
- **Orchestrator = 项目总指挥（决定下一步谁干）**

---

## 2. 整体架构（三层）

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3 + Vite)                 │
│   Idea Input  →  Pipeline Visualization  →  Artifact Cards  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI  (backend/main.py)                 │
│   /api/health · /api/run · /api/ws/run · /api/guardrails... │
└──────────────────────────────┬──────────────────────────────┘
                               │ asyncio.to_thread
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                LangGraph StateGraph (核心)                  │
│                                                             │
│   START → customer → [orchestrator] → research → ...        │
│                          ↑                                  │
│                          └── 所有 agent 完成后回到这里      │
│                                                             │
│   - Gemini 2.5 Flash (LLM)                                  │
│   - ChromaDB (RAG, 双库 + RBAC)                            │
│   - Guardrails (注入检测 / 代码安全)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 当前 Pipeline 图（实际跑通版本）

### 3.1 状态机视图

```
                            ┌──────────┐
                            │  START   │
                            └────┬─────┘
                                 ▼
                          ┌──────────────┐
                ┌────────►│  customer    │  → project_brief
                │         └──────┬───────┘
                │                │
                │                ▼
                │     ┌──────────────────────────┐
                │     │ orchestrator_router (函数)│ ◄────┐
                │     └──────────┬───────────────┘      │
                │                │                      │
                │   ┌────┬───────┼───────┬────┬────┐    │
                │   ▼    ▼       ▼       ▼    ▼    ▼    │
                │ research product architect coder qa  delivery
                │   │    │       │       │    │       │ │
                │   │    │       │       │    │       └─┴─ ►  END
                │   │    │       │       │    ▼
                │   │    │       │       │  ┌─────────┐
                │   │    │       │       │  │ qa_post │  ←── 失败 → revision++
                │   │    │       │       │  └────┬────┘
                │   │    │       │       │       │
                │   └────┴───────┴───────┴───────┘
                │   每个节点完成后都回到 orchestrator_router
                │
                └─── customer 在 brief 缺失时会被回流（fallback 已避免无限循环）
```

### 3.2 一次成功调用的实际 trace

我用中文 demo 跑出来的真实路径（见 `/tmp/zh_out.json`）：

```
customer → research → product → architect → coder → qa → qa_post → delivery → END
revision_round = 0
QA score = 0.97 (passed)
citations = 8 (来自 ChromaDB business + technical 库)
```

### 3.3 QA 失败时的回流（设计中，未在当前 demo 触发）

```
... → coder → qa → qa_post {passed=false}
                       │
                       ├── revision_round += 1
                       ├── 清空 code_artifact + qa_report
                       └── 路由器看到缺 code_artifact → 回到 coder
                       
revision_round > 2 时 → 强制 delivery（防死循环）
```

---

## 4. Orchestrator 是怎么实现的（重点）

> **核心思想：Orchestrator 不是一个 LLM Agent，是一个确定性 Python 函数 + LangGraph 的 conditional edges。**

很多开源例子里 Orchestrator 用 LLM 做"任务分解"，但我们的场景是**线性流水线 + 一个回流分支**，用 LLM 反而：
- 路由不稳定（同一个 state 可能选不同下一跳）
- 速率/成本浪费
- 难以做评估（路由准确率指标对不齐）

所以选择**纯 Python 状态机**：决策依据是 `ProjectState` 的字段，规则透明、可单元测试。

### 4.1 实现位置

[backend/agents/orchestrator.py](backend/agents/orchestrator.py) — 整个 Orchestrator 只有两个函数：

```python
def orchestrator_router(state: ProjectState) -> RouteTarget:
    # 决定"下一跳去哪个节点"
    ...

def qa_post(state: ProjectState) -> dict:
    # QA 失败时清空产物 + 增加回流计数
    ...
```

### 4.2 路由规则（按优先级）

```python
# 1. 死循环保护（draft 5.7）
if revision_round > 2:
    return "delivery"   # 强制收尾

# 2. Task Plan 线性约束（draft 5.8）
#    缺什么就路由到产出它的 agent
if not project_brief:    return "customer"
if not research_report:  return "research"
if not prd:              return "product"
if not tech_design:      return "architect"
if not code_artifact:    return "coder"
if not qa_report:        return "qa"

# 3. QA 失败回流到 Coder（draft 第 2.7 节"QA 发现 bug 后返回 Coder"）
if qa_report.passed is False:
    return "coder"

# 4. 最终交付
if not final_package:
    return "delivery"
return "__end__"
```

**这一套规则能自动满足 draft 里所有约束**：
- ✅ Product 必须在 Research 之后（缺 research 就回 research）
- ✅ Coder 必须在 Architect 之后
- ✅ QA 必须在 Coder 之后
- ✅ QA 失败回流到 Coder
- ✅ 回流不超过 2 次

### 4.3 LangGraph 怎么把规则"装"进图里

[backend/core/graph.py](backend/core/graph.py)：

```python
g = StateGraph(ProjectState)
g.add_node("customer", customer_agent)
g.add_node("research", research_agent)
# ... 注册所有节点

# 关键：每个 agent 完成后都用 orchestrator_router 决定下一跳
for node in ("customer", "research", "product", "architect", "coder", "delivery"):
    g.add_conditional_edges(node, orchestrator_router, ROUTE_MAP)

# QA 比较特殊：先过 qa_post 处理回流，再走路由器
g.add_edge("qa", "qa_post")
g.add_conditional_edges("qa_post", orchestrator_router, ROUTE_MAP)
```

`add_conditional_edges` 的机制：
- 节点函数返回 state 后，调用 `orchestrator_router(state)` 拿一个字符串
- 字符串通过 `ROUTE_MAP` 映射到下一个节点名 / `END`
- 整个过程是 LangGraph 调度的，外部代码不需要写 `while` 循环

### 4.4 qa_post：回流的"准备工作"

为什么 QA 后需要单独一个 `qa_post` 节点？因为我们要在路由器看到 `qa_report` 之前**清掉它**——否则路由器看到 `qa_report` 已存在就会绕过 QA 流程。

```python
def qa_post(state):
    qa = state.get("qa_report") or {}
    if qa.get("passed") is False:
        return {
            "revision_round": revision_round + 1,
            "code_artifact": None,   # ← 清空，让路由器把它送回 coder
            "qa_report": None,       # ← 清空，让路由器知道还要再 QA 一次
        }
    return {}
```

这样**修改 = 删除产物 + 让路由器自然路由**，不需要在路由器里写"上次 QA 失败"这种特殊判断。

### 4.5 为什么这种设计好

| 维度 | 纯 Python 路由（当前）| LLM 做路由 |
|---|---|---|
| 确定性 | ✅ 同 state 永远同跳 | ❌ 概率性，可能跳错 |
| 可测试 | ✅ 普通单元测试 | ❌ 要用回归测试集 |
| 路由准确率评估 | ✅ trace vs 期望路径直接对比 | ⚠️ 需要 LLM-as-judge |
| 成本 | ✅ 0 个 token | ❌ 每跳一次 LLM 调用 |
| 速度 | ✅ 微秒级 | ❌ 秒级 |
| 灵活性 | ⚠️ 流程改动需改代码 | ✅ 改 prompt 即可 |

我们的流程是**写死的产品设计 SOP**，不需要灵活性 → 选定确定性方案。

### 4.6 守住 draft 5.6 的"Orchestrator 强制约束"

draft 第 5.6 条："**所有数据流必须经过 Orchestrator，agent 不能跳过流程调用其他 agent**"。

这条在我们的实现里**架构层强制达成**：
- 每个 agent 函数签名是 `(state) -> dict`，**只能返回 state 增量**
- agent 内部**没有调用其他 agent 的能力**——它甚至不知道其他 agent 存在
- 路由完全由 LangGraph + `orchestrator_router` 控制
- 想绕过流程？只能改图结构，没办法在 agent 里偷跑

---

## 5. 已完成 vs 未完成（详细清单）

### 5.1 ✅ 已完成

| 模块 | 实现位置 | 状态 |
|---|---|---|
| Customer Agent | `backend/agents/customer.py` | ✅ + fallback 防死循环 |
| Research Agent | `backend/agents/research.py` | ✅ 带 RAG + citation |
| Product Agent | `backend/agents/product.py` | ✅ |
| Architect Agent | `backend/agents/architect.py` | ✅ 带 RAG |
| Coder Agent | `backend/agents/coder.py` | ✅ 带 code-safety guardrail |
| QA Agent | `backend/agents/qa.py` | ✅ 温度 0 评判 |
| Delivery Agent | `backend/agents/delivery.py` | ✅ |
| Orchestrator (router + qa_post) | `backend/agents/orchestrator.py` | ✅ 见 §4 |
| LangGraph 装配 | `backend/core/graph.py` | ✅ + checkpointer |
| 全局 State | `backend/core/state.py` | ✅ |
| 配置加载（env vars）| `backend/core/config.py` | ✅ pydantic-settings |
| Gemini 客户端 | `backend/llm/gemini.py` | ✅ 创意/严格双客户端 |
| RAG ChromaDB 包装 | `backend/rag/kb.py` | ⚠️ 架构 ✅，内容 6 条种子 |
| RBAC | `backend/rag/access_control.py` | ✅ 双库白名单 |
| Prompt 注入检测 | `backend/guardrails/injection.py` | ✅ Gemini 分类器 |
| Code Safety 扫描 | `backend/guardrails/code_safety.py` | ✅ 正则 + env var 检查 |
| FastAPI REST | `backend/api/routes.py` | ✅ |
| FastAPI WebSocket 流式 | `backend/api/routes.py` | ✅ stream_mode=updates |
| Pydantic schemas | `backend/api/schemas.py` | ✅ |
| Vue 3 前端 | `frontend/src/App.vue` | ✅ |
| 流水线可视化 | `frontend/src/components/PipelineView.vue` | ✅ |
| 工件展示 | `frontend/src/components/ArtifactCard.vue` | ✅ |
| CLI demo 脚本 | `scripts/run_demo.py` | ✅ |
| 中文输入支持 | （Gemini 多语言原生）| ✅ 已验证 |
| 完整端到端跑通 | — | ✅ HTTP 200 / 4-5 分钟 |

### 5.2 ⚠️ 部分完成

| 项目 | 完成度 | 缺什么 |
|---|---|---|
| **RAG 知识库内容** | 5% | 真实文档（每库 30-50 篇）+ 切片索引脚本 |
| **Evaluation** | 40% | RAGAS + claim-level verification + 测试集 |
| **Tool-level Guardrail** | 0% | Agent 还没接外部工具 |
| **输出 hallucination 严格检查** | 30% | QA 做了基础检查，没用 LLM-as-judge 严格复核 |

### 5.3 ❌ 未做

| 项目 | 计划 |
|---|---|
| **LoRA 微调 Customer Agent** | v2，独立 Colab notebook，Unsloth + Qwen2.5-7B |
| **A2A 严格协议（Google a2a-sdk）** | 待和老师确认严格度，可能 Path B 已够 |
| **LangSmith / Langfuse 接入** | 可观测性 bonus |
| **Agentic RL（自我学习）** | bonus 7，工作量最大 |

---

## 6. 关键路径上的 TODO（按优先级）

```
P0  写 scripts/index_kb.py + 收集 20 篇真实文档    (RAG 内容)
P0  写 scripts/eval_ragas.py + 30 条测试用例       (Evaluation)
P0  写 scripts/guardrails_test.py + 20 条注入样本  (作业明确要求)
─────────────────────────────────────────────────────
P1  问老师 A2A 严格度 → 决定是否用 a2a-sdk
P1  Tool-level Guardrail：给 Research 接 web 搜索工具
P1  LangSmith trace 接入
─────────────────────────────────────────────────────
P2  LoRA 微调（v2 单独工程）
P2  视频 + PPT + 测试报告
```

---

## 7. 怎么验证一切都跑通

```bash
# 1. 确认服务健康
curl http://127.0.0.1:8000/api/health
# {"status":"ok","model":"gemini-2.5-flash"}

# 2. 跑英文测试
python scripts/run_demo.py "your idea here"

# 3. 跑中文测试
curl -X POST http://127.0.0.1:8000/api/run \
  -H 'Content-Type: application/json' \
  -d '{"user_idea":"做一个面向中国大学生的求职助手 App"}'

# 4. 浏览器看可视化
open http://127.0.0.1:5173
```

成功的标志：
- `trace` 字段是 `customer → research → product → architect → coder → qa → qa_post → delivery`
- `qa_report.passed === true`
- `final_package` 包含 9 个 section
- `citations` 数组非空（证明 RAG 走通）
- `guardrail_flags` 通常为空（除非 Coder 真的写了泄露 secret 的代码）
