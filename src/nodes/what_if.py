# src/nodes/what_if.py
from __future__ import annotations
from datetime import timedelta
from typing import Dict, Any
import io
import pandas as pd
from agents import llm
from prompts_advanced import WHAT_IF_PROMPT
from tools.kpi_tools import compute_domain_kpis


def run_what_if_agent(disruption_type: str, disruption_params: Dict, baseline_kpis: Dict,
                      scenario_kpis: Dict, business_context: str) -> str:
    return llm.invoke(WHAT_IF_PROMPT.format_messages(
        disruption_type=disruption_type,
        disruption_params=disruption_params,
        baseline_kpis=baseline_kpis,
        scenario_kpis=scenario_kpis,
        business_context=business_context,
    )).content


def _apply_demand_spike(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    df["quantity_ordered"] = (df["quantity_ordered"] * params.get("multiplier", 1.2)).astype(int)
    return df


def _apply_driver_shortage(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    shortage_pct = params.get("shortage_pct", 0.3)
    n_affected = int(len(df) * shortage_pct)
    df.loc[df.index[:n_affected], "actual_date"] = (
        df.loc[df.index[:n_affected], "actual_date"] + timedelta(hours=4)
    )
    df["is_late"] = df["actual_date"] > df["scheduled_date"]
    return df


def _apply_warehouse_closure(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    location = params.get("location", "Boston-MGH")
    mask = df["dispatch_location"] == location
    df.loc[mask, "actual_date"] = df.loc[mask, "actual_date"] + timedelta(hours=4)
    df["is_late"] = df["actual_date"] > df["scheduled_date"]
    return df


def _apply_weather_event(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    risk_score = params.get("risk_score", 2)
    delay_map = {0: 0, 1: 1, 2: 3, 3: 6}
    delay_h = delay_map.get(risk_score, 2)
    df["actual_date"] = df["actual_date"] + timedelta(hours=delay_h)
    df["is_late"] = df["actual_date"] > df["scheduled_date"]
    return df


_HANDLERS = {
    "demand_spike": _apply_demand_spike,
    "driver_shortage": _apply_driver_shortage,
    "warehouse_closure": _apply_warehouse_closure,
    "weather_event": _apply_weather_event,
}


def node_what_if(state: Dict[str, Any]) -> Dict[str, Any]:
    disruption_type = state.get("disruption_type", "demand_spike")
    disruption_params = state.get("disruption_params", {"multiplier": 1.2})
    df = pd.read_json(io.StringIO(state["augmented_df_json"]))

    # Restore datetime columns lost in JSON serialization
    for col in ("scheduled_date", "actual_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="ms")

    handler = _HANDLERS.get(disruption_type, _apply_demand_spike)
    df_scenario = handler(df, disruption_params)
    scenario_kpis = compute_domain_kpis(df_scenario)

    summary = run_what_if_agent(
        disruption_type=disruption_type,
        disruption_params=disruption_params,
        baseline_kpis=state.get("csv_kpis", {}),
        scenario_kpis=scenario_kpis,
        business_context=state.get("business_context", ""),
    )
    return {
        "scenario_kpis": scenario_kpis,
        "what_if_summary": summary,
    }
