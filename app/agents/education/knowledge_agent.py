"""KnowledgeAgent - 知识解析与课程内容生成智能体。

核心能力:
  1. 解析课程大纲，生成结构化知识点文档
  2. 根据学生画像适配内容深度和风格
  3. 生成课程讲解文档（含概念说明、示例、思维导图）
  4. 输出: 课程讲解文档、知识点思维导图
"""

import json
from typing import Any, Dict

from loguru import logger

from app.agents.state_education import EducationState

_KNOWLEDGE_PROMPT = """你是高校**知识解析与课程内容生成专家**。
你的任务是基于课程信息和学生画像，生成符合高校教学场景的高质量个性化课程讲解文档。

**校园场景要素:**
- 课程类型: 必修课/选修课/实验课/研讨课
- 学分设置: 2学分/3学分/4学分课程的内容深度要求
- 考核方式: 考试/考查/论文/答辩
- 学期进度: 开学阶段(基础概念)/期中阶段(深入理解)/期末阶段(综合复习)
- 专业培养方案: 课程在专业知识体系中的定位

输出 JSON:
{
  "topic": "知识点名称",
  "difficulty_level": "入门/基础/进阶/高级",
  "target_student_level": "适配的学生水平(如: 大二计算机专业)",
  "credit_hours": 3,
  "assessment_type": "考试/考查/论文/实验",
  "learning_objectives": ["目标1", "目标2", "目标3"],
  "key_concepts": [{"name": "概念名", "explanation": "解释", "example": "示例"}],
  "mind_map": {"root": "主题", "children": [{"name": "子主题1", "children": [...]}]},
  "content_markdown": "完整的课程讲解 Markdown 内容(含标题/正文/公式/代码块/图表)",
  "prerequisites": ["前置课程1", "前置课程2"],
  "estimated_study_minutes": 45,
  "related_courses": ["后续课程1", "相关选修课程"],
  "self_check_questions": ["自测题1", "自测题2"],
  "exam_focus": ["考试重点1", "考试重点2"]
}"""


async def run_knowledge_agent(state: EducationState) -> EducationState:
    """生成课程讲解文档与知识点梳理。"""
    student_input = state.get("input") or ""
    profile = state.get("student_profile") or {}
    course = state.get("course_info") or {}
    logger.info(f"[KnowledgeAgent] 开始知识解析, topic={student_input[:80]!r}")

    try:
        from app.core.llm import get_chat_llm

        llm = get_chat_llm(temperature=0.2)
        context = f"""课程信息: {json.dumps(course, ensure_ascii=False)}
学生水平: {profile.get('knowledge_base', {}).get('level', '基础')}
学习目标: {profile.get('learning_goals', {}).get('short_term', '掌握当前知识点')}
学生请求: {student_input}"""

        resp = await llm.ainvoke([
            ("system", _KNOWLEDGE_PROMPT),
            ("human", context),
        ])
        raw = getattr(resp, "content", "") or ""
        doc = _parse_json(raw) or _fallback_doc(student_input)

        logger.info(f"[KnowledgeAgent] 文档生成完成, topic={doc.get('topic', '-')}")
        return {
            "knowledge_docs": [{
                "source": "knowledge_agent",
                "type": "course_document",
                "content": doc,
                "metadata": {"agent": "knowledge_agent"},
            }],
        }
    except Exception as exc:
        logger.exception(f"[KnowledgeAgent] 失败: {exc}")
        return {
            "knowledge_docs": [{"source": "knowledge_agent", "type": "course_document",
                               "content": _fallback_doc(student_input),
                               "metadata": {"agent": "knowledge_agent", "error_type": type(exc).__name__}}],
        }


def _parse_json(raw: str) -> dict | None:
    try:
        s, e = raw.find("{"), raw.rfind("}")
        return json.loads(raw[s:e + 1]) if s != -1 and e > s else None
    except Exception:
        return None


def _fallback_doc(topic: str) -> dict:
    return {
        "topic": topic or "未指定主题",
        "difficulty_level": "基础",
        "learning_objectives": ["理解基本概念", "掌握核心原理", "能够应用实践"],
        "key_concepts": [],
        "mind_map": {"root": topic, "children": []},
        "content_markdown": f"# {topic}\n\n## 概述\n\n待生成详细内容...\n",
        "estimated_study_minutes": 30,
        "self_check_questions": ["请用自己的话描述核心概念"],
        "needs_llm_generation": True,
    }
