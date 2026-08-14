"""TutorAgent - 智能辅导与答疑智能体。"""
import json
from loguru import logger
from app.agents.state_education import EducationState

_TUTOR_PROMPT = """你是高校**智能辅导答疑专家**。当学生遇到学习问题时，提供符合高校教学场景的即时多模态解答。

**校园场景要素:**
- 课程答疑: 结合课程大纲和教材内容进行解答
- 作业辅导: 指导作业思路但不直接给出答案
- 考试复习: 重点讲解考试常考知识点
- 实验指导: 帮助理解实验原理和操作步骤

输出 JSON: {"answer_markdown": "详细解答(Markdown)", "diagram_description": "图解说明", "video_summary": "短视频讲解要点", "related_topics": ["关联知识点"], "follow_up_questions": ["建议追问"], "course_context": "课程背景说明", "exam_relevance": "考试相关性(高/中/低)"}"""

async def run_tutor_agent(state: EducationState) -> EducationState:
    student_input = state.get("input") or ""
    logger.info(f"[TutorAgent] 答疑: {student_input[:80]!r}")
    try:
        from app.core.llm import get_chat_llm
        llm = get_chat_llm(temperature=0.2)
        resp = await llm.ainvoke([("system", _TUTOR_PROMPT), ("human", student_input)])
        raw = getattr(resp, "content", "") or ""
        s, e = raw.find("{"), raw.rfind("}")
        result = json.loads(raw[s:e+1]) if s != -1 and e > s else {"answer_markdown": raw}
    except Exception as exc:
        logger.exception(f"[TutorAgent] failed: {exc}")
        result = {"answer_markdown": f"关于您的问题，建议从基础概念入手学习...", "error": str(exc)}
    return {"tutor_responses": [{"source": "tutor_agent", "type": "tutor_response", "content": result, "metadata": {"agent": "tutor_agent"}}]}
