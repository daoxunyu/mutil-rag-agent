"""PathAgent - 个性化学习路径规划智能体。

核心能力:
  1. 整合系统生成的所有个性化资源
  2. 结合学生画像分析最佳学习顺序
  3. 规划科学、动态的个性化学习路径
  4. 资源精准推送 (文档/视频/题库/代码案例)
"""

import json
from typing import Any, Dict, List

from loguru import logger

from app.agents.state_education import EducationState

_PATH_PROMPT = """你是高校**个性化学习路径规划专家**。
基于学生画像和已生成的资源，设计符合高校教学场景的科学合理学习路径。

**校园场景要素:**
- 学期日历: 开学/期中/期末时间节点
- 课程安排: 每周课时/上课时间
- 考试安排: 期中考试周/期末考试周
- 作业截止: 课程作业/实验报告提交日期
- 学业目标: 保研/考研/就业/出国的时间规划

输出 JSON:
{
  "path_name": "学习路径名称",
  "total_estimated_hours": 数字,
  "semester_stage": "开学阶段/期中阶段/期末阶段",
  "milestones": [
    {
      "order": 1, "name": "阶段名称", "objective": "阶段目标",
      "estimated_hours": 数字, "resources": ["资源ID或名称列表"],
      "checkpoint": {"type": "quiz/coding/review/exam", "criteria": "完成标准"}
    }
  ],
  "recommended_sequence": ["按顺序排列的资源列表"],
  "adaptive_rules": [
    {"if": "条件(如正确率<70%)", "then": "调整动作(如回顾前置知识)"}
  ],
  "weekly_schedule": [
    {"day": "周一", "resources": [...], "focus": "重点说明"},
    {"day": "周三", "resources": [...], "focus": "重点说明"}
  ],
  "exam_prep_plan": {
    "midterm": {"start_date": "...", "focus": ["重点1", "重点2"]},
    "final": {"start_date": "...", "focus": ["重点1", "重点2"]}
  },
  "motivation_tips": ["鼓励性提示语列表"]
}"""


async def run_path_agent(state: EducationState) -> EducationState:
    """规划个性化学习路径并推送资源。"""
    profile = state.get("student_profile") or {}
    resources = state.get("resources") or []
    knowledge_docs = state.get("knowledge_docs") or []
    student_input = state.get("input") or ""
    logger.info(f"[PathAgent] 规划路径, profile_level={profile.get('knowledge_base', {}).get('level', '?')}")

    try:
        from app.core.llm import get_chat_llm

        llm = get_chat_llm(temperature=0.2)
        resource_summary = [{
            "title": r.get("content", {}).get("title", ""),
            "type": r.get("content", {}).get("resource_type", ""),
            "difficulty": r.get("content", {}).get("difficulty", ""),
        } for r in resources[:20]]
        context = f"""学生画像: {json.dumps(profile, ensure_ascii=False)}
可用资源: {json.dumps(resource_summary, ensure_ascii=False)}
学生请求: {student_input}"""

        resp = await llm.ainvoke([
            ("system", _PATH_PROMPT),
            ("human", context),
        ])
        raw = getattr(resp, "content", "") or ""
        path = _parse_json(raw) or _fallback_path(student_input, resources)
        logger.info(f"[PathAgent] 路径规划完成, milestones={len(path.get('milestones', []))}")

        return {
            "learning_paths": [{
                "source": "path_agent", "type": "learning_path",
                "content": path, "metadata": {"agent": "path_agent"},
            }],
        }
    except Exception as exc:
        logger.exception(f"[PathAgent] 失败: {exc}")
        return {
            "learning_paths": [{"source": "path_agent", "type": "learning_path",
                               "content": _fallback_path(student_input, resources),
                               "metadata": {"agent": "path_agent", "error_type": type(exc).__name__}}],
        }


def _parse_json(raw: str) -> dict | None:
    try:
        s, e = raw.find("{"), raw.rfind("}")
        return json.loads(raw[s:e + 1]) if s != -1 and e > s else None
    except Exception:
        return None


def _fallback_path(topic: str, resources: List[dict]) -> dict:
    return {
        "path_name": f"{topic} 学习路径",
        "total_estimated_hours": 10,
        "milestones": [
            {"order": 1, "name": "基础入门", "objective": "掌握基本概念和理论",
             "estimated_hours": 3, "resources": ["课程文档", "PPT课件"],
             "checkpoint": {"type": "quiz", "criteria": "选择题正确率 > 70%"}},
            {"order": 2, "name": "深入理解", "objective": "理解核心原理和方法",
             "estimated_hours": 4, "resources": ["拓展阅读", "教学视频"],
             "checkpoint": {"type": "quiz", "criteria": "简答题得分 > 60%"}},
            {"order": 3, "name": "实践应用", "objective": "能够动手实践",
             "estimated_hours": 3, "resources": ["代码案例", "实操项目"],
             "checkpoint": {"type": "coding", "criteria": "代码可运行且通过测试"}},
        ],
        "recommended_sequence": ["先看文档→再看视频→做练习题→写代码"],
        "push_schedule": [{"day": 1, "resources": ["课程文档"], "focus": "概念理解"}],
        "motivation_tips": ["每天进步一点点，坚持就是胜利！"],
    }
