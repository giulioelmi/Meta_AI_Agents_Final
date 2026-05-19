from __future__ import annotations
from typing import Dict, Any
import pandas as pd

def compute_domain_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    total = len(df)
    on_time = int((~df["is_late"]).sum())
    cold_chain = df[df["cold_chain_required"]]
    breaches = int(df["cold_chain_breach"].sum())
    critical = df[df["hospital_priority"] == 1]
    critical_on_time = int((~critical["is_late"]).sum()) if len(critical) > 0 else 0
    total_qty = int(df["quantity_ordered"].sum())
    capacity = int(df["truck_capacity_units"].iloc[0]) if total > 0 else 50

    return {
        "total_shipments": int(total),
        "on_time_rate_pct": round(100 * on_time / total, 2) if total else 0.0,
        "late_shipments": int(total - on_time),
        "cold_chain_shipments": int(len(cold_chain)),
        "cold_chain_breach_count": breaches,
        "cold_chain_breach_rate_pct": round(100 * breaches / len(cold_chain), 2) if len(cold_chain) else 0.0,
        "critical_hospital_shipments": int(len(critical)),
        "critical_hospital_on_time_pct": round(100 * critical_on_time / len(critical), 2) if len(critical) else 0.0,
        "total_units_dispatched": total_qty,
        "capacity_utilization_pct": round(100 * total_qty / (capacity * total), 2) if total else 0.0,
        "shipments_at_risk": int(df[df["is_late"] & (df["hospital_priority"] == 1)].shape[0]),
    }
