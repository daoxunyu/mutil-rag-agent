"""教育多智能体系统 - 个性化导学平台核心。

6 个专业 Agent 协同完成:
  1. ProfileAgent   - 对话式学习画像构建 (6+ 维度)
  2. KnowledgeAgent - 知识解析与课程内容生成
  3. ResourceAgent  - 多模态资源生成 (文档/PPT/题库/视频/代码案例)
  4. PathAgent      - 个性化学习路径规划
  5. TutorAgent     - 智能辅导与答疑
  6. EvalAgent      - 学习效果评估

架构: LangGraph 确定性编排 + 隔离 subagent 并行产资源
"""

from app.agents.education.profile_agent import run_profile_agent
from app.agents.education.knowledge_agent import run_knowledge_agent
from app.agents.education.resource_agent import run_resource_agent
from app.agents.education.path_agent import run_path_agent
from app.agents.education.tutor_agent import run_tutor_agent
from app.agents.education.eval_agent import run_eval_agent

__all__ = [
    "run_profile_agent",
    "run_knowledge_agent",
    "run_resource_agent",
    "run_path_agent",
    "run_tutor_agent",
    "run_eval_agent",
]
