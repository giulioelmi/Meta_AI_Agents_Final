# src/nodes/judge.py
from __future__ import annotations
from typing import Dict, Any
from agents import run_judge_agent, run_revise_agent

MAX_RETRIES = 3


def node_judge(state: Dict[str, Any]) -> Dict[str, Any]:
    result = run_judge_agent(
        business_context=state.get("business_context", ""),
        dispatch_plan=state.get("dispatch_plan", ""),
    )
    retries = state.get("audit_retries", 0)
    if result["verdict"] == "fail":
        retries += 1
    return {
        "audit_verdict": result["verdict"],
        "audit_violations": result.get("violations", []),
        "audit_required_fixes": result.get("required_fixes", []),
        "audit_retries": retries,
    }


def node_revise(state: Dict[str, Any]) -> Dict[str, Any]:
    revised = run_revise_agent(
        dispatch_plan=state.get("dispatch_plan", ""),
        violations=state.get("audit_violations", []),
        required_fixes=state.get("audit_required_fixes", []),
        stakeholder_synthesis=state.get("stakeholder_synthesis", ""),
    )
    return {"dispatch_plan": revised}


def route_after_judge(state: Dict[str, Any]) -> str:
    if state.get("audit_verdict") == "pass" or state.get("audit_retries", 0) >= MAX_RETRIES:
        return "report"
    return "revise_plan"
