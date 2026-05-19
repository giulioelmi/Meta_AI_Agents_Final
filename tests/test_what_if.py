# tests/test_what_if.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
from unittest.mock import patch, MagicMock
from tools.augment_tools import augment_shipment_df
from tools.kpi_tools import compute_domain_kpis


def _base_state():
    df = pd.read_csv("data/Incoming_shipment_03_06.csv")
    df = augment_shipment_df(df)
    return {
        "csv_kpis": compute_domain_kpis(df),
        "augmented_df_json": df.to_json(),
        "disruption_type": "demand_spike",
        "disruption_params": {"multiplier": 1.2},
        "business_context": "SLA: deliver within 4h for priority-1 hospitals.",
        "weather_risk": {"risk_score_0_3": 1},
    }


def test_demand_spike_raises_units_dispatched():
    from nodes.what_if import node_what_if
    fake = MagicMock()
    fake.content = "Demand spike increases risk."
    with patch("nodes.what_if.llm") as mock_llm:
        mock_llm.invoke.return_value = fake
        state = _base_state()
        result = node_what_if(state)
    assert "scenario_kpis" in result
    assert result["scenario_kpis"]["total_units_dispatched"] > state["csv_kpis"]["total_units_dispatched"]


def test_what_if_returns_summary():
    from nodes.what_if import node_what_if
    fake = MagicMock()
    fake.content = "Three bullet summary."
    with patch("nodes.what_if.llm") as mock_llm:
        mock_llm.invoke.return_value = fake
        result = node_what_if(_base_state())
    assert result["what_if_summary"] == "Three bullet summary."


def test_driver_shortage_increases_late_shipments():
    from nodes.what_if import node_what_if
    fake = MagicMock(); fake.content = "Driver shortage impact."
    state = _base_state()
    state["disruption_type"] = "driver_shortage"
    state["disruption_params"] = {"shortage_pct": 0.5}
    with patch("nodes.what_if.llm") as mock_llm:
        mock_llm.invoke.return_value = fake
        result = node_what_if(state)
    assert result["scenario_kpis"]["late_shipments"] >= state["csv_kpis"]["late_shipments"]
