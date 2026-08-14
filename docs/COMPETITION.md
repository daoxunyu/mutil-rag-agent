# 多智能体协同高校全专业个性化导学与资源生成平台

## 竞赛作品说明文档

---

## 一、作品概述

### 1.1 项目名称

**多智能体协同高校全专业个性化导学与资源生成平台**

### 1.2 核心定位

面向高等教育场景的**多智能体协同导学系统**，通过 6 个专业 Agent 的并行协作，实现：

- 🎯 **对话式学习画像构建** (8 维度动态画像)
- 📚 **多模态学习资源生成** (文档/PPT/题库/视频脚本/代码案例/拓展阅读，6 种类型)
- 🛤️ **个性化学习路径规划** (阶段性路径 + 自适应调整 + 精准推送)
- 💡 **智能辅导答疑** (文字解答 + 图解 + 短视频讲解)
- 📈 **学习效果评估** (多维度精准评估 + 动态调整策略)
- 🛡️ **防幻觉与安全过滤** (LLM + 确定性双重质量审核)

系统同时保留了原有的 **AIOps 智能运维诊断**能力（4 个诊断 Agent + fast/deep 双模式），展示多智能体框架的双场景适配能力。

### 1.3 技术亮点

| 亮点 | 说明 |
|------|------|
| **6 Agent 并行协作** | LangGraph fan-out/fan-in 模式，6 个教育 Agent 并行运行 |
| **SSE 流式输出** | 实时展示 Agent 协作过程，避免长时间白屏等待 |
| **规则路由 + LLM 智能** | EvidencePlan 规则路由 + LLM 内容生成的两层架构 |
| **画像增量更新** | 随学随新，每次学习自动更新画像 |
| **双重质量审核** | 确定性检查 + LLM 内容安全审查 |
| **RAG 知识增强** | Milvus 向量库 + BM25 混合检索 + bge-reranker 精排 |
| **MCP 工具协议** | 标准化工具接入，可扩展 |

---

## 二、需求分析

### 2.1 新时代大学生学习痛点

| 痛点 | 描述 | 解决方案 |
|------|------|---------|
| 资源繁杂无序 | 海量课程资料难以筛选 | 多 Agent 自动生成精准匹配的个性化资源 |
| 缺乏个性化指导 | 标准化教学无法兼顾个体差异 | 8 维度画像驱动的自适应学习 |
| 学习路径模糊 | 不知道从何学起、按什么顺序 | PathAgent 规划科学路径+推送计划 |
| 答疑反馈慢 | 遇到问题难以及时解决 | TutorAgent 即时多模态答疑 |
| 效果难以评估 | 缺乏量化学习反馈 | EvalAgent 多维度评估+动态调整 |

### 2.2 技术-需求结合点

| 赛题要求 | 技术实现 |
|---------|---------|
| 对话式学习画像 (6+维度) | ProfileAgent + LLM 对话抽取 → 8 维度 JSON 画像 |
| 多智能体协同资源生成 (5+类型) | 6 Agent LangGraph fan-out 并行 → 6 种资源类型 |
| 个性化路径规划与推送 | PathAgent + push_schedule 字段 |
| 智能辅导答疑 (加分) | TutorAgent + 多模态解答 (文字/图解/视频) |
| 学习效果评估 (加分) | EvalAgent + 多维度评分 |
| 防幻觉机制 | QualityReviewer 确定性+LLM双重审核 |
| 流式生成进度 | SSE 实时推送 Agent 状态 |

---

## 三、系统架构

### 3.1 多智能体架构图

```
┌────────────────────────────────────────────────────────────────┐
│                      前端 (Web UI)                              │
│   🎓 智能导学  │  🔧 AIOps诊断  │  📚 知识库  │  📊 事件中心    │
└────────────────────────────┬───────────────────────────────────┘
                             │ SSE / REST
┌────────────────────────────▼───────────────────────────────────┐
│                     FastAPI (:9900)                             │
│  /api/v1/education/*    /api/v1/aiops/*    /api/v1/chat/*     │
└────────────────────────────┬───────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  教育多智能体图   │ │ AIOps诊断图   │ │   技能路由层      │
│  (EducationGraph) │ │ (DeepGraph)  │ │   (SkillRouter)  │
└────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘
         │                  │                  │
    ┌────┴──────────────┐   │   ┌──────────────┴──────┐
    ▼    ▼    ▼    ▼    ▼   ▼   ▼    ▼     ▼     ▼   ▼
 Profile│Knowledge│Resource  Log│Metric│Infra│Runbook
  Agent │ Agent  │ Agent    Agent│Agent│Agent│ Agent
         │                  │
    ┌────┴──────┐     ┌─────┴─────┐
    ▼           ▼     ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Milvus │ │Postgres│ │ Redis  │ │  MCP   │
│ Vector │ │ Facts  │ │Streams │ │ Tools  │
└────────┘ └────────┘ └────────┘ └────────┘
```

### 3.2 教育多智能体编排流程

```
[START]
   │
   ▼
StudentContext      载入学生画像 + 课程信息
   │
   ▼
ResourcePlan        识别需求 → 决定派哪些 Agent + 资源类型
   │
   ├──→ ProfileAgent     📊 构建/更新 8 维度学习画像
   ├──→ KnowledgeAgent   📚 生成课程讲解文档 + 思维导图
   ├──→ ResourceAgent    🎯 生成 6 种多模态学习资源
   ├──→ PathAgent        🛤️ 规划个性化学习路径 + 推送计划
   ├──→ TutorAgent       💡 多模态智能答疑
   └──→ EvalAgent        📈 多维度学习效果评估
   │ (fan-in join barrier)
   ▼
ResourceIntegrator  整合所有 Agent 产出 → 统一资源包
   │
   ▼
QualityReviewer     防幻觉检查 + 内容安全过滤 (确定性 + LLM)
   │
   ▼
LearningAdvisor     生成学习建议 + 自适应调整策略
   │
   ▼
ReportAgent         格式化 Markdown 报告 → 触发 [END]
```

### 3.3 教育 Agent 详细设计

| Agent | 职责 | 输出 | 关键实现 |
|-------|------|------|---------|
| **ProfileAgent** | 对话式画像构建 | 8 维度 JSON 画像 | LLM 对话抽取 + 关键词兜底 |
| **KnowledgeAgent** | 知识解析 | 课程文档 + 思维导图 | LLM 结构化 JSON 生成 |
| **ResourceAgent** | 多模态资源 | 文档/PPT/题库/视频/代码/阅读 | 分类型 prompt + 确定性兜底 |
| **PathAgent** | 路径规划 | 分阶段路径 + 推送日程 | 图像驱动的自适应规划 |
| **TutorAgent** | 智能辅导 | 文字解答 + 图解 + 视频要点 | 多模态 prompt |
| **EvalAgent** | 学习评估 | 多维度评分 + 改进建议 | 数据驱动的精准评估 |

---

## 四、核心技术实现

### 4.1 多智能体协同框架

采用 **LangGraph StateGraph** 实现确定性编排：

```python
# 核心模式: fan-out 并行 + fan-in join
wf = StateGraph(EducationState)
# 注册 6 个 Agent 节点
for name in ["profile_agent", "knowledge_agent", ...]:
    wf.add_node(name, _dispatch_edu(name))
# fan-out: ResourcePlan → 6 Agent 并行
for name in EDUCATION_AGENTS:
    wf.add_edge("resource_plan", name)
    wf.add_edge(name, "resource_integrator")  # fan-in barrier
```

- **隔离上下文**: 每个 Agent 只读自己的 scoped 输入，中间推理不进共享 state
- **结构化黑板**: Agent 通过 `profiles/resources/paths/...` 共享字段交换结果
- **规则路由**: `ResourcePlan` 用关键词规则路由决定派遣哪些 Agent，避免不必要调用
- **并发安全**: 使用 `Annotated[List, operator.add]` reducer，多 Agent 并发写不冲突

### 4.2 8 维度学习画像

```json
{
  "knowledge_base": {"score": 65, "level": "进阶", "description": "..."},
  "cognitive_style": {"primary": "视觉", "score": 80, "evidence": "..."},
  "learning_goals": {"short_term": "...", "mid_term": "...", "long_term": "..."},
  "weakness_patterns": [{"topic": "...", "error_type": "...", "frequency": "高"}],
  "learning_pace": {"speed": "中", "session_minutes": 45},
  "interest_domains": [{"domain": "机器学习", "enthusiasm": 90}],
  "prerequisites": [{"course": "Python基础", "mastery": 80}],
  "resource_preference": {"documents": 70, "videos": 60, "code": 80, "interactive": 50}
}
```

### 4.3 6 种资源类型

| 资源类型 | 格式 | 示例内容 |
|---------|------|---------|
| `document` | Markdown | 概念讲解、公式推导、案例分析 |
| `ppt_outline` | JSON slides | 标题、要点、备注、时长 |
| `quiz` | JSON questions | 选择/填空/简答 + 答案 + 解析 |
| `video_script` | JSON scenes | 分镜、讲解词、时长 |
| `code_example` | 代码块 | 可运行代码 + 注释 + 输出 |
| `reading_material` | Markdown | 摘要、推荐理由、参考文献 |

### 4.4 防幻觉与安全机制

- **确定性检查**: `ResourceIntegrator` 对空资源、缺失字段标记 warning
- **LLM 内容审核**: `QualityReviewer` 调用独立 LLM 检查事实错误和不当内容
- **规则兜底**: 所有 Agent 都有 `_fallback_*` 函数，LLM 不可用时降级到确定性输出
- **内容过滤**: 禁止生成敏感/违规内容，审核结果标注在 `quality_review.safe_content`

### 4.5 流式生成进度

使用 **SSE (Server-Sent Events)** 实时推送：

```
event: status       → "🎓 多智能体系统启动中..."
event: agent_output → {"agent": "profiles", "label": "📊 学习画像", "content": {...}}
event: agent_output → {"agent": "resources", "label": "🎯 学习资源", "count": 6}
event: report       → {"content": "# 🎓 个性化学习报告\n..."}
event: done         → {}
```

---

## 五、AIOps 智能运维（保留功能）

系统同时保留完整的 AIOps 诊断能力：

- **fast 模式**: Skill-first Plan-Execute-Replan 单 Agent 快速诊断
- **deep 模式**: 4 Agent (Metric/Log/Infra/Runbook) 并行取证 + RCA 判定
- **4 个内置 Skill**: 主机资源 / 网络连通性 / Docker 容器 / 通用 OnCall
- **后台队列**: Redis Streams + 3 Worker + 全局执行槽
- **RAG 知识库**: Milvus Vector + BM25 Hybrid + RRF + rerank

---

## 六、创新点

1. **双场景 LangGraph 多智能体框架**: 同一套基础设施支撑教育导学和 AIOps 诊断
2. **规则路由 + LLM 生成**: 用规则做确定性编排（避免 Agent 互聊上下文失控），LLM 负责内容生成
3. **Evidence 黑板模式**: Agent 不直接互聊，通过结构化字段传递，并发安全且可审计
4. **全链路兜底**: 每个 Agent 都有确定性降级函数，确保系统在 LLM 不可用时仍可产出结果
5. **流式进度追踪**: SSE 实时呈现 6 个 Agent 的工作状态，解决了多模态资源生成的白屏等待问题

---

## 七、使用的开源项目与 AI 工具

| 项目/工具 | 用途 | 协议 | 来源 |
|----------|------|------|------|
| **LangGraph** | 多智能体编排框架 | MIT | https://github.com/langchain-ai/langgraph |
| **LangChain** | LLM 应用框架 | MIT | https://github.com/langchain-ai/langchain |
| **FastAPI** | Web API 框架 | MIT | https://github.com/fastapi/fastapi |
| **Milvus** | 向量数据库 | Apache 2.0 | https://github.com/milvus-io/milvus |
| **PostgreSQL** | 关系数据库 | PostgreSQL License | https://www.postgresql.org/ |
| **Redis** | 消息队列/缓存 | BSD-3 | https://redis.io/ |
| **MCP (Model Context Protocol)** | 工具接入协议 | MIT | https://modelcontextprotocol.io/ |
| **Claude Code** | AI 辅助编程工具 | — | 科大讯飞相关工具 (开发辅助) |
| **Tailwind CSS** | 前端样式 | MIT | https://tailwindcss.com/ |
| **bge-reranker-v2-m3** | RAG 精排模型 | MIT | BAAI |

---

## 八、测试说明

### 8.1 测试环境

- OS: Windows 11 Pro
- Python: 3.11.15
- Docker: 29.4.3
- 依赖: 见 requirements.txt

### 8.2 功能测试

| 测试项 | 方法 | 预期结果 |
|--------|------|---------|
| 教育多智能体 SSE | POST /api/v1/education/learn | 返回流式 Agent 产出 + 最终报告 |
| 画像构建 | POST /api/v1/education/profile | 返回 8 维度 JSON 画像 |
| 题库生成 | POST /api/v1/education/quiz | 返回选择/填空/简答题 |
| 智能答疑 | POST /api/v1/education/tutor | 返回文字+图解+视频脚本 |
| 学习评估 | POST /api/v1/education/eval | 返回多维度评分+建议 |
| AIOps SSE 诊断 | POST /api/v1/aiops/diagnose | 返回 Skill→Plan→Execute→Report |
| 质量审核 | 自动触发 | 检查 safe_content=true |

### 8.3 知识库测试

初始知识库: 以**机器学习/人工智能**课程为切入点，包含：
- 教材章节文档 (5 章)
- SOP 学习流程文档
- 练习题收集

导入命令: `python scripts/ingest_kb_corpus.py --reset`

---

## 九、部署说明

详见 [DEPLOY.md](../DEPLOY.md)
