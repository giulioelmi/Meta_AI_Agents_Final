# tests/test_judge.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
from unittest.mock import patch, MagicMock


def _mock_llm(content: str):
    fake = MagicMock()
    fake.content = content
    return fake


def test_judge_pass():
    from nodes.judge import node_judge
    verdict = json.dumps({"verdict": "pass", "violations": [], "required_fixes": []})
    with patch("agents.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm(verdict)
        result = node_judge({
            "business_context": "SLA: 4h.", "dispatch_plan": "Good plan.", "audit_retries": 0
        })
    assert result["audit_verdict"] == "pass"
    assert result["audit_violations"] == []
    assert result["audit_retries"] == 0


def test_judge_fail_increments_retries():
    from nodes.judge import node_judge
    verdict = json.dumps({
        "verdict": "fail",
        "violations": ["Cold chain breach not addressed."],
        "required_fixes": ["Add cold chain monitoring step."]
    })
    with patch("agents.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm(verdict)
        result = node_judge({
            "business_context": "SLA: 4h.", "dispatch_plan": "Bad plan.", "audit_retries": 0
        })
    assert result["audit_verdict"] == "fail"
    assert result["audit_retries"] == 1
    assert len(result["audit_violations"]) == 1


def test_route_after_judge_pass():
    from nodes.judge import route_after_judge
    assert route_after_judge({"audit_verdict": "pass", "audit_retries": 0}) == "report"


def test_route_after_judge_fail():
    from nodes.judge import route_after_judge
    assert route_after_judge({"audit_verdict": "fail", "audit_retries": 1}) == "revise_plan"


def test_route_after_judge_max_retries():
    from nodes.judge import route_after_judge
    assert route_after_judge({"audit_verdict": "fail", "audit_retries": 3}) == "report"


def test_node_revise_returns_updated_plan():
    from nodes.judge import node_revise
    fake = MagicMock(); fake.content = "Revised plan with cold chain steps."
    with patch("agents.llm") as mock_llm:
        mock_llm.invoke.return_value = fake
        result = node_revise({
            "dispatch_plan": "Old plan.",
            "audit_violations": ["Missing cold chain steps."],
            "stakeholder_synthesis": "All personas concerned about cold chain.",
        })
    assert result["dispatch_plan"] == "Revised plan with cold chain steps."
