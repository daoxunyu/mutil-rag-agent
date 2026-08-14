"""ResourceAgent - 多模态资源生成智能体。

核心能力:
  1. 生成 5+ 种类型的学习资源: 文档/PPT大纲/题库/视频脚本/代码案例/拓展阅读
  2. 根据学生画像适配资源难度和格式
  3. 多模态内容生成 (文本+代码+结构化数据)
"""

import json
from typing import Any, Dict, List

from loguru import logger

from app.agents.state_education import EducationState

_RESOURCE_TYPES = ["document", "ppt_outline", "quiz", "video_script", "code_example", "reading_material"]

_RESOURCE_PROMPT = """你是高校**多模态学习资源生成专家**。
根据课程内容和学生画像，生成符合高校教学场景的多种类型个性化学习资源。

**校园场景要素:**
- 考试导向: 期中考试/期末考试的常考题型
- 学分要求: 课程论文/实验报告的格式要求
- 实践教学: 实验课/课程设计的实操内容
- 复习阶段: 开学(预习)/期中(巩固)/期末(冲刺)

输出 JSON 数组, 每种资源类型一个对象:
[
  {
    "resource_type": "document|ppt_outline|quiz|video_script|code_example|reading_material|exam_review|lab_guide",
    "title": "资源标题",
    "difficulty": "入门/基础/进阶/高级",
    "estimated_time_minutes": 数字,
    "content": {资源类型对应的结构化内容},
    "format": "markdown|json|code",
    "tags": ["标签1", "标签2"],
    "learning_objectives": ["目标1"],
    "exam_relevance": "高/中/低"
  }
]

资源类型详细要求:
- document: 详细课程讲解 Markdown (含概念/示例/图表/公式)
- ppt_outline: 幻灯片大纲 (标题/要点/备注)
- quiz: 练习题 (单选/多选/填空/简答, 含答案和解析)
- video_script: 教学视频脚本 (分镜头/讲解词/时长)
- code_example: 代码实操案例 (完整可运行代码+注释)
- reading_material: 拓展阅读材料 (摘要/推荐理由/链接)
- exam_review: 期末复习资料 (重点总结/历年真题解析)
- lab_guide: 实验指导书 (实验目的/步骤/报告模板)
"""


async def run_resource_agent(state: EducationState) -> EducationState:
    """生成多模态学习资源 (5+ 种类型)。"""
    student_input = state.get("input") or ""
    profile = state.get("student_profile") or {}
    plan = state.get("resource_plan") or {}
    requested_types = plan.get("resource_types", list(_RESOURCE_TYPES))
    logger.info(f"[ResourceAgent] 生成资源, types={requested_types}")

    try:
        from app.core.llm import get_chat_llm

        llm = get_chat_llm(temperature=0.4)
        context = f"""学生画像: {json.dumps(profile, ensure_ascii=False)}
需生成的资源类型: {json.dumps(requested_types)}
学生请求: {student_input}

请为每种资源类型生成至少1个资源。重点题型要包含: 选择题、填空题、简答题。"""

        resp = await llm.ainvoke([
            ("system", _RESOURCE_PROMPT),
            ("human", context),
        ])
        raw = getattr(resp, "content", "") or ""
        resources = _parse_json_array(raw)
        if resources is None:
            logger.warning(f"[ResourceAgent] JSON解析失败, raw_len={len(raw)}, raw_preview={raw[:300]!r}")
            resources = _fallback_resources(student_input, requested_types)

        logger.info(f"[ResourceAgent] 生成完成, count={len(resources)}")
        return {
            "resources": [{
                "source": "resource_agent",
                "type": r.get("resource_type", "unknown"),
                "content": r,
                "metadata": {"agent": "resource_agent"},
            } for r in resources],
        }
    except Exception as exc:
        logger.exception(f"[ResourceAgent] 失败: {exc}")
        return {
            "resources": [{"source": "resource_agent", "type": "fallback",
                           "content": r, "metadata": {"agent": "resource_agent", "error_type": type(exc).__name__}}
                          for r in _fallback_resources(student_input, requested_types)],
        }


def _parse_json_array(raw: str) -> List[dict] | None:
    """多策略 JSON 数组解析，增强容错。"""
    if not raw or not raw.strip():
        return None
    raw = raw.strip()

    # 策略1: 直接解析整个字符串
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except Exception:
        pass

    # 策略2: 查找最外层的 [...] 或 {...}
    for left, right in [("[", "]"), ("{", "}")]:
        try:
            s = raw.find(left)
            # 从末尾开始找对应的右括号，避免嵌套问题
            depth = 0
            e = -1
            for i in range(s, len(raw)):
                if raw[i] in (left, "{" if left == "[" else "["):
                    depth += 1
                elif raw[i] in (right, "}" if left == "[" else "]"):
                    depth -= 1
                    if depth == 0:
                        e = i
                        break
            if s != -1 and e > s:
                data = json.loads(raw[s:e + 1])
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return [data]
        except Exception:
            continue

    # 策略3: 按 "resource_type" 分割，逐个解析对象
    try:
        results = []
        # 找所有 {...} 对，尝试解析
        i = 0
        while i < len(raw):
            if raw[i] == "{":
                depth = 0
                for j in range(i, len(raw)):
                    if raw[j] == "{":
                        depth += 1
                    elif raw[j] == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                obj = json.loads(raw[i:j + 1])
                                if isinstance(obj, dict) and "resource_type" in obj:
                                    results.append(obj)
                            except Exception:
                                pass
                            i = j
                            break
            i += 1
        if results:
            return results
    except Exception:
        pass

    return None


def _fallback_resources(topic: str, types: List[str]) -> List[dict]:
    """确定性兜底资源生成 — 确保即使 LLM 解析失败也有可用内容。"""
    import re
    # 提取简洁主题名
    short_topic = re.sub(r'^综合[：:]|^全面[：:]|帮我|分析|生成|梳理', '', topic).strip()[:50]
    resources = []
    for rt in types:
        if rt == "document":
            resources.append({
                "resource_type": "document", "title": f"{short_topic} - 学习文档",
                "difficulty": "基础", "estimated_time_minutes": 30,
                "content": {"markdown": (
                    f"# {short_topic}\n\n"
                    f"## 一、核心概念\n\n{short_topic}是机器学习中的重要基础。理解其核心概念对于后续学习至关重要。\n\n"
                    f"## 二、知识框架\n\n1. **基础理论**: 掌握基本定义和数学推导\n"
                    f"2. **核心算法**: 理解算法原理和适用场景\n"
                    f"3. **实践应用**: 能够使用Python实现并解决实际问题\n\n"
                    f"## 三、学习建议\n\n建议结合代码实践，每学完一个知识点后立即动手练习。"
                )},
                "format": "markdown", "tags": ["课程文档"],
            })
        elif rt == "quiz":
            resources.append({
                "resource_type": "quiz", "title": f"{short_topic} - 练习题库",
                "difficulty": "基础", "estimated_time_minutes": 20,
                "content": {"questions": [
                    {"type": "选择题", "question": f"{short_topic}的核心目标是什么？",
                     "options": ["A. 数据可视化", "B. 从数据中学习模式", "C. 数据库管理", "D. 网络通信"],
                     "answer": "B", "explanation": f"{short_topic}旨在从标注数据中学习映射关系。"},
                    {"type": "填空题", "question": f"{short_topic}中，用于评估模型性能的常用指标包括____和____。",
                     "answer": "准确率, F1分数", "explanation": "分类任务常用准确率、精确率、召回率、F1分数等指标。"},
                    {"type": "简答题", "question": f"请简述{short_topic}的基本工作流程。",
                     "reference_answer": f"1) 数据准备与预处理；2) 特征工程；3) 模型选择与训练；4) 模型评估与调优；5) 部署应用。",
                     "scoring_points": ["数据预处理步骤", "特征工程方法", "模型训练过程", "评估指标", "应用场景"]},
                ]}, "format": "json", "tags": ["练习"],
            })
        elif rt == "code_example":
            resources.append({
                "resource_type": "code_example", "title": f"{short_topic} - Python代码实操",
                "difficulty": "基础", "estimated_time_minutes": 30,
                "content": {"language": "python", "code": (
                    f"# {short_topic} - Python 代码示例\n"
                    f"import numpy as np\n"
                    f"from sklearn.model_selection import train_test_split\n"
                    f"from sklearn.metrics import accuracy_score, classification_report\n\n"
                    f"# 1. 准备数据 (示例)\n"
                    f"np.random.seed(42)\n"
                    f"X = np.random.randn(500, 5)  # 500个样本, 5个特征\n"
                    f"y = (X[:, 0] + X[:, 1] > 0).astype(int)  # 二分类标签\n\n"
                    f"# 2. 划分训练集和测试集\n"
                    f"X_train, X_test, y_train, y_test = train_test_split(\n"
                    f"    X, y, test_size=0.2, random_state=42\n"
                    f")\n\n"
                    f"# 3. 训练模型 (此处以基础模型为例, 实际应根据任务选择)\n"
                    f"# model = YourModel()\n"
                    f"# model.fit(X_train, y_train)\n\n"
                    f"# 4. 预测与评估\n"
                    f"# y_pred = model.predict(X_test)\n"
                    f"# print(f'准确率: {accuracy_score(y_test, y_pred):.2f}')\n"
                    f"# print(classification_report(y_test, y_pred))\n\n"
                    f"print(f'训练集大小: {X_train.shape}')\n"
                    f"print(f'测试集大小: {X_test.shape}')\n"
                    f"print('模型训练流程就绪, 请根据具体算法补全模型部分。')"
                ), "explanation": f"本代码展示了{short_topic}的完整工作流程: 数据准备→划分→训练→评估。"},
                "format": "code", "tags": ["编程实践"],
            })
        elif rt == "ppt_outline":
            resources.append({
                "resource_type": "ppt_outline", "title": f"{short_topic} - 教学课件",
                "difficulty": "基础", "estimated_time_minutes": 45,
                "content": {"slides": [
                    {"title": f"课程导入：{short_topic}概述", "points": ["学习目标", "为什么需要学习这个", "实际应用场景"]},
                    {"title": "核心概念与原理", "points": ["基本定义", "数学原理", "关键公式"]},
                    {"title": "算法详解", "points": ["算法流程", "优缺点分析", "适用场景"]},
                    {"title": "案例分析", "points": ["真实案例展示", "代码实现", "结果解读"]},
                    {"title": "总结与练习", "points": ["重点回顾", "课后习题", "拓展阅读推荐"]},
                ]}, "format": "json", "tags": ["课件"],
            })
        elif rt == "reading_material":
            resources.append({
                "resource_type": "reading_material", "title": f"{short_topic} - 拓展阅读",
                "difficulty": "基础", "estimated_time_minutes": 20,
                "content": {
                    "summary": f"围绕{short_topic}的进阶学习材料，帮助深入理解核心概念和最新发展。",
                    "references": [
                        {"title": "吴恩达《机器学习》课程", "url": "https://www.coursera.org/learn/machine-learning", "why": "最经典的机器学习入门课程"},
                        {"title": "李航《统计学习方法》", "url": "", "why": "中文经典教材，深入讲解监督学习算法"},
                        {"title": "Scikit-learn 官方文档", "url": "https://scikit-learn.org/", "why": "Python机器学习库的权威参考"},
                    ],
                },
                "format": "markdown", "tags": ["拓展阅读"],
            })
        elif rt == "video_script":
            resources.append({
                "resource_type": "video_script", "title": f"{short_topic} - 教学视频",
                "difficulty": "基础", "estimated_time_minutes": 15,
                "content": {"scenes": [
                    {"segment": "开场引入", "duration_sec": 60, "narration": f"大家好！今天我们来学习{short_topic}。这是机器学习中的重要基础内容，我会从概念到实践带你逐步掌握。"},
                    {"segment": "核心概念", "duration_sec": 300, "narration": f"首先我们来看{short_topic}的核心定义和数学原理...通过一个简单例子来理解：假设我们要预测..."},
                    {"segment": "代码演示", "duration_sec": 240, "narration": "现在让我们用Python来实现。打开Jupyter Notebook，跟着我一起写代码..."},
                    {"segment": "总结回顾", "duration_sec": 60, "narration": f"今天我们学习了{short_topic}的核心内容。课后请完成配套练习，下节课我们将继续深入学习。"},
                ]}, "format": "json", "tags": ["视频"],
            })
    return resources
