"""EvalAgent - 学习效果评估智能体。"""
import json
from loguru import logger
from app.agents.state_education import EducationState

_EVAL_PROMPT = """你是高校**学习效果评估专家**。评估学生当前学习效果，给出符合高校教学场景的多维度评价和改进建议。

**校园场景要素:**
- 学分达标: 评估是否达到课程学分要求
- 绩点预测: 根据学习情况预测期末绩点
- 考试准备: 判断是否为期中考试/期末考试做好准备
- 实践能力: 实验课/课程设计的完成质量
- 毕业要求: 是否满足专业培养方案要求

输出 JSON: {"overall_score": 0-100, "dimensions": [{"name": "维度名", "score": 0-100, "comment": "评价"}], "strengths": ["优势"], "weaknesses": ["需改进"], "next_focus": "下阶段重点", "study_tips": ["学习建议"], "gpa_prediction": 3.7, "exam_readiness": "充分/一般/不足", "credit_progress": {"completed": 86, "required": 140}}"""

async def run_eval_agent(state: EducationState) -> EducationState:
    profile = state.get("student_profile") or {}
    student_input = state.get("input") or ""
    logger.info(f"[EvalAgent] 评估: input={student_input[:80]!r}")
    try:
        from app.core.llm import get_chat_llm
        llm = get_chat_llm(temperature=0.1)
        ctx = f"学生画像: {json.dumps(profile, ensure_ascii=False)}\n学生输入: {student_input}"
        resp = await llm.ainvoke([("system", _EVAL_PROMPT), ("human", ctx)])
        raw = getattr(resp, "content", "") or ""
        s, e = raw.find("{"), raw.rfind("}")
        result = json.loads(raw[s:e+1]) if s != -1 and e > s else {"overall_score": 50, "dimensions": []}
    except Exception as exc:
        logger.exception(f"[EvalAgent] failed: {exc}")
        result = {"overall_score": 50, "dimensions": [], "error": str(exc)}
    return {"evaluations": [{"source": "eval_agent", "type": "evaluation_report", "content": result, "metadata": {"agent": "eval_agent"}}]}
