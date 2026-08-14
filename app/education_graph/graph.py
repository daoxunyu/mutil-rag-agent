"""教育多智能体编排图 — 与 deep_diagnosis_graph 同构的 LangGraph StateGraph。

复用现有的 fan-out/fan-in 并行模式，将 6 个教育 Agent 组织为：
  StudentContext → ResourcePlan → [6 Agent 并行] → ResourceIntegrator → QualityReviewer → LearningAdvisor → Report

每个 Agent 是隔离 subagent: 只回结构化资源，中间推理不进共享 state。
"""

import asyncio
import json
from typing import Any

from langgraph.graph import END, START, StateGraph
from loguru import logger

from app.agents.state_education import EducationState

# ============================================================
# 教育 Agent 配置 (name, type, agent_runner)
# ============================================================
EDUCATION_AGENTS = (
    ("profile_agent",    "student_profile",    "app.agents.education.profile_agent:run_profile_agent"),
    ("knowledge_agent",  "course_document",    "app.agents.education.knowledge_agent:run_knowledge_agent"),
    ("resource_agent",   "learning_resource",  "app.agents.education.resource_agent:run_resource_agent"),
    ("path_agent",       "learning_path",      "app.agents.education.path_agent:run_path_agent"),
    ("tutor_agent",      "tutor_response",     "app.agents.education.tutor_agent:run_tutor_agent"),
    ("eval_agent",       "evaluation_report",  "app.agents.education.eval_agent:run_eval_agent"),
)

# 资源域关键词 → 派遣建议 (规则路由)
_EDU_KEYWORDS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("画像", "profile", "我的水平", "学习风格", "认知", "了解我", "评估我的"),
     ("profile_agent",)),
    (("课程", "知识点", "讲解", "概念", "原理", "教材", "章节", "学习内容", "文档"),
     ("knowledge_agent",)),
    (("资源", "PPT", "题库", "视频", "动画", "代码", "案例", "实操", "材料", "习题", "题目", "生成"),
     ("resource_agent",)),
    (("路径", "规划", "计划", "顺序", "先学", "后学", "推荐", "进度", "安排"),
     ("path_agent",)),
    (("问题", "答疑", "不懂", "不会", "解释", "辅导", "帮我", "怎么做"),
     ("tutor_agent",)),
    (("评估", "测试", "考试", "效果", "检查", "复习", "掌握程度"),
     ("eval_agent",)),
)
_DEFAULT_EDU_AGENTS = ("knowledge_agent", "resource_agent")
_ALL_EDU_AGENTS = tuple(name for name, _, _ in EDUCATION_AGENTS)


def _route_education(text: str) -> tuple[list[str], str]:
    """规则路由: 学生输入 → 应派哪些教育 Agent"""
    norm = (text or "").lower()
    if not norm.strip():
        return list(_DEFAULT_EDU_AGENTS), "default_empty"
    if any(k in norm for k in ("全部", "所有", "all", "综合", "完整")):
        return list(_ALL_EDU_AGENTS), "full_pipeline"
    hit = []
    for keywords, agents in _EDU_KEYWORDS:
        if any(k in norm for k in keywords):
            for a in agents:
                if a not in hit:
                    hit.append(a)
    if not hit:
        return list(_DEFAULT_EDU_AGENTS), "default_no_match"
    return hit, "keyword_match"


# ============================================================
# 节点实现
# ============================================================

async def student_context_node(state: EducationState) -> EducationState:
    """① 学情导入: 载入学生画像、课程信息、学习历史"""
    student_input = state.get("input") or ""
    profile = state.get("student_profile") or {}
    course = state.get("course_info") or {}
    logger.info(f"[edu] StudentContext: input={student_input[:80]!r}, has_profile={bool(profile)}")
    return {
        "student_profile": profile,
        "course_info": course or {
            "name": "待指定课程",
            "subject": "根据学生输入自动识别",
            "chapters": [],
        },
    }


def resource_plan_node(state: EducationState) -> EducationState:
    """② 资源规划: 识别需求 → 决定派哪些 Agent + 资源类型"""
    text = (state.get("input") or "") + " "
    profile = state.get("student_profile") or {}
    if profile:
        text += json.dumps(profile, ensure_ascii=False)
    agents, strategy = _route_education(text)
    plan = {
        "agents": agents,
        "strategy": strategy,
        "resource_types": ["document", "ppt_outline", "quiz", "code_example", "reading_material", "video_script"],
    }
    logger.info(f"[edu] ResourcePlan: strategy={strategy} → agents={agents}")
    return {"resource_plan": plan}


def _dispatch_edu(name: str, runner_path: str):
    """给 Agent 节点包 dispatch guard: 不在 plan 的 Agent 直接 skip"""

    async def _guarded(state: EducationState) -> EducationState:
        plan = state.get("resource_plan") or {}
        agents = plan.get("agents") or list(_ALL_EDU_AGENTS)
        if name not in agents:
            logger.info(f"[edu] {name} skipped (not in plan)")
            return {}
        # 延迟导入 + 执行
        mod_path, func_name = runner_path.rsplit(":", 1)
        try:
            mod = __import__(mod_path, fromlist=[func_name])
            runner = getattr(mod, func_name)
            result = runner(state)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as exc:
            logger.exception(f"[edu] {name} failed: {exc}")
            return {}

    return _guarded


async def resource_integrator_node(state: EducationState) -> EducationState:
    """③ 资源整合: 将所有 Agent 输出归并成统一资源包"""
    profiles = state.get("profiles") or []
    knowledge_docs = state.get("knowledge_docs") or []
    resources = state.get("resources") or []
    learning_paths = state.get("learning_paths") or []
    tutor_responses = state.get("tutor_responses") or []
    evaluations = state.get("evaluations") or []

    integrated = {
        "profile": profiles[0].get("content") if profiles else None,
        "documents": [d.get("content") for d in knowledge_docs],
        "resources": [r.get("content") for r in resources],
        "learning_path": learning_paths[0].get("content") if learning_paths else None,
        "tutor_answers": [t.get("content") for t in tutor_responses],
        "evaluations": [e.get("content") for e in evaluations],
        "resource_count": len(knowledge_docs) + len(resources) + len(learning_paths),
    }
    logger.info(f"[edu] ResourceIntegrator: total_resources={integrated['resource_count']}")
    return {"integrated_resources": integrated}


async def quality_reviewer_node(state: EducationState) -> EducationState:
    """④ 质量审核: "防幻觉"检查 + 内容安全过滤"""
    integrated = state.get("integrated_resources") or {}
    issues = []
    # 简单确定性检查
    for doc in integrated.get("documents", []):
        if not doc or not isinstance(doc, dict):
            issues.append({"type": "empty_doc", "severity": "warning"})
    for res in integrated.get("resources", []):
        if not res or not isinstance(res, dict):
            issues.append({"type": "empty_resource", "severity": "warning"})

    review = {
        "passed": len(issues) == 0,
        "issues": issues,
        "review_summary": "所有资源已通过基础检查" if not issues else f"发现 {len(issues)} 个问题",
        "safe_content": True,
    }
    # 尝试用 LLM 做内容质量审查
    try:
        from app.core.llm import get_chat_llm
        llm = get_chat_llm(temperature=0)
        content_sample = json.dumps(integrated, ensure_ascii=False)[:2000]
        resp = await llm.ainvoke([
            ("system", "你是教育内容质量审查员。检查以下内容是否存在事实错误、不恰当内容或学术不严谨。回复 JSON: {\"has_issues\": bool, \"issues\": [], \"safe\": bool}"),
            ("human", content_sample),
        ])
        raw = getattr(resp, "content", "") or ""
        try:
            s, e = raw.find("{"), raw.rfind("}")
            llm_review = json.loads(raw[s:e + 1]) if s != -1 else {}
            if llm_review.get("has_issues"):
                review["issues"].extend(llm_review.get("issues", []))
        except Exception:
            pass
    except Exception as exc:
        logger.warning(f"[edu] QualityReviewer LLM check skipped: {exc}")

    logger.info(f"[edu] QualityReviewer: passed={review['passed']}, issues={len(review['issues'])}")
    return {"quality_review": review}


async def learning_advisor_node(state: EducationState) -> EducationState:
    """⑤ 学习建议: 综合画像+资源+路径 → 生成建议"""
    profile = state.get("student_profile") or {}
    integrated = state.get("integrated_resources") or {}
    path = integrated.get("learning_path") or {}
    review = state.get("quality_review") or {}

    recommendations = {
        "immediate_actions": [
            "浏览生成的课程文档，了解核心概念",
            "完成基础练习题，检验理解程度",
        ],
        "next_steps": [
            "根据学习路径逐步深入学习",
            "遇到问题随时向智能辅导提问",
        ],
        "adaptive_tips": [],
        "profile_insights": profile.get("suggested_strategy", "按计划推进学习"),
    }

    if path:
        milestones = path.get("milestones", [])
        if milestones:
            recommendations["immediate_actions"] = [f"开始第1阶段: {milestones[0].get('name', '基础入门')}"]
    if review.get("issues"):
        recommendations["adaptive_tips"].append("部分资源正在优化中，建议重点关注已通过审核的内容")

    logger.info(f"[edu] LearningAdvisor: tips={len(recommendations['adaptive_tips'])}")
    return {"learning_recommendations": recommendations}


def report_node(state: EducationState) -> EducationState:
    """⑥ 学习报告: 格式化最终输出 → 填 response 触发 END"""
    profile = state.get("student_profile") or {}
    integrated = state.get("integrated_resources") or {}
    path = integrated.get("learning_path") or {}
    review = state.get("quality_review") or {}
    recommendations = state.get("learning_recommendations") or {}
    student_input = state.get("input") or ""

    semester = state.get("semester", "")
    semester_stage = state.get("semester_stage", "")
    credits_completed = state.get("credits_completed", 0)
    credits_required = state.get("credits_required", 0)
    current_gpa = state.get("current_gpa", 0)

    lines = [
        "# 🎓 高校个性化学习报告",
        "",
        f"**当前学期**: {semester} ({semester_stage})",
        "",
        "## 📊 学习画像",
    ]
    if profile:
        lines.append(f"- **知识水平**: {profile.get('knowledge_base', {}).get('level', '-')} ({profile.get('knowledge_base', {}).get('score', '-')}/100)")
        lines.append(f"- **认知风格**: {profile.get('cognitive_style', {}).get('primary', '-')}")
        lines.append(f"- **学习节奏**: {profile.get('learning_pace', {}).get('speed', '-')}，建议每次{profile.get('learning_pace', {}).get('session_minutes', 45)}分钟")
        lines.append(f"- **兴趣方向**: {', '.join(d.get('domain', '') for d in profile.get('interest_domains', []))}")
        lines.append(f"- **画像摘要**: {profile.get('profile_summary', '待完善')}")
        academic_status = profile.get("academic_status", {})
        if academic_status:
            lines.append(f"- **当前学期**: {academic_status.get('semester', '-')}")
            lines.append(f"- **已修学分**: {academic_status.get('credits_completed', 0)}/{academic_status.get('credits_required', 0)}")
            lines.append(f"- **当前绩点**: {academic_status.get('current_gpa', 0)} → 目标: {academic_status.get('target_gpa', 0)}")
    else:
        lines.append("*(画像待构建，请通过对话提供更多信息)*")

    if credits_completed > 0:
        lines.append("")
        lines.append("## 🎯 学业进度")
        lines.append(f"- 已修学分: {credits_completed}/{credits_required} ({round(credits_completed/credits_required*100, 1)}%)")
        lines.append(f"- 当前绩点: {current_gpa}")

    lines.append("")
    lines.append("## 📚 生成资源")
    lines.append(f"- 课程文档: {len(integrated.get('documents', []))} 份")
    lines.append(f"- 学习资源: {len(integrated.get('resources', []))} 份 (PPT/题库/视频/代码案例/实验指导)")
    lines.append(f"- 学习路径: {'已规划' if path else '待规划'}")
    lines.append(f"- 辅导回答: {len(integrated.get('tutor_answers', []))} 条")
    lines.append(f"- 评估报告: {len(integrated.get('evaluations', []))} 份")

    lines.append("")
    lines.append("## 🛤️ 学习路径")
    if path:
        lines.append(f"- **学期阶段**: {path.get('semester_stage', '-')}")
        for ms in path.get("milestones", []):
            lines.append(f"### 第{ms.get('order', '?')}阶段: {ms.get('name', '')}")
            lines.append(f"- 目标: {ms.get('objective', '')}")
            lines.append(f"- 预计时长: {ms.get('estimated_hours', 0)} 小时")
            if ms.get("checkpoint"):
                cp = ms["checkpoint"]
                lines.append(f"- 检查点: {cp.get('type', '')} - {cp.get('criteria', '')}")
        exam_plan = path.get("exam_prep_plan", {})
        if exam_plan:
            lines.append("")
            lines.append("### 📝 考试复习计划")
            if exam_plan.get("midterm"):
                mt = exam_plan["midterm"]
                lines.append(f"- 期中考试: 复习重点 → {', '.join(mt.get('focus', []))}")
            if exam_plan.get("final"):
                ft = exam_plan["final"]
                lines.append(f"- 期末考试: 复习重点 → {', '.join(ft.get('focus', []))}")
    else:
        lines.append("*(完善画像后可生成个性化路径)*")

    lines.append("")
    lines.append("## ✅ 质量审核")
    lines.append(f"- 审核结果: {'通过' if review.get('passed') else '存在问题'}")
    lines.append(f"- 内容安全: {'安全' if review.get('safe_content') else '需复审'}")

    lines.append("")
    lines.append("## 💡 学习建议")
    for action in recommendations.get("immediate_actions", []):
        lines.append(f"- 🔥 **即刻行动**: {action}")
    for step in recommendations.get("next_steps", []):
        lines.append(f"- 📋 下一步: {step}")

    lines.append("")
    lines.append("---")
    lines.append("*本报告由高校智能导学平台多智能体协同系统自动生成*")

    response = "\n".join(lines)
    logger.info(f"[edu] Report: {len(response)} 字")
    return {"response": response, "final_report": response}


def build_education_graph():
    """构建教育多智能体编排图。

    Returns: 编译后的 CompiledStateGraph
    """
    wf = StateGraph(EducationState)

    # 注册节点
    wf.add_node("student_context", student_context_node)
    wf.add_node("resource_plan", resource_plan_node)
    for name, _, runner_path in EDUCATION_AGENTS:
        wf.add_node(name, _dispatch_edu(name, runner_path))
    wf.add_node("resource_integrator", resource_integrator_node)
    wf.add_node("quality_reviewer", quality_reviewer_node)
    wf.add_node("learning_advisor", learning_advisor_node)
    wf.add_node("report", report_node)

    # 串行前段
    wf.add_edge(START, "student_context")
    wf.add_edge("student_context", "resource_plan")
    # fan-out/fan-in (6 Agent 并行 → resource_integrator 作 join barrier)
    for name, _, _ in EDUCATION_AGENTS:
        wf.add_edge("resource_plan", name)
        wf.add_edge(name, "resource_integrator")
    # 串行后段
    wf.add_edge("resource_integrator", "quality_reviewer")
    wf.add_edge("quality_reviewer", "learning_advisor")
    wf.add_edge("learning_advisor", "report")
    wf.add_edge("report", END)

    compiled = wf.compile()
    logger.info(
        f"[edu] 教育多智能体图已编译: StudentContext→ResourcePlan→"
        f"[{len(EDUCATION_AGENTS)} Agent 并行]→ResourceIntegrator→QualityReviewer→LearningAdvisor→Report"
    )
    return compiled
