# tests/test_stakeholder_sim.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import patch, MagicMock


def _state():
    return {
        "disruption_type": "demand_spike",
        "what_if_summary": "20% demand spike increases at-risk shipments by 40%.",
        "scenario_kpis": {"on_time_rate_pct": 55.0, "cold_chain_breach_rate_pct": 12.0},
        "dispatch_plan": "Proceed with standard routing.",
        "business_context": "SLA: 4h for priority-1.",
    }


def test_stakeholder_sim_returns_all_personas():
    from nodes.stakeholder_sim import node_stakeholder_sim
    fake = MagicMock()
    fake.content = "I am concerned about this plan."
    with patch("nodes.stakeholder_sim.llm") as mock_llm:
        mock_llm.invoke.return_value = fake
        result = node_stakeholder_sim(_state())
    assert "stakeholder_reactions" in result
    assert len(result["stakeholder_reactions"]) == 6
    expected_personas = {"HospitalAdmin", "Dispatcher", "Driver", "WarehouseManager", "ComplianceOfficer", "CFO"}
    assert set(result["stakeholder_reactions"].keys()) == expected_personas


def test_stakeholder_sim_returns_synthesis():
    from nodes.stakeholder_sim import node_stakeholder_sim
    fake = MagicMock()
    fake.content = "Synthesis output."
    with patch("nodes.stakeholder_sim.llm") as mock_llm:
        mock_llm.invoke.return_value = fake
        result = node_stakeholder_sim(_state())
    assert "stakeholder_synthesis" in result
    assert len(result["stakeholder_synthesis"]) > 0
