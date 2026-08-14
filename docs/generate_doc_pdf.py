"""
Generate project documentation PDF.
Evaluation criteria: Feature Implementation (45%) + Documentation Richness (10%)
All SVGs use explicit polygon arrows — WeasyPrint compatible.
HTML template read from external file.
"""

import base64
import math
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = PROJECT_ROOT / "docs" / "Multi-Agent-RAG-Platform-项目说明文档.pdf"

intro_png = PROJECT_ROOT / "intro.png"
INTRO_BASE64 = ""
if intro_png.exists():
    with open(intro_png, "rb") as f:
        INTRO_BASE64 = base64.b64encode(f.read()).decode()


def arrow(x1, y1, x2, y2, color="#667eea", sw=2, aw=7, ah=5):
    """Explicit arrow: line + polygon arrowhead. WeasyPrint compatible."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 0.001:
        return ""
    ux, uy = dx / length, dy / length
    px, py = x2 - aw * ux, y2 - aw * uy
    nx, ny = -uy, ux
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{sw}"/>'
        f'<polygon points="{x2},{y2} {px+ah*nx},{py+ah*ny} {px-ah*nx},{py-ah*ny}" '
        f'fill="{color}"/>'
    )


A = arrow


def svg_arch_overview():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 620" width="880" height="590">
<defs>
  <linearGradient id="gH" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#667eea"/><stop offset="100%" stop-color="#764ba2"/></linearGradient>
  <linearGradient id="gC" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#3b82f6"/></linearGradient>
  <filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.12"/></filter>
</defs>
<rect x="260" y="8" width="400" height="48" rx="10" fill="url(#gH)" filter="url(#sh)"/>
<text x="460" y="37" text-anchor="middle" fill="white" font-family="SimHei" font-size="15" font-weight="bold">Web Frontend SPA (SSE Streaming)</text>
{A(460,56,460,86,"#667eea")}
<rect x="210" y="90" width="500" height="55" rx="10" fill="#3b82f6" filter="url(#sh)"/>
<text x="460" y="113" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">FastAPI Server (:9900) - SSE / REST / Webhook</text>
<text x="460" y="132" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="10">AIOps Diagnosis | RAG Chat | Education Learn | Queue API | Alert Webhook</text>
{A(270,145,270,195,"#667eea")}{A(370,145,370,195,"#667eea")}{A(470,145,470,195,"#667eea")}{A(570,145,570,195,"#667eea")}{A(670,145,670,195,"#667eea")}
<rect x="180" y="200" width="180" height="46" rx="8" fill="#8b5cf6" filter="url(#sh)"/>
<text x="270" y="222" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">Worker 1</text>
<text x="270" y="238" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">Diagnosis Consumer</text>
<rect x="370" y="200" width="180" height="46" rx="8" fill="#8b5cf6" filter="url(#sh)"/>
<text x="460" y="222" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">Worker 2</text>
<text x="460" y="238" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">Diagnosis Consumer</text>
<rect x="560" y="200" width="180" height="46" rx="8" fill="#8b5cf6" filter="url(#sh)"/>
<text x="650" y="222" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">Worker 3</text>
<text x="650" y="238" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">Diagnosis Consumer</text>
{A(270,246,270,280,"#667eea")}{A(460,246,460,280,"#667eea")}{A(650,246,650,280,"#667eea")}
<rect x="240" y="284" width="440" height="52" rx="10" fill="url(#gC)" filter="url(#sh)"/>
<text x="460" y="307" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">Diagnosis Runner (Unified Execution Engine)</text>
<text x="460" y="325" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">Skill Router -> Planner -> Executor -> Replanner</text>
{A(290,336,290,375,"#667eea")}{A(630,336,630,375,"#667eea")}
<rect x="140" y="380" width="290" height="58" rx="10" fill="#06b6d4" filter="url(#sh)"/>
<text x="285" y="403" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">fast: Plan-Execute-Replan</text>
<text x="285" y="422" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">Single Agent Loop - Quick Diagnosis</text>
<text x="285" y="434" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="8">Skill Router + 4-Step Loop + SSE Report</text>
<rect x="490" y="380" width="290" height="58" rx="10" fill="#0e7490" filter="url(#sh)"/>
<text x="635" y="403" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">deep: Evidence Graph</text>
<text x="635" y="422" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">6 Agent fan-out parallel evidence + RCA</text>
<text x="635" y="434" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="8">IncidentMgr+Correlation+EvidencePlan+4Evidence+RCA</text>
{A(285,438,285,480,"#667eea")}{A(635,438,635,480,"#667eea")}
<rect x="28" y="484" width="155" height="42" rx="6" fill="#475569" filter="url(#sh)"/>
<text x="105" y="510" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">Milvus Vector DB</text>
<rect x="198" y="484" width="125" height="42" rx="6" fill="#475569" filter="url(#sh)"/>
<text x="260" y="510" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">PostgreSQL</text>
<rect x="338" y="484" width="125" height="42" rx="6" fill="#475569" filter="url(#sh)"/>
<text x="400" y="510" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">Redis Streams</text>
<rect x="478" y="484" width="145" height="42" rx="6" fill="#475569" filter="url(#sh)"/>
<text x="550" y="510" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">MCP Tools x5</text>
<rect x="638" y="484" width="140" height="42" rx="6" fill="#475569" filter="url(#sh)"/>
<text x="708" y="510" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">LLM Wiki</text>
<rect x="793" y="484" width="112" height="42" rx="6" fill="#475569" filter="url(#sh)"/>
<text x="849" y="510" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">WebSearch</text>
<rect x="30" y="550" width="14" height="14" rx="3" fill="url(#gH)"/><text x="50" y="562" font-size="10" fill="#666">Frontend</text>
<rect x="110" y="550" width="14" height="14" rx="3" fill="#3b82f6"/><text x="130" y="562" font-size="10" fill="#666">API</text>
<rect x="185" y="550" width="14" height="14" rx="3" fill="#8b5cf6"/><text x="205" y="562" font-size="10" fill="#666">Worker</text>
<rect x="280" y="550" width="14" height="14" rx="3" fill="url(#gC)"/><text x="300" y="562" font-size="10" fill="#666">Engine</text>
<rect x="355" y="550" width="14" height="14" rx="3" fill="#06b6d4"/><text x="375" y="562" font-size="10" fill="#666">Fast</text>
<rect x="440" y="550" width="14" height="14" rx="3" fill="#0e7490"/><text x="460" y="562" font-size="10" fill="#666">Deep</text>
<rect x="535" y="550" width="14" height="14" rx="3" fill="#475569"/><text x="555" y="562" font-size="10" fill="#666">Infra</text>
</svg>"""


def svg_education_fanout():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 500" width="860" height="480">
<defs><filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.08"/></filter></defs>
<rect x="310" y="8" width="280" height="42" rx="21" fill="#667eea" filter="url(#sh)"/>
<text x="450" y="34" text-anchor="middle" fill="white" font-family="SimHei" font-size="14" font-weight="bold">Student Input (Learning Request)</text>
{A(450,50,450,78,"#667eea")}
<rect x="295" y="82" width="310" height="40" rx="8" fill="#3b82f6" filter="url(#sh)"/>
<text x="450" y="107" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">ResourcePlan: Identify Needs -> Dispatch Agents</text>
{A(180,122,180,168,"#667eea")}{A(315,122,315,168,"#667eea")}{A(450,122,450,168,"#667eea")}{A(585,122,585,168,"#667eea")}{A(720,122,720,168,"#667eea")}
<rect x="50" y="173" width="255" height="72" rx="10" fill="#ec4899" filter="url(#sh)"/>
<text x="177" y="198" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">ProfileAgent</text>
<text x="177" y="216" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">Student Profile: 8-dim assessment</text>
<text x="177" y="232" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="9">Knowledge/Cognitive/Goals/Weakness/Pace/Interests/Prereq/Preference</text>
<rect x="318" y="173" width="255" height="72" rx="10" fill="#f59e0b" filter="url(#sh)"/>
<text x="445" y="198" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">KnowledgeAgent</text>
<text x="445" y="216" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">Knowledge Parsing + RAG Retrieval</text>
<text x="445" y="232" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="9">Knowledge tree + prerequisites + advanced + references</text>
<rect x="586" y="173" width="255" height="72" rx="10" fill="#10b981" filter="url(#sh)"/>
<text x="713" y="198" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">ResourceAgent</text>
<text x="713" y="216" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">8-Type Resource Generation</text>
<text x="713" y="232" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="9">Doc/PPT/Quiz/Video/Code/Interactive/Lab/Project</text>
<rect x="120" y="260" width="255" height="62" rx="10" fill="#8b5cf6" filter="url(#sh)"/>
<text x="247" y="284" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">PathAgent</text>
<text x="247" y="302" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">Learning Path: Weekly Plan + Milestones</text>
<text x="247" y="316" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="9">Staged path + time estimates + dependency chains</text>
<rect x="398" y="260" width="255" height="62" rx="10" fill="#ef4444" filter="url(#sh)"/>
<text x="525" y="284" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">TutorAgent</text>
<text x="525" y="302" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">Smart Tutoring: Multi-turn Q&A</text>
<text x="525" y="316" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="9">Concept explain + homework + exam prep + error analysis</text>
<rect x="676" y="260" width="200" height="62" rx="10" fill="#14b8a6" filter="url(#sh)"/>
<text x="776" y="284" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">EvalAgent</text>
<text x="776" y="302" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="10">Learning Evaluation</text>
<text x="776" y="316" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="9">Mastery + weaknesses + GPA prediction</text>
{A(177,245,177,280,"#667eea",1.5)}{A(445,245,445,280,"#667eea",1.5)}{A(713,245,713,280,"#667eea",1.5)}
<line x1="177" y1="322" x2="177" y2="350" stroke="#667eea" stroke-width="1.5"/>
<line x1="445" y1="322" x2="445" y2="350" stroke="#667eea" stroke-width="1.5"/>
<line x1="713" y1="322" x2="713" y2="350" stroke="#667eea" stroke-width="1.5"/>
<line x1="776" y1="322" x2="776" y2="350" stroke="#667eea" stroke-width="1.5"/>
<line x1="177" y1="350" x2="776" y2="350" stroke="#667eea" stroke-width="2"/>
{A(450,350,450,385,"#667eea")}
<rect x="295" y="390" width="310" height="40" rx="8" fill="#8b5cf6" filter="url(#sh)"/>
<text x="450" y="415" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">ResourceIntegrator (dedup + merge) -> QualityReviewer</text>
{A(450,430,450,458,"#667eea")}
<rect x="220" y="462" width="460" height="34" rx="17" fill="#667eea" filter="url(#sh)"/>
<text x="450" y="484" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">LearningAdvisor + ReportAgent -> Complete Learning Plan</text>
</svg>"""


def svg_rag_pipeline():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 340" width="890" height="330">
<defs><filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.06"/></filter></defs>
<rect x="15" y="25" width="150" height="38" rx="19" fill="#06b6d4" filter="url(#sh)"/>
<text x="90" y="49" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">User Query</text>
{A(165,44,200,44,"#06b6d4")}
<rect x="205" y="10" width="210" height="68" rx="10" fill="#f0fdf4" stroke="#10b981" stroke-width="1.5" filter="url(#sh)"/>
<text x="310" y="33" text-anchor="middle" fill="#065f46" font-family="SimHei" font-size="11" font-weight="bold">Parent-Child Chunking</text>
<text x="310" y="49" text-anchor="middle" fill="#065f46" font-size="9">Parent: 800 chars large context window</text>
<text x="310" y="63" text-anchor="middle" fill="#065f46" font-size="9">Child: semantically complete small chunks</text>
{A(415,44,455,44,"#06b6d4")}
<rect x="460" y="8" width="195" height="70" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5" filter="url(#sh)"/>
<text x="557" y="30" text-anchor="middle" fill="#1e40af" font-family="SimHei" font-size="11" font-weight="bold">Vector Dense Search</text>
<text x="557" y="47" text-anchor="middle" fill="#1e40af" font-size="9">BGE-M3 Embedding (1024d)</text>
<text x="557" y="61" text-anchor="middle" fill="#1e40af" font-size="9">Milvus FLAT/IP index</text>
<text x="557" y="74" text-anchor="middle" fill="#1e40af" font-size="9">Recall Top-30 candidates</text>
{A(655,44,690,44,"#06b6d4")}
<rect x="695" y="10" width="210" height="68" rx="10" fill="#fdf4ff" stroke="#a855f7" stroke-width="1.5" filter="url(#sh)"/>
<text x="800" y="33" text-anchor="middle" fill="#6b21a8" font-family="SimHei" font-size="11" font-weight="bold">RRF Fusion Ranking</text>
<text x="800" y="49" text-anchor="middle" fill="#6b21a8" font-size="9">Reciprocal Rank Fusion</text>
<text x="800" y="63" text-anchor="middle" fill="#6b21a8" font-size="9">Vector(0.6) + BM25(0.4)</text>
<text x="800" y="75" text-anchor="middle" fill="#6b21a8" font-size="9">Weighted merge -> Top-15</text>
<rect x="460" y="100" width="195" height="52" rx="10" fill="#fff7ed" stroke="#f97316" stroke-width="1.5" filter="url(#sh)"/>
<text x="557" y="120" text-anchor="middle" fill="#9a3412" font-family="SimHei" font-size="11" font-weight="bold">BM25 Sparse Search</text>
<text x="557" y="136" text-anchor="middle" fill="#9a3412" font-size="9">jieba tokenize + TF-IDF keywords</text>
<text x="557" y="149" text-anchor="middle" fill="#9a3412" font-size="9">Exact char match - Weight 0.4</text>
<line x1="655" y1="126" x2="655" y2="44" stroke="#06b6d4" stroke-width="1.5" stroke-dasharray="5,3"/>
{A(655,44,690,44,"#06b6d4")}
{A(800,78,800,108,"#a855f7")}
<line x1="800" y1="78" x2="800" y2="175" stroke="#a855f7" stroke-width="2"/>
{A(800,175,720,175,"#a855f7")}
<rect x="460" y="175" width="250" height="58" rx="10" fill="#f5f3ff" stroke="#8b5cf6" stroke-width="1.5" filter="url(#sh)"/>
<text x="585" y="197" text-anchor="middle" fill="#5b21b6" font-family="SimHei" font-size="11" font-weight="bold">Local Rerank (Cross-Encoder)</text>
<text x="585" y="213" text-anchor="middle" fill="#5b21b6" font-size="9">BGE-Reranker-v2-m3</text>
<text x="585" y="228" text-anchor="middle" fill="#5b21b6" font-size="9">query-doc semantic pair scoring -> Top-3</text>
<line x1="710" y1="204" x2="735" y2="204" stroke="#8b5cf6" stroke-width="2"/>
<line x1="735" y1="204" x2="735" y2="130" stroke="#8b5cf6" stroke-width="2"/>
{A(735,130,698,130,"#8b5cf6")}
<rect x="695" y="108" width="210" height="48" rx="10" fill="#475569" filter="url(#sh)"/>
<text x="800" y="129" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">LLM Generation (Chat Model)</text>
<text x="800" y="147" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">System Prompt + Context + Query</text>
{A(800,156,800,195,"#475569")}
<rect x="695" y="200" width="210" height="38" rx="19" fill="#06b6d4" filter="url(#sh)"/>
<text x="800" y="224" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">Streaming Answer (SSE)</text>
<rect x="15" y="105" width="150" height="36" rx="18" fill="#cbd5e1" filter="url(#sh)"/>
<text x="90" y="127" text-anchor="middle" fill="#475569" font-family="SimHei" font-size="11" font-weight="bold">Document Upload</text>
{A(90,141,90,171,"#94a3b8")}
<rect x="15" y="175" width="150" height="42" rx="8" fill="#94a3b8" filter="url(#sh)"/>
<text x="90" y="196" text-anchor="middle" fill="white" font-family="SimHei" font-size="10">Parent-Child Split</text>
<text x="90" y="210" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">BGE-M3 embedding -> Milvus</text>
{A(165,196,202,44,"#94a3b8")}
<rect x="15" y="245" width="150" height="48" rx="8" fill="#e2e8f0" filter="url(#sh)"/>
<text x="90" y="266" text-anchor="middle" fill="#475569" font-family="SimHei" font-size="10" font-weight="bold">Chat Memory (Redis)</text>
<text x="90" y="281" text-anchor="middle" fill="#64748b" font-size="9">Last 3 turns - TTL 7 days</text>
{A(165,269,460,269,"#94a3b8",1.5)}
<text x="230" y="285" font-size="9" fill="#94a3b8">Merge last 3 conversation turns</text>
</svg>"""


def svg_deep_evidence():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 500" width="860" height="480">
<defs><filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.1"/></filter></defs>
<rect x="300" y="6" width="300" height="40" rx="20" fill="#ef4444" filter="url(#sh)"/>
<text x="450" y="32" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">Alert / Manual / Webhook Trigger</text>
{A(450,46,450,74,"#ef4444")}
<rect x="310" y="78" width="280" height="40" rx="8" fill="#f97316" filter="url(#sh)"/>
<text x="450" y="103" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">IncidentManager: Create + Dedup</text>
{A(450,118,450,144,"#ef4444")}
<rect x="290" y="148" width="320" height="40" rx="8" fill="#f59e0b" filter="url(#sh)"/>
<text x="450" y="173" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">CorrelationContext: Time-window Analysis</text>
{A(450,188,450,214,"#ef4444")}
<rect x="290" y="218" width="320" height="40" rx="8" fill="#fbbf24" filter="url(#sh)"/>
<text x="450" y="243" text-anchor="middle" fill="#1c1917" font-family="SimHei" font-size="12" font-weight="bold">EvidencePlan: Hypothesis-based Evidence Plan</text>
{A(160,258,160,298,"#ef4444")}{A(305,258,305,298,"#ef4444")}{A(450,258,450,298,"#ef4444")}{A(595,258,595,298,"#ef4444")}{A(740,258,740,298,"#ef4444")}
<rect x="35" y="303" width="240" height="70" rx="10" fill="#dc2626" filter="url(#sh)"/>
<text x="155" y="325" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">MetricAgent</text>
<text x="155" y="343" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">PromQL / Log queries</text>
<text x="155" y="358" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="8">Time-series anomaly / baseline deviation</text>
<text x="155" y="370" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="7">-> Structured metric snapshot + anomaly tags</text>
<rect x="290" y="303" width="240" height="70" rx="10" fill="#dc2626" filter="url(#sh)"/>
<text x="410" y="325" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">LogAgent</text>
<text x="410" y="343" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">App / System / Audit log search</text>
<text x="410" y="358" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="8">Error pattern match / Stack aggregation</text>
<text x="410" y="370" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="7">-> Key log excerpts + event timeline</text>
<rect x="545" y="303" width="240" height="70" rx="10" fill="#dc2626" filter="url(#sh)"/>
<text x="665" y="325" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">InfraAgent</text>
<text x="665" y="343" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">K8s/Docker/Network topology check</text>
<text x="665" y="358" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="8">Pod status / Service / Ingress routing</text>
<text x="665" y="370" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="7">-> Infra status report + change records</text>
<rect x="800" y="303" width="85" height="70" rx="10" fill="#dc2626" filter="url(#sh)"/>
<text x="842" y="325" text-anchor="middle" fill="white" font-family="SimHei" font-size="11" font-weight="bold">Runbook</text>
<text x="842" y="343" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="8">SOP Search</text>
<text x="842" y="358" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="7">Match known</text>
<text x="842" y="370" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="7">procedures</text>
<line x1="155" y1="373" x2="155" y2="408" stroke="#ef4444" stroke-width="1.5"/>
<line x1="410" y1="373" x2="410" y2="408" stroke="#ef4444" stroke-width="1.5"/>
<line x1="665" y1="373" x2="665" y2="408" stroke="#ef4444" stroke-width="1.5"/>
<line x1="155" y1="408" x2="665" y2="408" stroke="#ef4444" stroke-width="2"/>
{A(450,408,450,435,"#ef4444")}
<rect x="290" y="438" width="320" height="40" rx="8" fill="#ef4444" filter="url(#sh)"/>
<text x="450" y="458" text-anchor="middle" fill="white" font-family="SimHei" font-size="12" font-weight="bold">EvidenceReducer -> RCAJudge -> ReportAgent</text>
<text x="450" y="474" text-anchor="middle" fill="rgba(255,255,255,0.75)" font-size="9">Merge evidence -> Conflict resolution -> Root cause -> Remediation -> Report</text>
</svg>"""


def svg_langgraph_state():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 420" width="800" height="400">
<defs><filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.1"/></filter></defs>
<rect x="350" y="5" width="120" height="36" rx="18" fill="#475569" filter="url(#sh)"/>
<text x="410" y="28" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">START</text>
{A(410,41,410,68,"#475569")}
<rect x="270" y="72" width="280" height="52" rx="10" fill="#3b82f6" filter="url(#sh)"/>
<text x="410" y="95" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">SkillRouter</text>
<text x="410" y="114" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="10">Match Skill + recall historical experience</text>
{A(410,124,410,155,"#3b82f6")}
<polygon points="410,160 520,200 410,240 300,200" fill="#fbbf24" filter="url(#sh)"/>
<text x="410" y="197" text-anchor="middle" fill="#1c1917" font-family="SimHei" font-size="11" font-weight="bold">Has</text>
<text x="410" y="212" text-anchor="middle" fill="#1c1917" font-family="SimHei" font-size="11" font-weight="bold">response?</text>
{A(520,200,580,200,"#10b981",2.5,8,6)}
<rect x="585" y="178" width="100" height="44" rx="18" fill="#10b981" filter="url(#sh)"/>
<text x="635" y="205" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">END</text>
<text x="548" y="170" font-size="10" fill="#10b981" font-weight="bold">Yes</text>
{A(410,240,410,275,"#ef4444",2.5,8,6)}
<text x="420" y="262" font-size="10" fill="#ef4444" font-weight="bold">No</text>
<rect x="270" y="280" width="280" height="52" rx="10" fill="#8b5cf6" filter="url(#sh)"/>
<text x="410" y="303" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">Planner</text>
<text x="410" y="322" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="10">Based on Skill Playbook, create 4-6 step plan</text>
{A(410,332,410,360,"#8b5cf6")}
<rect x="270" y="364" width="280" height="48" rx="10" fill="#06b6d4" filter="url(#sh)"/>
<text x="410" y="386" text-anchor="middle" fill="white" font-family="SimHei" font-size="13" font-weight="bold">Executor (fan-out parallel)</text>
<text x="410" y="403" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="10">Execute plan[0] via MCP tools, record in past_steps</text>
<path d="M270,388 L50,388 L50,200 L295,200" stroke="#06b6d4" stroke-width="2" fill="none"/>
{A(295,200,300,200,"#06b6d4")}
<text x="55" y="295" font-size="10" fill="#06b6d4" font-weight="bold">Replanner</text>
<text x="55" y="310" font-size="9" fill="#06b6d4">Evaluate progress:</text>
<text x="55" y="323" font-size="9" fill="#06b6d4">Done / Continue / Reroute</text>
<rect x="560" y="290" width="14" height="14" rx="3" fill="#3b82f6"/><text x="580" y="302" font-size="10" fill="#666">Router</text>
<rect x="640" y="290" width="14" height="14" rx="3" fill="#8b5cf6"/><text x="660" y="302" font-size="10" fill="#666">Plan</text>
<rect x="710" y="290" width="14" height="14" rx="3" fill="#06b6d4"/><text x="730" y="302" font-size="10" fill="#666">Execute</text>
<rect x="560" y="312" width="14" height="14" rx="3" fill="#10b981"/><text x="580" y="324" font-size="10" fill="#666">Done</text>
<rect x="640" y="312" width="14" height="14" rx="3" fill="#ef4444"/><text x="660" y="324" font-size="10" fill="#666">Continue</text>
</svg>"""


def svg_sequence_education():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 540" width="880" height="520">
<defs><filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.06"/></filter></defs>
<line x1="30" y1="30" x2="30" y2="510" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
<line x1="175" y1="30" x2="175" y2="510" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
<line x1="320" y1="30" x2="320" y2="510" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
<line x1="610" y1="30" x2="610" y2="510" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
<line x1="755" y1="30" x2="755" y2="510" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
<rect x="5" y="5" width="85" height="32" rx="6" fill="#667eea" filter="url(#sh)"/>
<text x="47" y="26" text-anchor="middle" fill="white" font-family="SimHei" font-size="10" font-weight="bold">User</text>
<rect x="125" y="5" width="100" height="32" rx="6" fill="#3b82f6" filter="url(#sh)"/>
<text x="175" y="26" text-anchor="middle" fill="white" font-family="SimHei" font-size="10" font-weight="bold">FastAPI</text>
<rect x="260" y="5" width="120" height="32" rx="6" fill="#06b6d4" filter="url(#sh)"/>
<text x="320" y="26" text-anchor="middle" fill="white" font-family="SimHei" font-size="10" font-weight="bold">ResourcePlan</text>
<rect x="510" y="5" width="200" height="32" rx="6" fill="#8b5cf6" filter="url(#sh)"/>
<text x="610" y="26" text-anchor="middle" fill="white" font-family="SimHei" font-size="10" font-weight="bold">6 Agents (parallel)</text>
<rect x="690" y="5" width="130" height="32" rx="6" fill="#10b981" filter="url(#sh)"/>
<text x="755" y="26" text-anchor="middle" fill="white" font-family="SimHei" font-size="10" font-weight="bold">Integrator</text>
<text x="80" y="65" font-size="10" fill="#64748b">1. POST /education/learn</text>
{A(175,55,320,55,"#667eea")}
<text x="260" y="95" font-size="10" fill="#64748b">2. Parse learning request</text>
{A(320,85,320,108,"#06b6d4")}
<text x="264" y="125" font-size="10" fill="#64748b">3. Decide which agents to dispatch</text>
<text x="440" y="155" font-size="10" fill="#64748b">4. fan-out: 6 agents in parallel</text>
{A(320,138,610,138,"#8b5cf6")}
<line x1="610" y1="138" x2="610" y2="178" stroke="#8b5cf6" stroke-width="2"/>
<text x="618" y="198" font-size="9" fill="#8b5cf6">ProfileAgent: student profile</text>
<text x="618" y="214" font-size="9" fill="#f59e0b">KnowledgeAgent: knowledge parsing+RAG</text>
<text x="618" y="230" font-size="9" fill="#10b981">ResourceAgent: 8-type resources</text>
<text x="618" y="246" font-size="9" fill="#8b5cf6">PathAgent: learning path</text>
<text x="618" y="262" font-size="9" fill="#ef4444">TutorAgent: smart tutoring</text>
<text x="618" y="278" font-size="9" fill="#14b8a6">EvalAgent: evaluation</text>
<line x1="610" y1="288" x2="610" y2="315" stroke="#8b5cf6" stroke-width="2"/>
<text x="680" y="335" font-size="10" fill="#64748b">5. Each agent returns structured result</text>
{A(610,322,755,322,"#8b5cf6")}
<text x="685" y="365" font-size="10" fill="#64748b">6. Dedup + quality review</text>
{A(755,352,755,378,"#10b981")}
<text x="685" y="398" font-size="10" fill="#64748b">7. Generate final learning plan</text>
{A(755,385,175,385,"#10b981")}
<text x="200" y="418" font-size="10" fill="#64748b">8. SSE streaming push</text>
{A(175,408,30,408,"#667eea")}
<text x="80" y="440" font-size="9" fill="#06b6d4">Push event when each agent completes</text>
<text x="80" y="456" font-size="9" fill="#06b6d4">User sees real-time progress</text>
</svg>"""


CSS = """
@page {
  size: A4;
  margin: 2.2cm 2cm 2.2cm 2cm;
  @bottom-center {
    content: "Page " counter(page);
    font-family: "SimHei", "Microsoft YaHei", sans-serif;
    font-size: 10px;
    color: #888;
  }
}
@page :first {
  @bottom-center { content: none; }
  margin: 0;
}
body {
  font-family: "SimSun", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  font-size: 12.5px;
  line-height: 1.8;
  color: #333;
}
.cover {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  page-break-after: always;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
}
.cover h1 { font-family: "SimHei", sans-serif; font-size: 40px; margin-bottom: 12px; letter-spacing: 3px; }
.cover .subtitle { font-family: "SimHei", sans-serif; font-size: 22px; opacity: 0.9; margin-bottom: 30px; }
.cover .meta { font-size: 14px; opacity: 0.8; margin-top: 40px; }
.cover .badges { margin-top: 20px; display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
.cover .badge {
  background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4);
  border-radius: 20px; padding: 6px 18px; font-size: 13px; font-family: "SimHei", sans-serif;
}
.cover .spec { margin-top: 30px; font-size: 14px; opacity: 0.85; }
.toc { page-break-after: always; }
.toc h2 { font-family: "SimHei", sans-serif; font-size: 26px; border-bottom: 3px solid #667eea; padding-bottom: 8px; margin-bottom: 24px; }
.toc ul { list-style: none; padding: 0; }
.toc li { margin: 7px 0; font-size: 14px; }
.toc li a { color: #333; text-decoration: none; display: flex; justify-content: space-between; border-bottom: 1px dotted #ccc; padding: 4px 0; }
.toc li a::after { content: target-counter(attr(href), page); color: #667eea; }
.toc .l2 { padding-left: 24px; font-size: 13px; }
h1 { font-family: "SimHei", sans-serif; font-size: 28px; color: #1e293b; margin-top: 40px; page-break-before: always; }
h2 { font-family: "SimHei", sans-serif; font-size: 21px; color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 6px; margin-top: 32px; }
h3 { font-family: "SimHei", sans-serif; font-size: 17px; color: #475569; margin-top: 24px; }
h4 { font-family: "SimHei", sans-serif; font-size: 14px; color: #555; margin: 16px 0 6px; }
table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 11.5px; page-break-inside: avoid; }
th { background: #667eea; color: white; font-family: "SimHei", sans-serif; padding: 9px 11px; text-align: left; }
td { padding: 7px 11px; border-bottom: 1px solid #e2e8f0; }
tr:nth-child(even) td { background: #f8fafc; }
pre { background: #1e293b; color: #e2e8f0; padding: 14px 18px; border-radius: 6px; font-family: "Consolas","Courier New",monospace; font-size: 10.5px; line-height: 1.55; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
code { background: #f1f5f9; padding: 2px 6px; border-radius: 3px; font-family: "Consolas","Courier New",monospace; font-size: 11px; }
pre code { background: transparent; padding: 0; }
.arch-diagram, .flow-diagram { text-align: center; margin: 18px 0; page-break-inside: avoid; }
.arch-diagram svg, .flow-diagram svg { max-width: 100%; height: auto; }
.callout { border-left: 4px solid #667eea; background: #eef2ff; padding: 12px 18px; margin: 16px 0; border-radius: 0 6px 6px 0; }
.callout.warning { border-left-color: #f59e0b; background: #fffbeb; }
.callout.info { border-left-color: #06b6d4; background: #ecfeff; }
.callout.success { border-left-color: #10b981; background: #ecfdf5; }
.feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }
.feature-card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; background: white; page-break-inside: avoid; }
.feature-card h4 { margin: 0 0 6px; color: #667eea; }
.feature-card p { margin: 0; font-size: 11.5px; }
.screenshot { text-align: center; margin: 20px 0; page-break-inside: avoid; }
.screenshot img { max-width: 100%; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.screenshot .caption { font-size: 11px; color: #888; margin-top: 6px; }
.footer-note { margin-top: 40px; padding-top: 20px; border-top: 2px solid #667eea; text-align: center; font-size: 11px; color: #888; }
ul, ol { padding-left: 24px; }
li { margin: 4px 0; }
p { margin: 8px 0; text-align: justify; }
"""


def main():
    print("Generating comprehensive project documentation PDF...")
    date_str = datetime.now().strftime("%Y-%m-%d")

    screenshot_section = ""
    if INTRO_BASE64:
        screenshot_section = f"""
<div class="screenshot">
  <img src="data:image/png;base64,{INTRO_BASE64}" alt="Product Preview">
  <div class="caption">Fig: Multi-Agent Platform - Web UI Product Preview</div>
</div>"""

    # Read HTML template from external file
    template_path = PROJECT_ROOT / "docs" / "project_doc_template.html"
    if template_path.exists():
        html = template_path.read_text(encoding="utf-8")
        print(f"Template loaded: {len(html)} chars")
    else:
        print("[ERROR] Template file not found!")
        sys.exit(1)

    # Replace placeholders
    html = html.replace("__CSS__", CSS)
    html = html.replace("__DATE__", date_str)
    html = html.replace("__SCREENSHOT__", screenshot_section)
    html = html.replace("__ARCH_OVERVIEW__", svg_arch_overview())
    html = html.replace("__EDU_FANOUT__", svg_education_fanout())
    html = html.replace("__RAG_PIPELINE__", svg_rag_pipeline())
    html = html.replace("__DEEP_EVIDENCE__", svg_deep_evidence())
    html = html.replace("__LANGGRAPH_STATE__", svg_langgraph_state())
    html = html.replace("__SEQ_EDUCATION__", svg_sequence_education())
    html = html.replace("__SOURCE__", "{source}")

    html_path = PROJECT_ROOT / "docs" / "project_doc.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML written: {html_path} ({html_path.stat().st_size / 1024:.0f} KB)")

    # Convert to PDF
    print("Converting to PDF with WeasyPrint...")
    try:
        from weasyprint import HTML
        doc = HTML(string=html)
        doc.write_pdf(str(OUTPUT_PDF))
        size_kb = OUTPUT_PDF.stat().st_size / 1024
        print(f"[OK] PDF generated: {OUTPUT_PDF}")
        print(f"     Size: {size_kb:.0f} KB")
    except ImportError:
        print("[ERROR] weasyprint not installed. Run: pip install weasyprint")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
