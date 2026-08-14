"""高校智能导学平台 - 教育多智能体共享状态。

设计原则:
  - 各 Agent 是"一次性、隔离上下文"的 subagent，只产出结构化资源/评估
  - Agent 之间通过 resources/evals 黑板交换数据，不互相聊天
  - 使用 LangGraph 的 Annotated[List, operator.add] reducer 实现并发安全归并

校园场景支持:
  - 学期制度: 秋季/春季学期, 开学/期中/期末阶段
  - 学分体系: 必修/选修, 已修/待修学分
  - 绩点系统: GPA计算, 目标绩点
  - 考试安排: 期中/期末/实验考核/课程论文
  - 实践环节: 实验课/课程设计/实习/毕业设计

Agent 分工:
  ProfileAgent  - 对话式学习画像构建 (含学业状态)
  KnowledgeAgent - 知识解析与课程内容生成
  ResourceAgent  - 多模态资源生成 (文档/PPT/题库/视频/代码/实验指导)
  PathAgent      - 个性化学习路径规划 (含考试复习计划)
  TutorAgent     - 智能辅导与答疑
  EvalAgent      - 学习效果评估 (含绩点预测)
"""

import operator
from typing import Annotated, Any, Dict, List, TypedDict


class EducationState(TypedDict, total=False):
    """教育多智能体编排图的共享状态。"""

    # ===== 输入 =====
    input: str                          # 学生输入/请求
    session_id: str                     # 会话ID
    student_id: str                     # 学生ID

    # ===== 校园上下文 =====
    semester: str                       # 当前学期 (如: 2026年春季学期)
    semester_stage: str                 # 学期阶段 (开学阶段/期中阶段/期末阶段)
    academic_year: str                  # 学年 (如: 2025-2026)
    student_major: str                  # 学生专业 (如: 计算机科学与技术)
    student_grade: str                  # 年级 (如: 大二)

    # ===== 学业状态 =====
    credits_completed: int              # 已修学分
    credits_required: int               # 毕业所需学分
    current_gpa: float                  # 当前绩点
    target_gpa: float                   # 目标绩点
    course_schedule: List[Dict[str, Any]]  # 课程表 [{course, time, location, teacher}]
    exam_dates: Dict[str, str]          # 考试安排 {"期中考试": "2026-11-15", "期末考试": "2026-01-10"}

    # ===== 学情上下文 (StudentContext 填) =====
    student_profile: Dict[str, Any]     # 学生画像 (含学业状态)
    course_info: Dict[str, Any]         # 课程信息 (含学分/考核方式)
    learning_history: List[Dict[str, Any]]  # 学习历史

    # ===== 资源规划 (ResourcePlan 填) =====
    resource_plan: Dict[str, Any]       # 资源生成计划 {agents, strategy, resource_types}

    # ===== 并行 Agent 输出 (operator.add = 并发安全) =====
    # ProfileAgent 输出: 学习画像
    profiles: Annotated[List[Dict[str, Any]], operator.add]
    # KnowledgeAgent 输出: 课程讲解文档/知识点
    knowledge_docs: Annotated[List[Dict[str, Any]], operator.add]
    # ResourceAgent 输出: 多模态资源 (PPT/题库/视频/代码案例/实验指导)
    resources: Annotated[List[Dict[str, Any]], operator.add]
    # PathAgent 输出: 学习路径 (含考试复习计划)
    learning_paths: Annotated[List[Dict[str, Any]], operator.add]
    # TutorAgent 输出: 答疑/辅导
    tutor_responses: Annotated[List[Dict[str, Any]], operator.add]
    # EvalAgent 输出: 评估报告 (含绩点预测)
    evaluations: Annotated[List[Dict[str, Any]], operator.add]

    # ===== 整合阶段 =====
    integrated_resources: List[Dict[str, Any]]  # 整合后的资源包
    quality_review: Dict[str, Any]              # 质量审核结果

    # ===== 输出 =====
    learning_recommendations: Dict[str, Any]    # 学习建议
    final_report: str                           # 最终报告/响应
    response: str                               # 触发 END 的响应
