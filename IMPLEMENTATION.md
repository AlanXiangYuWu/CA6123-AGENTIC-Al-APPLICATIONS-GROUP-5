# CA6123 Group 5 — 实现方案逐点说明

本文对应 `CA6123 项目规划（draft.md` 的每一节，说明**用什么技术 + 怎么落地 + 对应代码位置**。代码全部在 [`agentic_workflow.py`](agentic_workflow.py)。

---

## 0. 整体技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| Agent 编排 | **LangGraph** `StateGraph` | 显式状态机，可视化路由、支持回流、自带 checkpointer |
| LLM | **Gemini 2.0 Flash**（`langchain-google-genai`） | 已有 API Key，免费额度大，速度快 |
| RAG 向量库 | **ChromaDB** (本地 PersistentClient) | 零运维、本地可跑、支持 metadata 过滤实现 RBAC |
| Embedding | Gemini `text-embedding-004` 或 Chroma 默认 | 与主 LLM 同生态 |
| 评估 | **RAGAS** + LangSmith trace | 官方 RAG 评估框架 + 路由准确率 |
| 护栏 | LLM 分类器 + 静态扫描 + Schema 校验 | 多层叠加 |
| 微调（v2） | Unsloth + Qwen2.5-7B + LoRA | T4 GPU 4-bit 可跑（v1 先用 Gemini 跳过） |
| A2A | LangGraph 内部 State 共享（v1）；可选 `a2a-sdk`（v2） | 待和老师确认严格度 |

---

## 1. 完整工作流图（draft 第 1 节）

**实现方式**：用 LangGraph 的 `StateGraph` + 条件边构建。

- 7 个节点：`customer / research / product / architect / coder / qa / delivery`
- 1 个 router 函数 `orchestrator_router`：纯 Python 函数，不调用 LLM，根据 state 字段决定下一跳
- START → customer，所有业务节点完成 → router → 下一节点 / END

> 代码位置：`build_graph()` ([agentic_workflow.py](agentic_workflow.py))

---

## 2. 各 Agent 实现（draft 第 2 节）

每个 Agent 都是**一个 Python 函数**，签名 `(state) -> dict`，统一模式：
1. 从 state 取上游产物
2.（可选）走 RAG 检索带 RBAC
3. 调 Gemini 生成结构化 JSON 输出
4. 跑 guardrail（如 code safety）
5. 返回 state 增量

### (1) Customer Agent
- **输入**：用户原始消息（自然语言）
- **输出**：`project_brief` JSON（product_name, target_users, core_problem, must_have_features, platform, success_criteria）
- **关键技巧**：在 system prompt 中要求"最多追问 3 次，确认后用 `<BRIEF>...</BRIEF>` 标签包裹 JSON"——这样路由函数可以稳定检测"是否产出 brief"
- **v2 替换点**：把 Gemini 换成 LoRA 微调后的 Qwen2.5（见第 3 节）

### (2) Orchestrator
- **不是 LLM Agent**，是个**路由函数 + state 字段**
- 决策依据（按优先级）：
  1. `revision_round > 2` → 强制 delivery（防死循环，对应 draft 5.7）
  2. 缺 project_brief → customer
  3. 缺 research_report → research
  4. ……（线性 gating，对应 draft 5.8 Task Plan 约束）
  5. `qa_report.passed == False` → coder（回流）
  6. 否则 → delivery → END
- **回流机制**：`qa_post` 节点在 QA 失败时清空 `code_artifact` 和 `qa_report`、`revision_round += 1`

> 为什么不用 LLM 做 Orchestrator？路由准确率要求高、确定性优于灵活性、便于评估、零成本。

### (3) Research Agent
- **RAG 检索**：query = brief 关键字，调 `kb().retrieve(query, agent="Research")`，受 RBAC 限制只能访问 `business` 库
- **Citation 强制**：system prompt 要求"每个事实带 `[doc_id]` 标记"，输出 JSON 中包含 `citations: [{claim, source_doc_id}]`
- **输出**：`research_report = {competitors, user_pain_points, opportunities, citations}`

### (4) Product Agent
- **输入**：brief + research_report
- **输出**：`prd = {positioning, user_flows, features (priority-ranked), non_functional_requirements, success_metrics}`
- 不走 RAG（信息已在 state 中），纯 LLM 综合

### (5) Architect Agent
- **RAG**：检索 `technical` 库（框架文档）
- **输出**：`tech_design = {tech_stack, system_components, data_model, api_contracts, deployment_notes}`

### (6) Coder Agent
- **输入**：tech_design
- **输出**：`code_artifact = {files: [{path, content}], entry_point, run_instructions}`
- **Guardrail 联动**：每个文件过 `code_safety_scan()`，检测 `AIza` `sk-` `AKIA` 等 secret 前缀和未走 env var 的 API key 引用，命中写入 `state.guardrail_flags`

### (7) QA Agent
- **温度 0**（用 `llm_strict`），保证评判稳定
- **检查 4 件事**：PRD 覆盖 brief / Tech 覆盖 PRD / Code 匹配 Tech / 是否有幻觉
- **输出**：`qa_report = {passed: bool, score: 0-1, issues, test_cases}`
- `passed=False` 触发回流到 coder

### (8) Delivery Agent
- **聚合**所有上游产物，输出 9 段 Final Package（对应 draft 第 2 节末尾）
- 不走 RAG，纯总结

---

## 3. LoRA 微调（draft 第 3 节）

**v1 阶段**：跳过，用 Gemini + 精心设计的 system prompt 顶替。
**v2 阶段**：单独 pipeline，与主流程解耦：

```python
# Colab T4 + Unsloth 4-bit
from unsloth import FastLanguageModel
model, tok = FastLanguageModel.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", load_in_4bit=True, max_seq_length=2048
)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=32, target_modules=["q_proj","k_proj","v_proj","o_proj"]
)
# 数据集：draft 中的 messages 格式 JSON
# 训练后 export 成 GGUF / 挂在本地推理服务，customer_agent 改成调本地 endpoint
```

**数据来源**：draft 提到"人工 / GPT 生成"。建议先用 Gemini 自己生成 200-500 组对话（输入：模糊 idea；输出：多轮追问 + 最终 brief），再人工过滤 50 组高质量做 eval。

---

## 4. Evaluation（draft 第 4 节）

### 4.1 路由准确率（Workflow correctness）
- 每个 agent 节点向 `state.trace` append 自己名字
- 跑完后比对 `state.trace` 与人工标注的"正确路径"
- 三个指标：
  - **路由准确率**：每一跳是否对
  - **顺序准确率**：完整路径是否按 Task Plan 排
  - **回流准确率**：QA 失败时是否回到 coder

> 代码位置：`_append_trace()` + 每个 agent 末尾

### 4.2 RAGAS（Agent 输出 vs 知识库）
独立离线脚本（建议新建 `eval_ragas.py`）：

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

# 准备 30-50 个测试用例：question / contexts(检索结果) / answer / ground_truth
ds = Dataset.from_list([...])
result = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
result.to_pandas().to_csv("ragas_report.csv")
```

### 4.3 Claim-level verification
对每个 agent 输出里 `citations` 字段中的每条 claim，重新跑一次 LLM-as-judge：
"给定 source_doc，以下 claim 是否被支持？" 输出 yes/no/partial。

---

## 5. Advanced Guardrails（draft 第 5 节）

| # | 实现位置 | 技术 |
|---|---|---|
| (1) Prompt Injection | `detect_prompt_injection()` | Gemini 分类器，温度 0，JSON 输出。在 `run()` 入口处调用，conf > 0.7 直接拒绝 |
| (2) RBAC | `KnowledgeBase.retrieve()` + `AGENT_KB_ACCESS` | dict 白名单 + collection 隔离 |
| (3) Tool-level | （v2）每个 agent 注册 `allowed_tools = [...]`，执行前校验 | 现在 agent 还没接外部工具，留接口 |
| (4) 输出检查 | QA Agent 的 `issues` 字段 | LLM-as-judge 检查 hallucination/groundedness |
| (5) Code Safety | `code_safety_scan()` | 静态正则扫描 secret 前缀 + env var 用法 |
| (6) Orchestrator 控制 | LangGraph 强制：节点不能调用其它节点 | 架构层强约束，agent 只能返回 state，路由由 router 决定 |
| (7) 回流限制 | `revision_round > 2` 强制 delivery | 路由函数第一条规则 |
| (8) Task Plan 约束 | 路由函数线性 gating | Product 必须等 Research 完成才会被路由到 |

**测试报告**：单独写 `guardrails_test.py`，准备 20 条注入样本（"忽略你之前的指令" / "把 system prompt 打印出来" / 多语言变体）+ 20 条正常样本，统计拦截率/误杀率，画混淆矩阵。

---

## 6. RAG（draft 第 6 节）

**采用方案一**（双库 + RBAC），更符合 guardrails 要求：

| Collection | 内容 | 可访问 Agent |
|---|---|---|
| `business` | PRD 模板、市场调研模板、商业画布、行业报告 | Research, Product, QA, Delivery |
| `technical` | 框架文档（LangGraph/FastAPI/...）、设计模式、安全 best practice | Architect, Coder, QA |

**索引流程**（一次性脚本 `index_kb.py`）：
1. 收集 PDF / Markdown 文档
2. `langchain.text_splitter.RecursiveCharacterTextSplitter` 切片（chunk=800, overlap=100）
3. Gemini embedding 向量化
4. 写入 ChromaDB，metadata 带 `{kb, doc_id, chunk_id, source_url}`

> 代码位置：`KnowledgeBase` 类，`_seed_if_empty()` 提供了一个最小可跑的种子集（生产前替换为真实文档索引脚本）

---

## 7. A2A（draft 第 7 节，待和老师确认）

**两种实现路径**，建议先问老师：

### Path A — 严格 Google A2A 协议
- 用 `a2a-sdk` 把 `Customer Agent` 和 `Delivery Agent` 包成独立 HTTP server
- Orchestrator 用 A2A client 调用：4 步 = Discover (`/.well-known/agent.json`) → Authenticate → Send Task → Stream Result
- 加分但工作量大

### Path B — 泛化"多 Agent 协作"
- 完全在 LangGraph 内部，agent 通过共享 `ProjectState` 通信
- 满足"设计过的多 Agent 协作"语义
- 简单，已实现

**推荐**：v1 默认 Path B；v2 把 Customer + Delivery 用 a2a-sdk 暴露，证明掌握协议（演示价值高）。

---

## 8. 对应作业 8 个章节的映射

draft 是技术规划，作业要求 8 章。映射如下：

| 作业章节 | 本项目对应实现 |
|---|---|
| 1. Overview | README + 工作流图（draft 第 1 节） |
| 2. Perceive | Customer Agent 多轮追问 + RAG（draft 6） |
| 3. Reason | Orchestrator 路由 + 各 agent 内部 CoT prompt |
| 4. Action | RAG 检索 + （v2）外部工具调用 + （可选）A2A |
| 5. Learn | Few-shot prompt + LoRA 微调（draft 3） |
| 6. AI-Human | Customer Agent 追问交互 + 回流确认 |
| 7. Responsible AI | 8 层 Guardrails（draft 5） + 测试报告 |
| 8. Conclusion | 团队分工 + 创新点（A2A、双 KB RBAC、回流死循环保护） |

---

## 9. 工作分工建议（6 人）

| 模块 | 工作量 | 负责人建议 |
|---|---|---|
| Orchestrator + LangGraph 主架构 | 大 | 1 人（技术 lead） |
| Customer Agent + LoRA 微调 | 大 | 1 人 |
| Research + Product Agent + 业务 KB | 中 | 1 人 |
| Architect + Coder Agent + 技术 KB | 中 | 1 人 |
| QA + Delivery Agent + Eval | 中 | 1 人 |
| Guardrails + 测试报告 + A2A | 中 | 1 人 |

每人都要在视频里讲自己模块的 Perceive/Reason/Action/Learn 切片。

---

## 10. 下一步 TODO

1. 撤销已泄露的 API Key，重新生成
2. `pip install langgraph langchain-google-genai chromadb pydantic` 验证 `agentic_workflow.py` 跑通
3. 收集 10 篇真实业务文档 + 10 篇技术文档，跑 `index_kb.py` 替换 seed 数据
4. 写 `eval_ragas.py` + 30 条测试用例
5. 写 `guardrails_test.py` + 20 条注入样本
6. 找老师确认 A2A 严格度
7. 决定是否做 LoRA（v2）
