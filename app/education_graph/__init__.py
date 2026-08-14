"""教育多智能体编排图。

与 app/diagnosis_graphs/ 的 AIOps 诊断图并列存在——两个独立图，
复用同一套 LangGraph 基础设施，各自解决不同场景。

教育图结构:
    [START]
       │
       ▼
  StudentContext        载入学生画像+课程信息
       │
       ▼
  ResourcePlan          识别资源需求 → 决定派哪几个专业 Agent
       │
   ┌───┼───────┬───────────┬──────────┐   ← fan-out (并行)
   ▼   ▼       ▼           ▼          ▼
 Profile Knowledge Resource  Path    Tutor      各 Agent 隔离运行，只回结构化资源
   └───┴───────┴───────────┴──────────┘   ← fan-in (join barrier)
       │
       ▼
  ResourceIntegrator    整合去重 → 统一资源包
       │
       ▼
  QualityReviewer       质量审核 ("防幻觉"检查)
       │
       ▼
  LearningAdvisor       生成学习建议+推送计划
       │
       ▼
  ReportAgent           格式化最终报告; 填 response 触发 [END]
"""

from app.education_graph.graph import build_education_graph

__all__ = ["build_education_graph"]
