from __future__ import annotations
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from prompts import PDF_CONTEXT_PROMPT, OPS_ANALYSIS_PROMPT, PLANNER_PROMPT, REPORT_PROMPT

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.2,
    tags=["msba-demo", "multi-agent"],
    metadata={"repo": "MSBA_AI_Agents_Demo"}
)


def run_context_agent(snippets: str) -> str:
    return llm.invoke(PDF_CONTEXT_PROMPT.format_messages(snippets=snippets)).content

def run_ops_agent(summary: Dict[str, Any], kpis: Dict[str, Any], anomalies_md: str) -> str:
    return llm.invoke(OPS_ANALYSIS_PROMPT.format_messages(
        summary=summary, kpis=kpis, anomalies_md=anomalies_md
    )).content

def run_planner_agent(
    business_context: str,
    ops_insights: str,
    weather_risk: Dict[str, Any],
    what_if_summary: str = "",
    scenario_kpis: Dict[str, Any] = None,
    stakeholder_synthesis: str = "",
) -> str:
    return llm.invoke(PLANNER_PROMPT.format_messages(
        business_context=business_context,
        ops_insights=ops_insights,
        weather_risk=weather_risk,
        what_if_summary=what_if_summary,
        scenario_kpis=scenario_kpis or {},
        stakeholder_synthesis=stakeholder_synthesis,
    )).content

def run_report_agent(
    business_context: str,
    kpis: Dict[str, Any],
    anomaly_highlights: str,
    weather_risk: Dict[str, Any],
    dispatch_plan: str,
) -> str:
    return llm.invoke(REPORT_PROMPT.format_messages(
        business_context=business_context,
        kpis=kpis,
        anomaly_highlights=anomaly_highlights,
        weather_risk=weather_risk,
        dispatch_plan=dispatch_plan
    )).content


def run_judge_agent(business_context: str, dispatch_plan: str) -> Dict[str, Any]:
    import json as _json
    from prompts_advanced import JUDGE_PROMPT
    raw = llm.invoke(JUDGE_PROMPT.format_messages(
        business_context=business_context,
        dispatch_plan=dispatch_plan,
    )).content
    try:
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.split("\n")[1:])
            cleaned = cleaned.rstrip("`").strip()
        return _json.loads(cleaned)
    except Exception:
        return {"verdict": "pass", "violations": [], "required_fixes": []}


def run_revise_agent(dispatch_plan: str, violations: list, required_fixes: list,
                     stakeholder_synthesis: str) -> str:
    from prompts_advanced import REVISE_PROMPT
    return llm.invoke(REVISE_PROMPT.format_messages(
        dispatch_plan=dispatch_plan,
        violations="\n".join(f"- {v}" for v in violations),
        required_fixes="\n".join(f"- {f}" for f in required_fixes),
        stakeholder_synthesis=stakeholder_synthesis,
    )).content
