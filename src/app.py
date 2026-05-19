# src/app.py
from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from ui_helpers import NODE_STEPS, DISRUPTIONS, PAGE_CSS, build_pipeline_html

st.set_page_config(
    page_title="SeeWeeS Ops Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in [
    ("disruption_type", "demand_spike"),
    ("pipeline_done",   False),
    ("final_state",     {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Logo / brand ───────────────────────────────────────────────────────────────
st.markdown(
    '<div style="padding:18px 40px 0;background:rgba(10,10,10,0.97);'
    'border-bottom:1px solid #1d1d1f">'
    '<div style="font-size:15px;font-weight:600;color:#f5f5f7;'
    'letter-spacing:0.05em;padding-bottom:14px">'
    'SeeWeeS <span style="color:#6e6e73;font-weight:400">/ Ops Intelligence</span>'
    '</div></div>',
    unsafe_allow_html=True,
)

# ── Disruption type pill row ───────────────────────────────────────────────────
disruption_keys = list(DISRUPTIONS.keys())
cols = st.columns([1.4, 1.4, 1.6, 1.4, 0.2, 1.2], gap="small")
run_clicked = False

for col, dtype in zip(cols[:4], disruption_keys):
    cfg = DISRUPTIONS[dtype]
    is_active = st.session_state.disruption_type == dtype
    with col:
        label = ("● " if is_active else "○ ") + cfg["label"]
        if st.button(label, key=f"dtype_{dtype}", use_container_width=True):
            if dtype != st.session_state.disruption_type:
                st.session_state.disruption_type = dtype
                st.session_state.pipeline_done   = False
                st.session_state.final_state     = {}
            st.rerun()

with cols[5]:
    run_clicked = st.button("Run", key="run_btn", use_container_width=True, type="primary")

# ── Disruption level control ───────────────────────────────────────────────────
selected_type = st.session_state.disruption_type
cfg = DISRUPTIONS[selected_type]
disruption_params: dict = {}

level_col, _ = st.columns([3, 3], gap="small")
with level_col:
    if cfg["kind"] == "slider_float":
        val = st.slider(
            f"Level — {cfg['label']}",
            min_value=float(cfg["min"]),
            max_value=float(cfg["max"]),
            value=float(cfg["default"]),
            step=float(cfg["step"]),
            format="×%.1f",
        )
        disruption_params = {cfg["param"]: val}

    elif cfg["kind"] == "slider_pct":
        val = st.slider(
            f"Level — {cfg['label']}",
            min_value=int(cfg["min"]),
            max_value=int(cfg["max"]),
            value=int(cfg["default"]),
            step=int(cfg["step"]),
            format="%d%%",
        )
        disruption_params = {cfg["param"]: val / 100}

    elif cfg["kind"] == "slider_int":
        val = st.slider(
            f"Level — {cfg['label']}",
            min_value=int(cfg["min"]),
            max_value=int(cfg["max"]),
            value=int(cfg["default"]),
            step=int(cfg["step"]),
        )
        disruption_params = {cfg["param"]: val}

    elif cfg["kind"] == "select":
        val = st.selectbox(
            f"Location — {cfg['label']}",
            options=cfg["options"],
        )
        disruption_params = {cfg["param"]: val}

st.markdown("---")

# ── Pipeline placeholder ───────────────────────────────────────────────────────
pipeline_ph = st.empty()
step_keys   = [s[0] for s in NODE_STEPS]


def _show_pipeline(completed: list, active, accumulated: dict) -> None:
    html = build_pipeline_html(completed, active, accumulated, selected_type)
    pipeline_ph.empty()
    with pipeline_ph.container():
        st.components.v1.html(html, height=920, scrolling=True)


# Idle state
if not run_clicked and not st.session_state.pipeline_done:
    _show_pipeline([], None, {})

# Restored state after a previous run
if not run_clicked and st.session_state.pipeline_done:
    _show_pipeline(step_keys, None, st.session_state.final_state)

# ── Run pipeline ───────────────────────────────────────────────────────────────
if run_clicked:
    st.session_state.pipeline_done = False
    st.session_state.final_state   = {}

    try:
        from tracing import init_langsmith_tracing
        init_langsmith_tracing()
    except Exception:
        pass

    from graph import build_graph

    app        = build_graph()
    init_state = {
        "pdf_path": os.path.join(
            os.path.dirname(__file__), "..", "data",
            "SeeWeeS Specialty Dispatch Playbook.pdf",
        ),
        "csv_path": os.path.join(
            os.path.dirname(__file__), "..", "data",
            "Incoming_shipment_03_06.csv",
        ),
        "disruption_type":   selected_type,
        "disruption_params": disruption_params,
    }

    completed:  list = []
    accumulated: dict = {}

    _show_pipeline([], step_keys[0], {})

    for event in app.stream(init_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            accumulated.update(state_update)
            if node_name in step_keys:
                if node_name not in completed:
                    completed.append(node_name)
                idx    = step_keys.index(node_name)
                active = step_keys[idx + 1] if idx + 1 < len(step_keys) else None
            else:
                active = None
            _show_pipeline(completed, active, accumulated)

    _show_pipeline(step_keys, None, accumulated)
    st.session_state.pipeline_done = True
    st.session_state.final_state   = accumulated

# ── Full executive report (below pipeline) ────────────────────────────────────
if st.session_state.pipeline_done:
    report_html = st.session_state.final_state.get("report_html", "")
    if report_html:
        st.markdown(
            '<div style="padding:0 40px">'
            '<h2 style="font-size:18px;font-weight:600;color:#f5f5f7;'
            'margin:32px 0 16px;font-family:-apple-system,sans-serif">'
            'Executive Report</h2></div>',
            unsafe_allow_html=True,
        )
        st.components.v1.html(report_html, height=900, scrolling=True)
