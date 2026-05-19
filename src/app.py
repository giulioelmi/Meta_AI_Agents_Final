# src/app.py
from __future__ import annotations
import sys
import os

# Ensure src/ is on the path when run as streamlit app.py
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="SeeWeeS Ops Command Center",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 SeeWeeS Ops Command Center")
st.caption("Multi-agent AI system for medical supply chain dispatch")

# ── Sidebar: scenario configuration ──────────────────────────────────────────
with st.sidebar:
    st.header("Scenario Configuration")

    disruption_type = st.selectbox(
        "Disruption Type",
        options=["demand_spike", "driver_shortage", "warehouse_closure", "weather_event"],
        format_func=lambda x: {
            "demand_spike": "📈 Demand Spike",
            "driver_shortage": "🚗 Driver Shortage",
            "warehouse_closure": "🏭 Warehouse Closure",
            "weather_event": "🌩️ Weather Event",
        }[x],
    )

    st.subheader("Parameters")
    disruption_params: dict = {}

    if disruption_type == "demand_spike":
        multiplier = st.slider("Demand multiplier", 1.0, 2.0, 1.2, 0.05)
        disruption_params = {"multiplier": multiplier}

    elif disruption_type == "driver_shortage":
        shortage_pct = st.slider("Drivers unavailable (%)", 10, 70, 30, 5)
        disruption_params = {"shortage_pct": shortage_pct / 100}

    elif disruption_type == "warehouse_closure":
        location = st.selectbox("Closed location", ["Boston-MGH", "Boston-BWH"])
        disruption_params = {"location": location}

    elif disruption_type == "weather_event":
        risk_score = st.slider("Weather risk score (0–3)", 0, 3, 2)
        disruption_params = {"risk_score": risk_score}

    st.divider()
    run_button = st.button("▶ Run Pipeline", type="primary", use_container_width=True)

# ── Main area ─────────────────────────────────────────────────────────────────
if run_button:
    with st.spinner("Running multi-agent pipeline… this takes ~60–90 seconds"):
        try:
            from tracing import init_langsmith_tracing
            init_langsmith_tracing()
        except Exception:
            pass  # LangSmith optional

        from graph import build_graph

        app = build_graph()
        initial_state = {
            "pdf_path": os.path.join(os.path.dirname(__file__), "..", "data", "SeeWeeS Specialty Dispatch Playbook.pdf"),
            "csv_path": os.path.join(os.path.dirname(__file__), "..", "data", "Incoming_shipment_03_06.csv"),
            "disruption_type": disruption_type,
            "disruption_params": disruption_params,
        }

        final = app.invoke(initial_state)

    st.success("Pipeline complete!")

    # ── KPI dashboard ──
    st.header("📊 KPI Dashboard")
    col1, col2 = st.columns(2)

    baseline = final.get("csv_kpis", {})
    scenario = final.get("scenario_kpis", {})

    with col1:
        st.subheader("Baseline")
        if baseline:
            st.metric("On-time rate", f"{baseline.get('on_time_rate_pct', 0):.1f}%")
            st.metric("Cold chain breach rate", f"{baseline.get('cold_chain_breach_rate_pct', 0):.1f}%")
            st.metric("Shipments at risk", baseline.get("shipments_at_risk", 0))
            st.metric("Critical hospital on-time", f"{baseline.get('critical_hospital_on_time_pct', 0):.1f}%")

    with col2:
        st.subheader(f"Scenario: {disruption_type}")
        if scenario:
            delta_ontime = scenario.get("on_time_rate_pct", 0) - baseline.get("on_time_rate_pct", 0)
            delta_breach = scenario.get("cold_chain_breach_rate_pct", 0) - baseline.get("cold_chain_breach_rate_pct", 0)
            st.metric("On-time rate", f"{scenario.get('on_time_rate_pct', 0):.1f}%", delta=f"{delta_ontime:+.1f}%")
            st.metric("Cold chain breach rate", f"{scenario.get('cold_chain_breach_rate_pct', 0):.1f}%", delta=f"{delta_breach:+.1f}%")
            st.metric("Shipments at risk", scenario.get("shipments_at_risk", 0))
            st.metric("Critical hospital on-time", f"{scenario.get('critical_hospital_on_time_pct', 0):.1f}%")

    # ── Audit result ──
    st.header("⚖️ Audit Result")
    verdict = final.get("audit_verdict", "unknown")
    retries = final.get("audit_retries", 0)
    violations = final.get("audit_violations", [])
    if verdict == "pass":
        st.success(f"✅ Plan APPROVED after {retries} revision(s)")
    else:
        st.warning(f"⚠️ Plan reached max retries ({retries}) — proceeding with best available plan")
    if violations:
        with st.expander("Violations flagged"):
            for v in violations:
                st.write(f"• {v}")

    # ── Stakeholder synthesis ──
    st.header("👥 Stakeholder Simulation")
    reactions = final.get("stakeholder_reactions", {})
    if reactions:
        tabs = st.tabs(list(reactions.keys()))
        for tab, (persona, reaction) in zip(tabs, reactions.items()):
            with tab:
                st.write(reaction)
    synthesis = final.get("stakeholder_synthesis", "")
    if synthesis:
        with st.expander("Synthesis — Failure Paths & Escalation Triggers", expanded=True):
            st.markdown(synthesis)

    # ── Executive report ──
    st.header("📄 Executive Report")
    report_html = final.get("report_html", "")
    if report_html:
        st.components.v1.html(report_html, height=800, scrolling=True)
    else:
        st.warning("No report generated.")

else:
    st.info("Configure your disruption scenario in the sidebar and click **▶ Run Pipeline** to begin.")
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Supply_chain_network.svg/640px-Supply_chain_network.svg.png",
        caption="SeeWeeS I-95 Corridor Operations",
        width="stretch",
    )
