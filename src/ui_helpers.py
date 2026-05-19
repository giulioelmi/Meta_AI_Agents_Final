# src/ui_helpers.py
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple


# (node_key, display_title, subtitle)
NODE_STEPS: List[Tuple[str, str, str]] = [
    ("pdf_context",     "PDF Context",        "Business rules & SLA thresholds extracted from playbook"),
    ("csv_analysis",    "CSV Analysis",       "Shipment data augmented with domain KPIs"),
    ("weather",         "Weather Risk",       "I-95 corridor waypoint risk assessment"),
    ("what_if",         "What-If Simulation", "Disruption scenario applied to baseline"),
    ("stakeholder_sim", "Stakeholder Sim",    "6-persona reaction network"),
    ("planner",         "Planner",            "Mitigation dispatch plan"),
    ("judge",           "Judge / Audit",      "Plan compliance & constraint verification"),
    ("report",          "Executive Report",   "Final HTML report"),
]

DISRUPTIONS: Dict[str, Dict[str, Any]] = {
    "demand_spike": {
        "label": "Demand Spike",
        "kind":  "slider_float",
        "param": "multiplier",
        "min": 1.1, "max": 3.0, "default": 1.2, "step": 0.1,
    },
    "driver_shortage": {
        "label": "Driver Shortage",
        "kind":  "slider_pct",
        "param": "shortage_pct",
        "min": 10, "max": 80, "default": 30, "step": 5,
    },
    "warehouse_closure": {
        "label": "Warehouse Closure",
        "kind":  "select",
        "param": "location",
        "options": ["Boston-MGH", "Boston-BWH"],
    },
    "weather_event": {
        "label": "Weather Event",
        "kind":  "slider_int",
        "param": "risk_score",
        "min": 0, "max": 3, "default": 2, "step": 1,
    },
}

PAGE_CSS = """
<style>
/* ── Reset & base ── */
[data-testid="stAppViewContainer"] { background: #0a0a0a !important; }
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Pill buttons (disruption type) ── */
div[data-testid="stButton"] > button {
    border-radius: 20px !important;
    font-family: -apple-system,"SF Pro Display","Helvetica Neue",sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 6px 18px !important;
    border: 1px solid #3a3a3c !important;
    background: transparent !important; color: #6e6e73 !important;
    transition: all 0.18s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #1d1d1f !important; color: #f5f5f7 !important;
}

/* ── Slider ── */
[data-testid="stSlider"] { padding: 0 4px !important; }
[data-testid="stSlider"] label { font-size: 12px !important; color: #6e6e73 !important; }
[data-testid="stSlider"] [data-testid="stMarkdownContainer"] p { color: #6e6e73 !important; font-size:12px !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] label { font-size: 12px !important; color: #6e6e73 !important; }
[data-testid="stSelectbox"] > div > div {
    background: #1d1d1f !important; border-color: #3a3a3c !important;
    color: #f5f5f7 !important; font-size: 13px !important;
}

/* ── Divider ── */
hr { border-color: #1d1d1f !important; margin: 0 !important; }
</style>
"""
