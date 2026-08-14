"""FastAPI 应用入口.

启动顺序:
  1. 初始化日志
  2. 校验配置
  3. 创建 FastAPI 实例
  4. 注册中间件
  5. 注册全局异常处理器
  6. 注册路由
  7. 挂载静态文件 (前端)
  8. lifespan 钩子 (启动时连 Milvus, 关闭时断开)

启动方式:
  开发: uvicorn app.main:app --reload
  生产: uvicorn app.main:app --workers 4
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.middleware import setup_middlewares
from app.api.v1 import aiops, chat, documents, education, eval as eval_api, health, incidents, queue, skills, webhook, wiki, approvals, courses, calendar, collaboration
from app.config import settings
from app.core.mcp_client import mcp_client_manager
from app.core.milvus import milvus_manager
from app.db.postgres import close_postgres, connect_postgres, init_incident_schema
from app.exceptions import AppException
from app.logging_config import setup_logging
from app.queue.redis_streams import incident_queue
from app.schemas.common import ApiResponse


# ============================================================
# Lifespan: 启动/关闭钩子
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理.

    yield 之前: 启动时执行 (连数据库、初始化资源)
    yield 之后: 关闭时执行 (清理资源)
    """
    # ==================== 启动 ====================
    logger.info("=" * 60)
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    logger.info(f"运行模式: {'DEBUG' if settings.debug else 'PRODUCTION'}")
    logger.info("=" * 60)

    # 追踪哪些服务实际连接成功, 用于关闭时清理
    _milvus_ok = False
    _postgres_ok = False
    _redis_ok = False

    # 1. 校验配置 (无效时警告, 不阻止启动)
    try:
        settings.validate_runtime()
    except Exception as e:
        logger.warning(f"配置校验警告: {e}")

    # 2. 连接 Milvus (可选, 失败降级)
    try:
        milvus_manager.connect()
        _milvus_ok = True
        logger.info("Milvus 连接成功")
    except Exception as e:
        logger.warning(f"Milvus 不可用, 向量检索功能禁用: {e}")

    # 3. 初始化 Incident Pipeline (Postgres 事实库 + Redis Stream 队列)
    if settings.incident_pipeline_enabled:
        try:
            await connect_postgres()
            await init_incident_schema()
            _postgres_ok = True
            logger.info("Postgres 连接成功")
        except Exception as e:
            logger.warning(f"Postgres 不可用, 事件存储功能禁用: {e}")

        try:
            await incident_queue.connect()
            _redis_ok = True
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 不可用, 消息队列功能禁用: {e}")

    # 4. 加载 MCP 工具 (可选依赖, 失败仅 warning)
    try:
        await mcp_client_manager.connect(fail_silently=True)
    except Exception as e:
        logger.warning(f"MCP 连接异常: {e}")

    logger.info("应用就绪 (部分服务可能不可用), 等待请求...")
    yield
    # ==================== 关闭 ====================
    logger.info("应用正在关闭...")
    try:
        await mcp_client_manager.close()
    except Exception:
        pass
    if _redis_ok:
        try:
            await incident_queue.close()
        except Exception:
            pass
    if _postgres_ok:
        try:
            await close_postgres()
        except Exception:
            pass
    if _milvus_ok:
        try:
            milvus_manager.disconnect()
        except Exception:
            pass
    logger.info("应用已关闭")


# ============================================================
# 创建 FastAPI 实例
# ============================================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="企业级多智能体智能运维诊断平台 - 基于 LangGraph + RAG + MCP",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================
# 中间件
# ============================================================
setup_middlewares(app)


# ============================================================
# 全局异常处理器
# ============================================================
@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """处理业务异常."""
    logger.warning(f"业务异常: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            code=exc.code, message=exc.message, detail=exc.detail
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理 Pydantic 校验失败."""
    logger.warning(f"参数校验失败: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=ApiResponse.error(
            code="VALIDATION_ERROR",
            message="请求参数校验失败",
            detail=exc.errors(),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """兜底: 处理所有未捕获异常."""
    logger.exception(f"未预期的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error(
            code="INTERNAL_ERROR",
            message="服务内部错误, 请稍后重试或联系管理员",
            detail=str(exc) if settings.debug else None,
        ).model_dump(),
    )


# ============================================================
# 路由注册
# ============================================================
API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(aiops.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(incidents.router, prefix=API_PREFIX)
app.include_router(skills.router, prefix=API_PREFIX)
app.include_router(webhook.router, prefix=API_PREFIX)
app.include_router(queue.router, prefix=API_PREFIX)
app.include_router(eval_api.router, prefix=API_PREFIX)
app.include_router(wiki.router, prefix=API_PREFIX)
app.include_router(approvals.router, prefix=API_PREFIX)
app.include_router(education.router, prefix=API_PREFIX)  # 教育多智能体导学平台
app.include_router(courses.router, prefix=API_PREFIX)
app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(collaboration.router, prefix=API_PREFIX)

logger.info("[Routes] courses/calendar/collaboration/education routers registered")

# ============================================================
# 静态文件 (前端)
# ============================================================
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
else:
    logger.warning(f"前端目录不存在: {FRONTEND_DIR} (将在阶段 5 创建)")

    @app.get("/", include_in_schema=False)
    async def root() -> ApiResponse[dict]:
        """临时根路由 (前端目录还没创建时使用)."""
        return ApiResponse.success(
            data={
                "name": settings.app_name,
                "version": settings.app_version,
                "docs": "/docs",
                "health": f"{API_PREFIX}/health",
            },
            message="服务运行中, 前端目录将在阶段 5 创建",
        )


# ============================================================
# 启动时初始化日志
# ============================================================
setup_logging()

