"""ProfileAgent - 对话式学习画像构建智能体。

核心能力:
  1. 通过自然语言对话自动抽取学生特征
  2. 构建包含 6+ 维度的动态学生画像
  3. 支持画像随学随新 (增量更新)

画像维度:
  1. 知识基础 (knowledge_base)    - 专业基础知识掌握程度
  2. 认知风格 (cognitive_style)   - 视觉/听觉/动手/阅读偏好
  3. 学习目标 (learning_goals)     - 短期/中期/长期目标
  4. 易错点偏好 (weakness_pattern) - 常犯错误类型与薄弱环节
  5. 学习节奏 (learning_pace)      - 快/中/慢，单次学习时长偏好
  6. 兴趣方向 (interest_domain)    - 课程内偏好的子领域
  7. 前置知识 (prerequisites)      - 已修相关课程
  8. 资源偏好 (resource_preference) - 文档/视频/代码/互动偏好
"""

from __future__ import annotations

import json
from typing import Any, Dict

from loguru import logger

from app.agents.state_education import EducationState

_PROFILE_SYSTEM_PROMPT = """你是高校个性化导学平台的**学生画像构建专家**。
你的任务是通过与学生的自然语言对话,自动抽取并构建符合高校教学场景的多维学习画像。

**校园场景要素:**
- 学期制度: 秋季学期/春季学期, 开学/期中/期末阶段
- 学分体系: 必修课/选修课, 学分要求, 已修/待修学分
- 绩点系统: GPA计算, 目标绩点(保研/出国/毕业要求)
- 考试安排: 期中考试/期末考试/实验考核/课程论文
- 实践环节: 实验课/课程设计/实习/毕业设计
- 学业进度: 大一/大二/大三/大四, 专业分流/方向选择

输出一个严格的 JSON 对象,包含以下维度(每个维度给出0-100的数值评估和文字描述):

{
  "knowledge_base": {"score": 0-100, "level": "入门/基础/进阶/精通", "description": "..."},
  "cognitive_style": {"primary": "视觉/听觉/动手/阅读", "score": 0-100, "evidence": "..."},
  "learning_goals": {"short_term": "短期目标(如: 通过期中考试)", "mid_term": "中期目标(如: 本学期GPA达到3.5)", "long_term": "长期目标(如: 保研/就业/考研)", "clarity": 0-100},
  "weakness_patterns": [{"topic": "薄弱知识点", "error_type": "常犯错误类型", "frequency": "高/中/低"}],
  "learning_pace": {"speed": "快/中/慢", "session_minutes": 30, "evidence": "..."},
  "interest_domains": [{"domain": "感兴趣的专业方向", "enthusiasm": 0-100}],
  "prerequisites": [{"course": "已修课程名称", "mastery": 0-100}],
  "resource_preference": {"documents": 0-100, "videos": 0-100, "code": 0-100, "interactive": 0-100},
  "academic_status": {"semester": "当前学期(如: 大二下学期)", "credits_completed": 86, "credits_required": 140, "current_gpa": 3.7, "target_gpa": 3.8},
  "profile_summary": "一句话总结该学生的学习特征",
  "suggested_strategy": "针对该学生的教学建议(结合学期进度/考试安排)"
}

若某维度信息不足,标注 "needs_more_data": true 并用合理默认值。
"""


async def run_profile_agent(state: EducationState) -> EducationState:
    """构建/更新学生画像 (隔离 subagent, 只产出 profile 写入 state)。"""
    student_input = state.get("input") or ""
    existing_profile = state.get("student_profile") or {}
    logger.info(f"[ProfileAgent] 开始构建画像, input={student_input[:100]!r}")

    try:
        from app.core.llm import get_chat_llm

        llm = get_chat_llm(temperature=0.3)
        user_prompt = f"""基于以下学生信息和对话历史,构建学习画像:

当前已有画像: {json.dumps(existing_profile, ensure_ascii=False) if existing_profile else "(首次构建)"}

学生输入/对话: {student_input}

请输出完整的 JSON 画像对象。"""
        resp = await llm.ainvoke([
            ("system", _PROFILE_SYSTEM_PROMPT),
            ("human", user_prompt),
        ])
        raw = getattr(resp, "content", "") or ""

        # 解析 JSON
        profile = _parse_json(raw)
        if not profile:
            profile = _build_fallback_profile(student_input)

        profile["updated_at"] = ""  # 由调用方填充时间戳
        profile["dimension_count"] = len([k for k in profile if k not in ("profile_summary", "suggested_strategy", "updated_at", "dimension_count")])
        logger.info(f"[ProfileAgent] 画像构建完成, dimensions={profile.get('dimension_count')}")

        return {
            "profiles": [{
                "source": "profile_agent",
                "content": profile,
                "type": "student_profile",
                "metadata": {"agent": "profile_agent"},
            }],
            "student_profile": profile,
        }
    except Exception as exc:
        logger.exception(f"[ProfileAgent] 构建失败: {exc}")
        fallback = _build_fallback_profile(student_input)
        return {
            "profiles": [{"source": "profile_agent", "content": fallback, "type": "student_profile",
                          "metadata": {"agent": "profile_agent", "error_type": type(exc).__name__}}],
        }


def _parse_json(raw: str) -> dict | None:
    try:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            return json.loads(raw[s:e + 1])
    except Exception:
        pass
    return None


def _build_fallback_profile(student_input: str) -> dict:
    """LLM 不可用时的确定性兜底画像。"""
    # 简单的关键词匹配兜底
    text = (student_input or "").lower()
    return {
        "knowledge_base": {"score": 50, "level": "基础", "description": "待通过更多互动确认", "needs_more_data": True},
        "cognitive_style": {"primary": "视觉", "score": 50, "evidence": "根据基础偏好推测"},
        "learning_goals": {"short_term": "完成当前课程学习", "mid_term": "通过期末考试", "long_term": "掌握专业技能", "clarity": 30},
        "weakness_patterns": [{"topic": "待发现", "error_type": "未知", "frequency": "中"}],
        "learning_pace": {"speed": "中", "session_minutes": 45, "evidence": "默认推荐时长"},
        "interest_domains": [{"domain": "综合", "enthusiasm": 50}],
        "prerequisites": [],
        "resource_preference": {"documents": 70, "videos": 60, "code": 50, "interactive": 40},
        "profile_summary": "画像信息不足,建议进行更多对话互动以完善画像",
        "suggested_strategy": "先从基础知识摸底开始,逐步了解学生水平后调整教学策略",
        "needs_more_data": True,
    }
