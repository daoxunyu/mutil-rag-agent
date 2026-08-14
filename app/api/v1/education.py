"""教育多智能体导学 API — 与 AIOps 诊断 API 并列存在。

POST /api/v1/education/learn   → SSE 流式学习请求 (画像+资源+路径)
POST /api/v1/education/profile → 对话式画像构建
POST /api/v1/education/quiz    → 生成练习题
POST /api/v1/education/tutor   → 智能答疑
GET  /api/v1/education/eval    → 学习评估
"""

import json
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agents.state_education import EducationState
from app.education_graph import build_education_graph

router = APIRouter(prefix="/education", tags=["education"])

_edu_graph = None


def _get_edu_graph():
    global _edu_graph
    if _edu_graph is None:
        _edu_graph = build_education_graph()
    return _edu_graph


class EducationRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000, description="学生输入/学习请求")
    mode: str = Field(default="comprehensive", description="comprehensive/profile/knowledge/resource/path/tutor/eval")
    student_id: str = Field(default="", description="学生ID")
    course: str = Field(default="", description="课程名称")
    chapter: str = Field(default="", description="章节")


class ProfileRequest(BaseModel):
    student_id: str = Field(default="")
    query: str = Field(..., min_length=1, max_length=2000, description="学生自我介绍/学习需求描述")
    major: str = Field(default="", description="专业")
    grade: str = Field(default="", description="年级")


@router.post("/learn", summary="多智能体学习资源生成 (SSE 流式)")
async def education_learn(req: EducationRequest, request: Request):
    """启动教育多智能体编排，流式返回资源生成过程。

    与 AIOps /api/v1/aiops/diagnose 使用相同的 SSE 模式。
    6 个 Agent 协作: Profile→Knowledge→Resource→Path→Tutor→Eval
    """
    async def event_stream() -> AsyncIterator[dict[str, str]]:
        try:
            graph = _get_edu_graph()
            initial_state: EducationState = {
                "input": req.query,
                "student_id": req.student_id,
                "course_info": {
                    "name": req.course or "待识别课程",
                    "chapter": req.chapter or "",
                },
            }
            yield {"event": "message", "data": json.dumps({"type": "status", "content": "🎓 多智能体系统启动，6 个 Agent 协作中..."}, ensure_ascii=False)}

            # 使用 astream 流式执行，每完成一个节点就推送
            AGENT_LABELS = {
                "profile_agent": "📊 学习画像",
                "knowledge_agent": "📚 知识解析",
                "resource_agent": "🎯 资源生成",
                "path_agent": "🛤️ 路径规划",
                "tutor_agent": "💡 智能辅导",
                "eval_agent": "📈 学习评估",
            }
            AGENT_OUTPUT_KEYS = {
                "profile_agent": "profiles",
                "knowledge_agent": "knowledge_docs",
                "resource_agent": "resources",
                "path_agent": "learning_paths",
                "tutor_agent": "tutor_responses",
                "eval_agent": "evaluations",
            }
            final_state: EducationState = {}
            async for event in graph.astream(initial_state):
                for node_name, node_state in event.items():
                    if not isinstance(node_state, dict):
                        continue  # 节点返回 None 或非 dict, 跳过
                    final_state.update(node_state)
                    label = AGENT_LABELS.get(node_name)
                    if label:
                        key = AGENT_OUTPUT_KEYS.get(node_name, "")
                        items = node_state.get(key) or []
                        content = None
                        if items:
                            item = items[0]
                            if isinstance(item, dict):
                                content = item.get("content", item)
                            else:
                                content = str(item)[:2000]
                        # 发送原始 dict, 前端 formatAgentContent() 会渲染为可读 HTML
                        yield {"event": "message", "data": json.dumps({
                            "type": "agent_output",
                            "agent": key,
                            "label": label,
                            "content": content,
                        }, ensure_ascii=False)}
                    elif node_name == "report" or node_name == "__end__":
                        pass  # handled below

            # 发送最终报告
            report = final_state.get("response") or final_state.get("final_report") or ""
            if not report:
                # 聚合各 Agent 产出为简单报告
                parts = []
                for key, label in AGENT_LABELS.items():
                    items = final_state.get(AGENT_OUTPUT_KEYS[key]) or []
                    if items:
                        parts.append(f"## {label}\n\n{str(items[0].get('content', items[0]))[:500]}")
                report = "\n\n".join(parts) if parts else "学习资源生成完成，请查看各 Agent 产出。"
            yield {"event": "message", "data": json.dumps({"type": "report", "content": report}, ensure_ascii=False)}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
        except Exception as exc:
            logger.exception(f"[edu] learn failed: {exc}")
            yield {"event": "message", "data": json.dumps({"type": "error", "content": str(exc)}, ensure_ascii=False)}

    return EventSourceResponse(event_stream())


@router.post("/profile", summary="对话式学习画像构建 (6+ 维度)")
async def build_profile(req: ProfileRequest) -> dict[str, Any]:
    """通过对话自动构建至少 6 维度的学生画像。"""
    try:
        from app.agents.education.profile_agent import run_profile_agent
        state: EducationState = {
            "input": f"专业:{req.major} 年级:{req.grade} {req.query}",
            "student_id": req.student_id,
            "profiles": [],
        }
        result = await run_profile_agent(state)
        profiles = result.get("profiles") or []
        return {"code": "SUCCESS", "data": {
            "profile": profiles[0].get("content") if profiles else {},
            "dimensions": profiles[0].get("content", {}).get("dimension_count", 8) if profiles else 0,
        }}
    except Exception as exc:
        logger.exception(f"[edu] profile build failed: {exc}")
        raise HTTPException(500, f"画像构建失败: {exc}")


@router.post("/quiz", summary="生成个性化练习题")
async def generate_quiz(req: EducationRequest) -> dict[str, Any]:
    """根据学生画像和课程内容生成练习题（选择/填空/简答）。"""
    try:
        from app.agents.education.resource_agent import run_resource_agent
        state: EducationState = {
            "input": req.query,
            "resource_plan": {"resource_types": ["quiz"], "agents": ["resource_agent"], "strategy": "quiz_only"},
            "resources": [],
        }
        result = await run_resource_agent(state)
        resources = result.get("resources") or []
        quiz_resources = [r for r in resources if r.get("type") == "quiz" or
                          (isinstance(r.get("content"), dict) and r["content"].get("resource_type") == "quiz")]
        return {"code": "SUCCESS", "data": {"quizzes": [r.get("content") for r in quiz_resources]}}
    except Exception as exc:
        raise HTTPException(500, f"题库生成失败: {exc}")


@router.post("/tutor", summary="智能辅导答疑")
async def tutor_ask(req: EducationRequest) -> dict[str, Any]:
    """智能答疑：文字解答 + 图解 + 短视频讲解。"""
    try:
        from app.agents.education.tutor_agent import run_tutor_agent
        state: EducationState = {"input": req.query, "tutor_responses": []}
        result = await run_tutor_agent(state)
        answers = result.get("tutor_responses") or []
        return {"code": "SUCCESS", "data": {"answer": answers[0].get("content") if answers else {}}}
    except Exception as exc:
        raise HTTPException(500, f"答疑失败: {exc}")


@router.post("/eval", summary="学习效果评估")
async def evaluate_learning(req: EducationRequest) -> dict[str, Any]:
    """多维度学习效果评估 + 动态调整建议。"""
    try:
        from app.agents.education.eval_agent import run_eval_agent
        state: EducationState = {"input": req.query, "evaluations": []}
        result = await run_eval_agent(state)
        evals = result.get("evaluations") or []
        return {"code": "SUCCESS", "data": {"evaluation": evals[0].get("content") if evals else {}}}
    except Exception as exc:
        raise HTTPException(500, f"评估失败: {exc}")
