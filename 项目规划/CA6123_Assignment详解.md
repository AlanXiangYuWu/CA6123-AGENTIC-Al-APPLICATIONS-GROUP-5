# CA6123 Group Assignment


## 🎯 Assignment 一句话概括

**4 人小组 · 设计并实现一个 Agentic AI 应用 · 完整覆盖"Perceive → Reason → Action → Learn"四阶段循环 · 录一个 ≤ 12 分钟 YouTube 视频演示 + 交源码 · 5/11 截止。**

---

## ⏰ 关键日期

| 日期 | 事项 | 逾期后果 |
|---|---|---|
| **2026-05-11（周一）12 noon** | Video YouTube 链接 + Source Code 提交到 NTULearn | 无 submission = Assignment 0 分 |
| **2026-05-15（周五）12 noon** | Peer Evaluation 提交 | 没交 = **该项 5% 0 分** |

提交次数：**最多 3 次，但只评估最后一次**。建议只在最终满意时上传。

---

## 📦 Assignment 核心要求

### 1. 主题范围

**自由选题**，官方示例（不限于）：

1. Complex travel assistant
2. Autonomous expense receipt processor
3. Intelligent SQL query agent
4. Retail location strategy analyser
5. Multi-agent research team
6. Automated data science workflow agent

### 2. 必须具备的 6 大特征

| 特征 | 含义 |
|---|---|
| **Planning** | agent 自主规划步骤（而非被 prompted 一步一步给指令）|
| **Multi-agent workflow** | 至少多个 specialised agents 协作 |
| **Multi-step reasoning** | 复杂目标拆解为子任务 |
| **Tool use** | 调用 APIs / databases / web / 代码执行等外部工具 |
| **Learning** | in-context learning（few-shot）或更高级的学习能力 |
| **Responsible human oversight** | 有 human-in-the-loop 设计 |

### 3. Good vs Bad · 关键判别

**❌ Bad（Gen AI，不符合 Agentic 要求）**：
> "Find flights to New York." → 给一段 JSON 答案

**✅ Good（Agentic AI）**：
> "Book a 5-to-7-day return trip to New York for under S$1500 that fits my calendar."
> → agent 自主查日历 → 搜航班 → 比价 → 筛选 → 预订 → 写入日历 → 确认

**Agentic = 给目标 → 自主多步 → 交结果**
**Gen AI = 给指令 → 一步执行 → 交答案**

选题时反问自己：**"用户只说一句目标，系统能自动完成吗？"**——能就是 Agentic，不能就是 Gen AI。



---

## 🔄 Agentic AI 四阶段循环（Assignment 核心骨架）

```
                 Perceive
                    ↓
                  Reason
                    ↓
                  Action
                    ↓
                  Learn
                    ↓
                (回到 Perceive)
```

### Perceive（感知）
**职责**：收集环境数据 + 理解用户意图

**Video 必须展示**：
- Prompt engineering（system prompt / user prompt 设计）
- Context engineering（减少幻觉，注入合适上下文）
- 多模态输入（如用到图片 / 音频 / 文档）

**Bonus · Agentic RAG**：不是简单 RAG（检索就用），而是 agent 自己判断何时需要 retrieve、retrieve 什么、如何验证结果。

### Reason（推理）
**职责**：分析理解 + 制定计划

**Video 必须展示**：
- LLM 做**意图分类和路由**（routing to specialized agents）
- 复杂任务**拆解**（Chain-of-Thought / Tree-of-Thought / Plan-Execute）
- 决策过程可见（不是黑盒）

### Action（行动）
**职责**：执行决策、调用工具

**Video 必须展示**：
- Tool calling（function calling）
- 具体工具：web scraping / search / API / DB / code execution
- 工具失败的错误处理

**Bonus**：
- **MCP (Model Context Protocol)**：用 MCP 协议对接工具
- **A2A (Agent2Agent)**：agent 间用 A2A 协议协作

### Learn（学习）
**职责**：评估结果 + 改进策略

**Video 必须展示**：
- In-context learning（few-shot prompting）——基础必做
- 任务失败时的重试 / 反思 / 修正

**Bonus**：
- Agent Observability（追踪 agent 行为、记录 trace）
- Agent Evaluation（量化评估 agent 表现）
- Reinforcement Learning（真的让 agent 从反馈中学习）

---

## 📹 Video Submission · 格式与要求

### 硬性规定

| 项目 | 要求 |
|---|---|
| **平台** | YouTube（提交 URL 链接）|
| **时长** | **≤ 12 分钟**（超时部分不评估）|
| **内容** | 一段**单一连续**视频（不能拼接多段）|
| **原声** | **所有组员必须出镜 + 本人真声讲解** · **禁止 TTS** |
| **字幕** | 可选（建议加）|
| **Slides** | 可用 PPT 辅助，必须有口述 |
| **Pointers** | 建议用虚拟指针（PPT 激光笔）|
| **视觉清晰** | 字太小 / 画面乱 → 扣 Clarity 分 |

### Video 必须覆盖的 8 个部分

1. **Overview** · 目标 + 动机 + 功能描述 + 整体 workflow
2. **Perceive 阶段** · prompt engineering + context engineering
3. **Reason 阶段** · 意图分类 + 路由 + 任务拆解（CoT）
4. **Action 阶段** · tool calling 设计与实现
5. **Learn 阶段** · in-context learning 等
6. **AI-Human Interaction** · human oversight 设计
7. **Responsible Agentic AI** · guardrails 设计 + 测试 + 有效性评估
8. **Conclusions** · 组员贡献 + 创新点 + 挑战 + bonus + AI 工具声明

### 原创性声明

- Assignment 必须**小组原创**，抄袭 = 严重学术违规
- 用了 AI 工具（Claude / ChatGPT / Cursor 等），**必须在 video 最后一页 slide 明确声明**
- 老师期望你**能讲清楚为什么这样做**（demonstrate ownership）

---

## 💻 Source Code Submission

### 格式要求

- **Jupyter Notebook**（`.ipynb`）或 **Python 源文件**（`.zip`）
- 文件名**必须带 Group No.**（例 `Group5_AgenticAI.ipynb`）

### 代码质量要求

| 要求 | 说明 |
|---|---|
| 清晰的 headings、函数名、section | 便于老师快速定位 |
| 详细注释 + markdown 解释 | 每个关键决策要有说明 |
| 代码实现 + 设计考虑都要说明 | 不只"怎么做"，也要"为什么" |
| 可读、组织良好、可复现 | 老师可能实际跑代码验证 |

**警告**：代码不清、文档差 → **扣分**

---

## 💯 评分细则（Rubric）

### Assignment 100% 内部拆分

```
Technical Competency    25%   四阶段循环设计 + 实现 + 鲁棒性
Correctness & Clarity   25%   描述正确 + 清晰 + 代码匹配
Responsible Agentic AI  25%   guardrails + human-in-the-loop + 日志 + 评估
Novelty & Originality   10%   应用创新 + workflow 设计新颖
Bonus Features          15%   Appendix B 的高级特性
──────────────────────────
                       100%
```

### 1. Technical Competency · 25%

**老师看什么**：
- 四阶段循环每阶段的**设计合理性**
- 实现的**鲁棒性**（异常处理、fallback、边界）
- Workflow 的**复杂度**（不是越复杂越好，解决问题的复杂度合理）

**怎么拿满**：
- 四阶段都有独立、实打实的代码
- 展示错误处理（tool 失败、LLM 幻觉、超时）
- 展示非 trivial 的 multi-agent 协作（不是一个 agent 装成多个）

### 2. Correctness & Clarity · 25%

**老师看什么**：
- 四阶段描述**技术正确**（不能瞎说概念）
- **解释清楚**（视觉辅助 + live demo）
- **提交代码与 video 演示的功能一致**

**怎么拿满**：
- PPT 有 workflow 流程图
- Video 里有 live demo（不只是讲 slides）
- 代码 comment 和 markdown 说明充分
- 术语用对（CoT、ReAct、RAG、MCP、function calling 等）

### 3. Responsible Agentic AI · 25%

**老师看什么**：
- **Guardrails** 的合理性与可靠性
- **Human-in-the-loop** 交互设计
- **Performance tracking**（通过 logs）
- **Rigorous evaluation**（系统性测试）

**怎么拿满**：
- 至少 2-3 种 guardrails（话题过滤 + PII 脱敏 + prompt injection 检测）
- 展示 guardrails 触发场景
- 至少 1 个 human-in-the-loop 决策点（高风险动作前求确认）
- 有日志系统记录 agent 决策轨迹
- 设计 evaluation metric（任务完成率、token 消耗、延迟、准确率）

### 4. Novelty & Originality · 10%

**老师看什么**：
- **应用场景**的新颖度
- **Workflow 设计**的新颖度

**怎么拿满**：
- 不要选 6 个示例主题
- 找真实场景（最好和组员背景/行业相关）
- workflow 设计有独特之处

### 5. Bonus Features · 15%

见下节深度解析。

---

## 🌟 Bonus Features 深度解析（15%）

### 1. Agentic RAG ⭐⭐⭐ 推荐做
**是什么**：agent 自主决定何时 retrieve、从哪 retrieve、结果不够是否再 retrieve
**工作量**：中
**效果**：提升 Perceive 分数
**建议**：用 LangChain agent executor 或 LlamaIndex AgenticRAG

### 2. Agent Observability ⭐⭐⭐ 强推荐（性价比最高）
**是什么**：追踪 agent 每一步（trace）
**工具**：Langfuse / W&B / LangSmith / OpenTelemetry
**工作量**：低（接入成熟工具即可）
**效果**：直接打 Responsible AI 分
**Video 展示**：录制 Langfuse dashboard 截图，展示完整 trace

### 3. Agent Evaluation ⭐⭐⭐ 推荐做
**是什么**：主动评估 agent 质量
**方法**：
- 定义 golden set（几十到几百测试 case）
- 对 agent 跑测试，记录成功率 / 延迟 / token
- LLM-as-judge 评估输出
**工作量**：中
**效果**：同时打 Responsible AI 分

### 4. MCP (Model Context Protocol) ⭐⭐⭐ 强推荐
**是什么**：Anthropic 2024 标准，统一 agent 访问外部资源
**工作量**：中
**效果**：视觉上非常"前沿"，老师印象深刻
**建议**：至少实现 1 个 MCP server

### 5. A2A (Agent2Agent) ⭐⭐ 可选
**是什么**：agent 之间用标准协议通信
**工作量**：高
**建议**：只做 simulated（框架形式）

### 6. Advanced Guardrails ⭐⭐⭐ 推荐做
**是什么**：
- **Prompt injection 过滤**（检测 "ignore previous instructions"）
- **PII redaction**（信用卡号、邮箱、身份证号脱敏）
- **Output moderation**（OpenAI Moderation API / Guardrails AI）

**工作量**：中
**效果**：直接打 Responsible AI 25% 分

### 7. Agent Reinforcement Learning ⭐ 不推荐
**工作量**：极高
**风险**：短期做不出 demo 效果
**建议**：**除非你有 RL 背景，否则别碰**

### 8. Other Advanced Features
自己高级实现（meta-learning / prompt optimization 等），video 里明确 highlight 也算 bonus。

**建议至少做 3 个 bonus features（选推荐度 ⭐⭐⭐ 的）**

---

## 👥 Team Roles · 4 人分工建议

| 角色 | 职责 |
|---|---|
| **Team Lead (Member 1)** | Orchestrator agent 设计 · 任务分配 · System Prompts / Context / Tools / In-Context Learning |
| **Member 2** | Specialised Agent A · workflow design (Sequential/Parallel) |
| **Member 3** | Specialised Agent B |
| **Member 4** | Specialised Agent C |

**组长职责**：
- 默认是 group members list 里**第一个名字**
- 负责 5/11 之前上传作业
- 组内可以重新指定其他人上传，**但只能上传一次**
- **Group No. 必须写在文件名里**

---


## 📋 Submission Checklist

### Video 检查
- [ ] 长度 ≤ 12 分钟
- [ ] 所有组员都出镜讲过
- [ ] 全是真人原声（无 TTS）
- [ ] 八大部分都覆盖
- [ ] 至少 2-3 个 bonus features highlight
- [ ] 最后一页 slide 声明使用的 AI 工具
- [ ] YouTube 链接可访问（不是 private）
- [ ] 字幕清晰（可选）
- [ ] Slide 字体够大

### Code 检查
- [ ] 文件名带 Group No.
- [ ] `.ipynb` 或 `.zip` 格式
- [ ] 有清晰 headings / sections
- [ ] 关键代码有注释
- [ ] 有 markdown 解释设计思路
- [ ] 代码能跑（实际跑一次验证）
- [ ] 依赖包列出
- [ ] 环境变量 / API Key **占位符**（不要放真实 key）

### 组织检查
- [ ] Group Lead 明确
- [ ] 上传到 NTULearn Blackboard UCV → Assignment → Gradebook
- [ ] Video 上传到 "Assignment Video" 条目
- [ ] Code 上传到 "Assignment Code" 条目
- [ ] 只上传一次（最后版本最终有效）

---

## 🏆 高分实战策略

### 总体思路

按 rubric 优先级投入时间：
```
Tech Competency (25%) + Correctness (25%) + Responsible (25%) = 75%
→ "正规军分"，必须满分或接近满分

Bonus (15%) → 2-3 个 bonus 拉开与普通组差距

Novelty (10%) → 选对题就拿到
```

### 选题策略

**差选题**：
- 照搬示例的 6 个
- "做一个 Q&A 助手"（太 Gen AI）
- "做一个自动化某 SaaS 功能"（太 narrow）

**好选题**：
- 结合组员真实行业背景的场景（教育 / 医疗 / 法律 / 金融细分）
- 有明确"目标 → 多步 → 结果"的痛点
- 场景本身就需要多 agent 协作
- **有可量化的评估指标**（加分项）

### Workflow 设计策略

每阶段都做出**显性可见**的工作：
- **Perceive**：不只"读 prompt"，要有 context enrichment
- **Reason**：必须有明确的 task decomposition（先列步骤，再执行）
- **Action**：至少调 **3+ 种不同 tools**（不要全是 web search）
- **Learn**：哪怕 simple reflection loop，也要让老师看到"失败 → 反思 → 重试"

### Video 拍摄策略

**前 30 秒是黄金时间**：
- 不要花时间自我介绍
- 直接展示：用户输入一句目标 → agent 自动跑完 → 结果
- "Before-After"对比：传统方法 X 步，agentic 一条指令搞定

**中段要有 live demo**：
- 不要全程 slide 讲解
- 至少 30-60 秒屏幕录制：agent 真的在跑、在 call tool、在输出

**展示"失败 & recovery"**：
- 故意让 agent 遇到错误
- 展示 guardrail 触发
- 比"全程顺利"的 demo 说服力强 10 倍

**最后 1 分钟**：
- bonus features 快速列出
- 每人一句话说自己贡献
- AI 工具声明

### Slide 设计策略

- 不要密密麻麻文字（Clarity 扣分）
- 每张 slide 最多 5 条 bullet
- 用 workflow 图（Lucid / draw.io / Mermaid）
- 代码截图放大到能看清
- 配色专业（深色背景 + 高对比字 / 纯白底 slides）

### 时间分配建议（33 天）

| 周 | 任务 |
|---|---|
| **Week 1 (4/13-4/18)** | 组队 + 选题 + 分工 + 跑通 Lab 1 |
| **Week 2 (4/20-4/25)** | Prototype 骨架（4 阶段 skeleton）+ Lab 2（multi-agent）|
| **Week 3 (4/27-5/2)** | 接入 tools + guardrails + 1 个 bonus · **5/2 mid-quiz** |
| **Week 4 (5/4-5/9)** | 完善 4 阶段 + 加 2-3 个 bonus + 集成测试 |
| **Week 5 Mon (5/11)** | **5/11 12 noon 前录 video + 上传** |

**关键风险点**：
- Week 1 末还没选定主题 → 严重落后
- Week 3 还没接通 tools → 考虑砍范围
- Video 留给最后 1-2 天 → 太紧张，**应该 5/8-5/9 就开始录**

---

## ⚠️ 常见陷阱 · 别踩坑

### 陷阱 1 · "这是 Gen AI 不是 Agentic"
- **症状**：整个 app 就是 ChatGPT + RAG，无自主规划、无多 agent
- **后果**：Technical Competency 和 Novelty 双低
- **解决**：反复问"给一个目标，agent 能自主走完吗？"

### 陷阱 2 · Multi-agent 是假的
- **症状**：说是 3 个 agent，其实同一 LLM 被 call 3 次
- **后果**：老师看代码就识破
- **解决**：每个 agent 有独立 system prompt / tools / memory

### 陷阱 3 · 四阶段不均衡
- **症状**：Perceive / Reason 花 80% 精力，Action / Learn 草草了事
- **后果**：Technical Competency 扣分
- **解决**：四阶段分配给 4 个组员

### 陷阱 4 · Responsible AI 只嘴上说
- **症状**：Video 提 "我们有 guardrails"，但没演示触发
- **后果**：25% 分大打折扣
- **解决**：录一段"恶意输入 → guardrail 触发 → 被拒绝"

### 陷阱 5 · 代码和 video 不一致
- **症状**：Video 说有某功能，代码找不到
- **后果**：Correctness 大扣
- **解决**：上传前对照 video 每个功能在代码里找到

### 陷阱 6 · Video 超 12 分钟
- **症状**：录了 15 分钟，舍不得剪
- **后果**：**超出部分完全不评估**，conclusion 全丢
- **解决**：严格按脚本录，每人限时 2.5-3 分钟


### 陷阱 7 · 组长文件名没写对
- **症状**：`assignment_final.ipynb`（没 group no.）
- **后果**：可能被分错组
- **解决**：文件名统一 `GroupXX_CA6123_项目名.ipynb`

### 陷阱 8 · Peer Eval 忘了交
- **症状**：5/15 12 noon 过了才想起来
- **后果**：自己的 Peer Eval 5% 直接 0 分
- **解决**：**5/11 提交完作业当天就把 peer eval 填了**

### 陷阱 9 · AI 工具用了但没声明
- **症状**：用 Claude 写代码，video 最后一页没提
- **后果**：学术诚信问题，可能严重处分
- **解决**：final slide 列所有 AI 工具

---

## 🎬 Video 12 分钟脚本模板

| 时间 | 内容 | 讲者 |
|---|---|---|
| 0:00-0:30 | **Hook 开场** · goal-in / result-out 惊艳 demo | 组长 |
| 0:30-1:30 | **Overview** · 问题背景 + 为什么 agentic + workflow 图 | 组长 |
| 1:30-3:00 | **Perceive** · prompt & context engineering + RAG | Member 2 |
| 3:00-5:00 | **Reason** · LLM 意图分类 + CoT + live demo | Member 2 或 3 |
| 5:00-7:30 | **Action** · tool calling + 多 agent 协作 + live demo | Member 3 |
| 7:30-8:30 | **Learn** · in-context learning + reflection loop | Member 4 |
| 8:30-9:30 | **AI-Human Interaction** · human-in-the-loop 展示 | Member 4 |
| 9:30-10:30 | **Responsible AI** · guardrails + 触发演示 + evaluation | 组长或轮流 |
| 10:30-11:30 | **Bonus Features** · 每个 bonus 10-20 秒展示 | 组长 |
| 11:30-12:00 | **Conclusions** · 组员贡献 + 挑战 + 创新 + AI 工具声明 | 组长 |

**第 1 天就定脚本，每人知道自己 2-3 分钟要讲什么，分头准备。**

---

## 📁 相关资源

```
/Users/cube/Documents/01-NTU/09-CA6123 Agentic AI & Applications/
├── Assignment/
│   ├── CA6123 Assignment Brief - 02Apr2026.pdf         ← 官方 brief
│   ├── Assignment_Briefing_Google_API_Key_Test.ipynb   ← API Key 测试
│   └── CA6123_Assignment详解.md                         ← 本文件
├── Week 1/Notebook/Lab_1_LLM_Retrieval_Augmented_Generation.ipynb
│   → Perceive / RAG 部分可复用
├── Week 2/Notebook/
│   ├── Lab_2a_Simple_Agent_From_Prompt_to_Action_with_Search_tool.ipynb
│   │   → Action / tool calling 模板
│   ├── Lab_2b_Agent_Tools_LRO.ipynb
│   │   → Long-Running Operations 模板
│   └── Lab_2c_MultiAgent_Systems_&_Workflow_Patterns_v1_0.ipynb
│       → Multi-agent 骨架（Assignment 可从这起）
└── CA6123_课程概览.md                                    ← 课程总体策略
```

---

## ✅ 一页总结

**目标**：做一个 agentic AI 应用，**4 人 · 4 阶段 · 12 分钟 video · 5/11 截止**

**三条铁律**：
1. 选题要"给目标 → 自动多步 → 交结果"（不是"给指令 → 一步答"）
2. 四阶段均衡投入，Responsible AI 不要只嘴上说
3. 至少做 2-3 个 bonus features，video 里 highlight

**四个 deadline**：
- **5/11 12 noon** · Video + Code
- **5/15 12 noon** · Peer Eval
- **5/2 13:30** · Mid-course Quiz（并行压力）
- **5/16 13:30** · Final Quiz（assignment 之后）

**拿高分的关键**：选对题 + 四阶段扎实 + 2-3 bonus + video 有 live demo + Responsible AI 有触发演示 + 组员认真参与
