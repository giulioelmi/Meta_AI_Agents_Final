import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import pandas as pd
from datetime import datetime, timedelta
from tools.kpi_tools import compute_domain_kpis

def _sample_df():
    base = datetime(2026, 3, 6, 10, 0)
    return pd.DataFrame({
        "item_id": [10021, 10022, 10023],
        "is_late": [False, True, False],
        "cold_chain_required": [True, True, False],
        "cold_chain_breach": [False, True, False],
        "hospital_priority": [1, 1, 2],
        "quantity_ordered": [10, 20, 5],
        "truck_capacity_units": [50, 50, 50],
        "scheduled_date": [base, base, base],
        "actual_date": [base, base + timedelta(hours=2), base],
    })

def test_on_time_rate():
    kpis = compute_domain_kpis(_sample_df())
    assert kpis["on_time_rate_pct"] == pytest.approx(66.67, abs=0.1)

def test_cold_chain_breach_rate():
    kpis = compute_domain_kpis(_sample_df())
    assert kpis["cold_chain_breach_rate_pct"] == pytest.approx(50.0, abs=0.1)

def test_critical_hospital_on_time_rate():
    kpis = compute_domain_kpis(_sample_df())
    assert kpis["critical_hospital_on_time_pct"] == pytest.approx(50.0, abs=0.1)

def test_shipments_at_risk():
    kpis = compute_domain_kpis(_sample_df())
    # Only item 10022: late AND priority 1
    assert kpis["shipments_at_risk"] == 1

def test_all_required_keys_present():
    kpis = compute_domain_kpis(_sample_df())
    required = [
        "total_shipments", "on_time_rate_pct", "late_shipments",
        "cold_chain_shipments", "cold_chain_breach_count", "cold_chain_breach_rate_pct",
        "critical_hospital_shipments", "critical_hospital_on_time_pct",
        "total_units_dispatched", "capacity_utilization_pct", "shipments_at_risk",
    ]
    for k in required:
        assert k in kpis, f"Missing KPI: {k}"
