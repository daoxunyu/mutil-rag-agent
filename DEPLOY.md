# Multi-Agent AIOps Platform V3 本地部署文档

> **部署日期**: 2026-07-09  
> **项目**: multi-agent-aiops (多智能体智能运维诊断平台)  
> **架构**: fast/deep 双诊断模式，4 个专业 Agent 并行取证

---

## 目录

- [1. 环境信息](#1-环境信息)
- [2. 基础设施部署](#2-docker-基础设施部署)
- [3. Python 环境与依赖](#3-python-环境与依赖)
- [4. 配置 .env](#4-配置-env)
- [5. 启动应用](#5-启动应用)
- [6. 访问地址](#6-访问地址)
- [7. LLM API Key 配置](#7-llm-api-key-配置)
- [8. Windowws 兼容性修复](#8-windows-兼容性修复)
- [9. 可选：启动 MCP 服务与 Worker](#9-可选启动-mcp-服务与-worker)
- [10. 导入知识库](#10-导入知识库)
- [11. 常见问题排查](#11-常见问题排查)

---

## 1. 环境信息

| 组件 | 版本/配置 | 路径/地址 |
|------|-----------|-----------|
| **操作系统** | Windows 11 Pro | — |
| **Docker** | 29.4.3 | `C:\Program Files\Docker\Docker\` |
| **Python (conda)** | 3.11.15 | `D:\agentcomeptition2\mutil-rag-agent\.venv` |
| **Node.js** | 22.18.0 | 系统 PATH |

---

## 2. Docker 基础设施部署

### 2.1 所需服务

本项目依赖 6 个基础设施服务：

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| **etcd** | `quay.io/coreos/etcd:v3.5.5` | 2379-2380 | Milvus 元数据存储 |
| **MinIO** | `minio/minio:RELEASE.2023-03-20T20-16-18Z` | 9001 | Milvus 对象存储 |
| **Milvus** | `milvusdb/milvus:v2.4.10` | 19530 (gRPC), 9091 (REST) | 向量数据库 |
| **Attu** | `zilliz/attu:v2.4` | 8000 | Milvus 可视化管理 |
| **Redis** | `redis:7-alpine` | 6379 | 消息队列 (Streams) |
| **PostgreSQL** | `postgres:16-alpine` | **5433** (避免冲突) | 诊断事实库 |

### 2.2 端口说明

> ⚠️ **重要**: 由于 openAgent 项目已占用 5432 端口，本项目 PostgreSQL 改用 **5433** 端口。
> 通过 `.env` 中 `POSTGRES_PORT=5433` 覆盖 docker-compose 默认值。

### 2.3 启动命令

```powershell
cd D:\agentcomeptition2\mutil-rag-agent

# 启动基础设施 (不含 open-websearch，需要构建较慢)
docker compose up -d etcd minio standalone attu redis postgres

# 等待所有容器 healthy
docker ps
```

### 2.4 验证

```powershell
# 检查所有容器状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 验证 PostgreSQL 连接 (端口 5433)
docker exec multi-agent-postgres psql -U multi_agent -d multi_agent_aiops -c "\dt"

# 验证 Milvus
docker exec multi-agent-milvus curl -s http://localhost:9091/healthz

# Attu 管理界面: http://localhost:8000
```

### 2.5 停止服务

```powershell
docker compose down          # 停止基础设施
docker compose down -v       # 同时删除数据卷
```

---

## 3. Python 环境与依赖

### 3.1 创建环境

```powershell
# 创建 Python 3.11 conda 环境
conda create -p D:\agentcomeptition2\mutil-rag-agent\.venv python=3.11 -y

# 验证
D:\agentcomeptition2\mutil-rag-agent\.venv\python --version
# Python 3.11.15
```

### 3.2 安装依赖

```powershell
D:\agentcomeptition2\mutil-rag-agent\.venv\python -m pip install -r D:\agentcomeptition2\mutil-rag-agent\requirements.txt
```

**主要依赖包**:

| 类别 | 核心包 | 版本 |
|------|--------|------|
| Web 框架 | fastapi, uvicorn | 0.139.0 / 0.51.0 |
| AI 框架 | langchain | 1.3.12 |
| 智能体编排 | langgraph | 1.2.8 |
| 向量数据库 | pymilvus (Milvus) | 2.6.16 |
| 数据库 | asyncpg | 0.31.0 |
| MCP 协议 | fastmcp | 3.4.4 |
| RAG 评测 | ragas, openevals | 0.4.x |
| 日志 | loguru | 0.7.3 |

---

## 4. 配置 .env

### 4.1 创建配置文件

`.env` 文件位于项目根目录，已自动创建。核心配置：

```env
# LLM 模型 (必需: 至少配一个真实 API Key)
DEEPSEEK_API_KEY=sk-your-real-deepseek-key
# 或
DASHSCOPE_API_KEY=your-real-dashscope-key

# 数据库 (端口 5433 避免与 openAgent 冲突)
DATABASE_URL=postgresql://multi_agent:multi_agent@localhost:5433/multi_agent_aiops
POSTGRES_PORT=5433

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Redis
REDIS_URL=redis://localhost:6379/0

# 其他
KB_ADMIN_TOKEN=change-this-admin-token
```

### 4.2 配置项速查

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DEEPSEEK_API_KEY` | 必填 | DeepSeek API Key |
| `DASHSCOPE_API_KEY` | 必填 | 阿里云 DashScope Key |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding 提供商 |
| `MILVUS_HOST` | `localhost` | Milvus 地址 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接串 |
| `DATABASE_URL` | postgresql://... | PostgreSQL 连接串 |

---

## 5. 启动应用

### 5.1 一键启动

```powershell
cd D:\agentcomeptition2\mutil-rag-agent

# 启动 API 服务器 (含前端静态文件)
.venv\python -m uvicorn app.main:app --host 0.0.0.0 --port 9900
```

### 5.2 启动日志解读

```
INFO - Milvus 连接成功 | collections: []
INFO - [postgres] connected
INFO - [postgres] incident schema ready      ← 数据库表自动创建
INFO - [incident-queue] connected stream=aiops:incident_tasks
INFO - 加载 MCP 工具: ['system', 'websearch', 'winlog', 'network', 'docker']
WARNING - MCP 'docker' 连接失败               ← 可忽略，MCP 服务未启动
INFO - Application startup complete.           ← 启动完成
```

> **说明**: 数据库 schema 在应用启动时通过 lifespan 事件自动创建（`init_incident_schema()`），无需手动初始化。

---

## 6. 访问地址

| 页面 | 地址 | 说明 |
|------|------|------|
| **Web UI (前端)** | http://localhost:9900 | 诊断/事件中心/知识库/评测 |
| **API 文档 (Swagger)** | http://localhost:9900/docs | 完整 API 交互文档 |
| **API 文档 (ReDoc)** | http://localhost:9900/redoc | 替代风格文档 |
| **健康检查** | http://localhost:9900/api/v1/health | 服务存活检查 |
| **就绪检查** | http://localhost:9900/api/v1/health/ready | 所有依赖就绪检查 |
| **队列状态** | http://localhost:9900/api/v1/queue/status | Redis Streams 队列状态 |
| **Attu (Milvus UI)** | http://localhost:8000 | Milvus 可视化管理 |

### API 概览

| 功能 | 方法 | 路径 |
|------|------|------|
| AIOps 诊断 (SSE) | POST | `/api/v1/aiops/diagnose` |
| 后台诊断提交 | POST | `/api/v1/aiops/diagnose/submit` |
| 队列状态 | GET | `/api/v1/queue/status` |
| Alertmanager Webhook | POST | `/api/v1/webhook/alertmanager` |
| RAG Chat | POST | `/api/v1/chat/stream` |
| Skill 列表 | GET | `/api/v1/skills` |
| 上传文档 | POST | `/api/v1/documents/upload` |
| 审批管理 | GET/POST | `/api/v1/approvals/...` |
| Wiki 经验库 | GET/POST | `/api/v1/wiki/...` |

---

## 7. LLM API Key 配置

> ⚠️ **关键**: 没有有效的 LLM API Key，诊断功能无法使用。应用启动会检查 API Key。

### 支持的 LLM 提供商

| 提供商 | 配置项 | 获取地址 |
|--------|--------|---------|
| **DeepSeek** | `DEEPSEEK_API_KEY` | https://platform.deepseek.com |
| **阿里云 DashScope** | `DASHSCOPE_API_KEY` | https://dashscope.aliyun.com |

```env
# 方式一：DeepSeek
DEEPSEEK_API_KEY=sk-your-real-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 方式二：阿里云 DashScope
DASHSCOPE_API_KEY=your-real-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### Embedding 配置

```env
# 本地 Ollama (推荐，免费)
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3

# 或使用 DashScope
EMBEDDING_PROVIDER=dashscope
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v4
```

### 工具 API

```env
# Web Search (需要 open-websearch 服务运行)
WEB_SEARCH_PROVIDER=open_websearch
OPEN_WEBSEARCH_BASE_URL=http://127.0.0.1:3210

# 知识库管理 Token
KB_ADMIN_TOKEN=change-this-admin-token
```

---

## 8. Windows 兼容性修复

本项目部分代码使用了 Linux 专有模块，在 Windows 下需要以下修复：

### 8.1 `fcntl` → `msvcrt` (文件锁)

**文件**: `app/wiki/store.py`

```python
# 修改前 (Linux only)
import fcntl
fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

# 修改后 (跨平台)
import os
if os.name == 'nt':
    import msvcrt
    msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)
else:
    import fcntl
    fcntl.flock(fileno, fcntl.LOCK_EX)
```

---

## 9. 可选：启动 MCP 服务与 Worker

### 9.1 MCP 诊断工具服务

MCP 服务提供系统诊断、网络检查、Docker 监控等能力：

```powershell
# 终端 1: System MCP
.venv\python mcp_servers/system_server.py

# 终端 2: Network MCP  
.venv\python mcp_servers/network_server.py

# 终端 3: Docker MCP
.venv\python mcp_servers/docker_server.py

# 终端 4: WebSearch MCP (需要 open-websearch 服务)
.venv\python mcp_servers/websearch_server.py

# 终端 5: Windows Log MCP
.venv\python mcp_servers/winlog_server.py
```

### 9.2 后台诊断 Worker

```powershell
# Worker 1
.venv\python -m app.diagnosis_worker --name worker-1

# Worker 2 (新终端)
.venv\python -m app.diagnosis_worker --name worker-2

# Worker 3 (新终端)
.venv\python -m app.diagnosis_worker --name worker-3
```

### 9.3 open-websearch (Web 搜索服务)

```powershell
# 构建并启动 (首次需要 npm install，较慢)
docker compose up -d open-websearch
```

---

## 10. 导入知识库

```powershell
cd D:\agentcomeptition2\mutil-rag-agent

# 试运行 (查看将要导入的内容)
.venv\python scripts/ingest_kb_corpus.py --dry-run

# 正式导入并重建索引
.venv\python scripts/ingest_kb_corpus.py --reset
```

---

## 11. 常见问题排查

### 11.1 容器启动失败

```powershell
# 检查所有容器 (包括失败的)
docker ps -a

# 查看特定容器日志
docker logs multi-agent-milvus
docker logs multi-agent-postgres

# 端口冲突检查
netstat -ano | findstr ":5433"
netstat -ano | findstr ":19530"
netstat -ano | findstr ":6379"
```

### 11.2 API 启动报错

```powershell
# DEEPSEEK_API_KEY 未配置
# 错误: RuntimeError: DEEPSEEK_API_KEY 未配置
# 解决: 编辑 .env，填入真实或占位 API Key

# fcntl 模块缺失
# 错误: ModuleNotFoundError: No module named 'fcntl'
# 解决: 参考第 8.1 节修复

# PostgreSQL 连接失败
# 检查: docker ps | grep multi-agent-postgres
# 确认端口 5433 未被占用
```

### 11.3 MCP 连接失败 (WARNING 级别，不影响启动)

API 启动时会尝试连接 5 个 MCP 服务。未启动时只会打 WARNING，不影响 API 和 Web UI 正常访问。

```powershell
# 如需使用诊断功能，启动对应的 MCP 服务
.venv\python mcp_servers/system_server.py &
.venv\python mcp_servers/network_server.py &
```

### 11.4 Milvus 连接问题

```powershell
# 检查 Milvus 状态
docker logs multi-agent-milvus | tail -5

# 通过 Attu 管理界面检查: http://localhost:8000
```

### 11.5 完全清理与重建

```powershell
# 停掉所有服务
docker compose down -v

# 重新启动
docker compose up -d etcd minio standalone attu redis postgres

# 等 30 秒让所有服务就绪后再启动 API
```

---

## 附录：架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue-like SPA)                  │
│                 http://localhost:9900                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 FastAPI API Server (:9900)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │Diagnosis │  │ RAG Chat │  │ Webhook  │  │  Queue API  │ │
│  │  SSE     │  │  Stream  │  │ AlertMgr │  │  Status     │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Worker 1    │  │  Worker 2    │  │  Worker 3    │
│ (diagnosis)  │  │ (diagnosis)  │  │ (diagnosis)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └──────────┬──────┴─────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────────┐
│ fast   │  │  deep    │  │   Skill      │
│ Plan-  │  │ Evidence │  │   Router     │
│ Execute│  │  Graph   │  │   Playbook   │
└───┬────┘  └────┬─────┘  └──────┬───────┘
    │            │               │
    └────────────┼───────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐ ┌─────────┐ ┌──────────┐
│ Milvus │ │ Postgres│ │  Redis   │
│ Vector │ │ Facts   │ │ Streams  │
│  DB    │ │ DB      │ │ Queue    │
└────────┘ └─────────┘ └──────────┘

deep 模式多 Agent 取证流程:
  IncidentManager → CorrelationContext → EvidencePlan
    → MetricAgent / LogAgent / InfraAgent / RunbookAgent (并行)
    → EvidenceReducer → RCAJudge → RemediationPlanner → ReportAgent
```
