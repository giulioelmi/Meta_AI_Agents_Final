# SeeWeeS Apple-Dark UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `src/app.py` with an Apple-inspired dark-theme Streamlit UI that streams pipeline progress in real time, expands each step inline with rich contextual content, and exposes disruption-type and disruption-level controls at the top of the page (no sidebar).

**Architecture:** Two files: `src/ui_helpers.py` owns all rendering logic (CSS constant, step constants, per-step HTML panel renderers, `build_pipeline_html()`); `src/app.py` owns page config, CSS injection, session state, top controls, and the streaming loop. LangGraph `app.stream(stream_mode="updates")` drives step-by-step updates; an `st.empty()` placeholder is replaced on each event with a fresh `st.components.v1.html()` call containing the full self-contained pipeline document.

**Tech Stack:** Streamlit ≥ 1.35, LangGraph streaming (`stream_mode="updates"`), inline HTML/CSS/JS (no external dependencies), Python 3.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/ui_helpers.py` | Create | `NODE_STEPS`, `DISRUPTIONS`, `PAGE_CSS`, per-step panel renderers, `build_pipeline_html()` |
| `src/app.py` | Rewrite | Page config, CSS injection, session state, top controls (type buttons + level slider), streaming loop, full report section |

---

### Task 1: Create `src/ui_helpers.py` — constants and CSS

**Files:**
- Create: `src/ui_helpers.py`

- [ ] **Step 1: Create the file with imports, NODE_STEPS, DISRUPTIONS**

```python
# src/ui_helpers.py
from __future__ import annotations
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
```

- [ ] **Step 2: Append PAGE_CSS to the same file**

```python
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

/* ── Run button override ── */
div[data-testid="stButton"].run-pill > button {
    background: #f5f5f7 !important; color: #0a0a0a !important;
    border-color: transparent !important; font-weight: 600 !important;
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
```

- [ ] **Step 3: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/ui_helpers.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/ui_helpers.py
git commit -m "feat: add ui_helpers skeleton — NODE_STEPS, DISRUPTIONS, PAGE_CSS"
```

---

### Task 2: Add per-step panel renderers to `src/ui_helpers.py`

Each renderer returns an HTML string for the expanded step content. They receive `accumulated_state: Dict[str, Any]`.

**Files:**
- Modify: `src/ui_helpers.py`

- [ ] **Step 1: Append `_card()` helper and `render_pdf_context_panel()`**

```python
# ── Rendering helpers ──────────────────────────────────────────────────────────

def _card(content: str) -> str:
    return (
        f'<div style="background:#111;border:1px solid #1d1d1f;border-radius:12px;'
        f'padding:20px;margin-top:14px">{content}</div>'
    )


def _kpi_grid(items: List[Tuple[str, str, str]]) -> str:
    """items: (label, value, hex_color). Returns a flex row of KPI pills."""
    pills = "".join(
        f'<div style="flex:1;min-width:90px;background:#1a1a1c;border-radius:10px;'
        f'padding:14px 12px;text-align:center">'
        f'<div style="font-size:11px;color:#6e6e73;margin-bottom:6px">{label}</div>'
        f'<div style="font-size:20px;font-weight:600;color:{color}">{value}</div>'
        f'</div>'
        for label, value, color in items
    )
    return f'<div style="display:flex;gap:8px;flex-wrap:wrap">{pills}</div>'


def render_pdf_context_panel(state: Dict[str, Any]) -> str:
    ctx = state.get("business_context", "")
    lines = [l.strip("•-* ").strip() for l in ctx.splitlines() if l.strip().startswith(("•", "-", "*"))][:6]
    if lines:
        pills = "".join(
            f'<span style="display:inline-block;background:#1c2a1c;color:#30d158;'
            f'border-radius:6px;padding:4px 10px;font-size:11px;margin:3px">{l[:70]}</span>'
            for l in lines
        )
        body = pills
    else:
        preview = ctx[:300].strip() + ("…" if len(ctx) > 300 else "")
        body = f'<p style="font-size:13px;color:#aeaeb2;line-height:1.6">{preview}</p>'
    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'Extracted business rules</div>{body}'
    )
```

- [ ] **Step 2: Append `render_csv_analysis_panel()`**

```python
def render_csv_analysis_panel(state: Dict[str, Any]) -> str:
    kpis = state.get("csv_kpis", {})
    on_time  = kpis.get("on_time_rate_pct", 0)
    breach   = kpis.get("cold_chain_breach_rate_pct", 0)
    at_risk  = kpis.get("shipments_at_risk", 0)
    total    = kpis.get("total_shipments", 0)
    crit_pct = kpis.get("critical_hospital_on_time_pct", 0)

    grid = _kpi_grid([
        ("On-time",          f"{on_time:.1f}%",  "#30d158"),
        ("Cold breach",      f"{breach:.1f}%",   "#ff453a" if breach > 5 else "#30d158"),
        ("At-risk",          str(at_risk),        "#ff9f0a" if at_risk > 0 else "#30d158"),
        ("Critical on-time", f"{crit_pct:.1f}%", "#30d158"),
        ("Total",            str(total),          "#aeaeb2"),
    ])
    insights = state.get("ops_insights", "")
    insight_html = ""
    if insights:
        preview = insights[:200].strip() + ("…" if len(insights) > 200 else "")
        insight_html = (
            f'<div style="margin-top:14px;font-size:12px;color:#6e6e73;line-height:1.6">'
            f'{preview}</div>'
        )
    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'Baseline KPIs</div>{grid}{insight_html}'
    )
```

- [ ] **Step 3: Append `render_weather_panel()`**

```python
def render_weather_panel(state: Dict[str, Any]) -> str:
    risk = state.get("weather_risk", {})
    per_wp = risk.get("per_waypoint", [])
    route_score = risk.get("route_risk_score_0_3", risk.get("risk_score_0_3", 0))
    RISK_COLORS  = {0: "#30d158", 1: "#30d158", 2: "#ff9f0a", 3: "#ff453a"}
    RISK_LABELS  = {0: "Clear",   1: "Low",     2: "Moderate", 3: "High"}

    def score_val(s: Any) -> int:
        try:
            return int(s)
        except (TypeError, ValueError):
            return 0

    if per_wp:
        rows = "".join(
            f'<tr>'
            f'<td style="padding:7px 10px;color:#aeaeb2;font-size:12px">{w.get("waypoint","")}</td>'
            f'<td style="padding:7px 10px;color:#f5f5f7;font-size:12px">{w.get("city","")}, {w.get("state","")}</td>'
            f'<td style="padding:7px 10px;font-size:12px;'
            f'color:{RISK_COLORS.get(score_val(w.get("risk_score_0_3",0)),"#6e6e73")}">'
            f'{RISK_LABELS.get(score_val(w.get("risk_score_0_3",0)),"—")}</td>'
            f'<td style="padding:7px 10px;font-size:12px;color:#6e6e73">'
            f'{w.get("max_precip_mm_day","—")} mm/d &nbsp;{w.get("max_wind_gust_kmh","—")} km/h gust</td>'
            f'</tr>'
            for w in per_wp
        )
        table = (
            f'<table style="width:100%;border-collapse:collapse">'
            f'<thead><tr>'
            f'<th style="text-align:left;padding:6px 10px;font-size:11px;color:#48484a;font-weight:500">WP</th>'
            f'<th style="text-align:left;padding:6px 10px;font-size:11px;color:#48484a;font-weight:500">Location</th>'
            f'<th style="text-align:left;padding:6px 10px;font-size:11px;color:#48484a;font-weight:500">Risk</th>'
            f'<th style="text-align:left;padding:6px 10px;font-size:11px;color:#48484a;font-weight:500">Conditions</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>'
        )
    else:
        sv = score_val(route_score)
        table = (
            f'<div style="text-align:center;padding:20px">'
            f'<div style="font-size:32px;color:{RISK_COLORS.get(sv,"#6e6e73")};font-weight:700">'
            f'{RISK_LABELS.get(sv,str(route_score))}</div>'
            f'<div style="font-size:12px;color:#6e6e73;margin-top:6px">Route risk score: {route_score}/3</div>'
            f'</div>'
        )

    sv = score_val(route_score)
    route_label = (
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'I-95 Corridor Waypoints — Route risk: '
        f'<span style="color:{RISK_COLORS.get(sv,\"#6e6e73\")}">'
        f'{RISK_LABELS.get(sv, str(route_score))}</span></div>'
    )
    return _card(route_label + table)
```

- [ ] **Step 4: Append `render_what_if_panel()`**

```python
def render_what_if_panel(state: Dict[str, Any]) -> str:
    baseline = state.get("csv_kpis", {})
    scenario = state.get("scenario_kpis", {})
    summary  = state.get("what_if_summary", "")

    b_ontime = baseline.get("on_time_rate_pct", 0)
    s_ontime = scenario.get("on_time_rate_pct", 0)
    b_breach = baseline.get("cold_chain_breach_rate_pct", 0)
    s_breach = scenario.get("cold_chain_breach_rate_pct", 0)
    b_risk   = baseline.get("shipments_at_risk", 0)
    s_risk   = scenario.get("shipments_at_risk", 0)

    def _dc(delta: float, lower_is_better: bool = False) -> str:
        if lower_is_better:
            return "#30d158" if delta <= 0 else "#ff453a"
        return "#30d158" if delta >= 0 else "#ff453a"

    d_on  = s_ontime - b_ontime
    d_br  = s_breach - b_breach
    d_rk  = s_risk   - b_risk

    comparison = (
        f'<div style="display:flex;gap:14px;align-items:stretch">'
        f'<div style="flex:1;background:#1a1a1c;border-radius:10px;padding:16px">'
        f'<div style="font-size:11px;color:#6e6e73;margin-bottom:10px;font-weight:500">Baseline</div>'
        f'<div style="font-size:13px;color:#aeaeb2">On-time: <b style="color:#30d158">{b_ontime:.1f}%</b></div>'
        f'<div style="font-size:13px;color:#aeaeb2;margin-top:5px">Breach: <b>{b_breach:.1f}%</b></div>'
        f'<div style="font-size:13px;color:#aeaeb2;margin-top:5px">At-risk: <b>{b_risk}</b></div>'
        f'</div>'
        f'<div style="display:flex;align-items:center;font-size:20px;color:#3a3a3c">&#8594;</div>'
        f'<div style="flex:1;background:#1a1a1c;border-radius:10px;padding:16px">'
        f'<div style="font-size:11px;color:#6e6e73;margin-bottom:10px;font-weight:500">Scenario</div>'
        f'<div style="font-size:13px;color:#aeaeb2">On-time: '
        f'<b style="color:{_dc(d_on)}">{s_ontime:.1f}%</b>'
        f' <span style="font-size:11px;color:{_dc(d_on)}">({d_on:+.1f}%)</span></div>'
        f'<div style="font-size:13px;color:#aeaeb2;margin-top:5px">Breach: '
        f'<b style="color:{_dc(d_br,True)}">{s_breach:.1f}%</b>'
        f' <span style="font-size:11px;color:{_dc(d_br,True)}">({d_br:+.1f}%)</span></div>'
        f'<div style="font-size:13px;color:#aeaeb2;margin-top:5px">At-risk: '
        f'<b style="color:{_dc(d_rk,True)}">{s_risk}</b>'
        f' <span style="font-size:11px;color:{_dc(d_rk,True)}">({d_rk:+})</span></div>'
        f'</div>'
        f'</div>'
    )
    summary_html = ""
    if summary:
        preview = summary[:240].strip() + ("…" if len(summary) > 240 else "")
        summary_html = (
            f'<div style="margin-top:12px;font-size:12px;color:#6e6e73;line-height:1.6">'
            f'{preview}</div>'
        )
    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'Baseline vs Scenario KPIs</div>{comparison}{summary_html}'
    )
```

- [ ] **Step 5: Append `render_stakeholder_panel()` with SVG network**

```python
# Persona positions in SVG viewBox 400×270
_PERSONA_XY: Dict[str, Tuple[int, int]] = {
    "HospitalAdmin":       (200, 28),
    "CFO":                 (44,  100),
    "Dispatcher":          (356, 100),
    "WarehouseManager":    (44,  200),
    "ComplianceOfficer":   (356, 200),
    "Driver":              (200, 248),
}
_CENTER_XY = (200, 132)


def _stakeholder_svg(reactions: Dict[str, str]) -> str:
    edges = "".join(
        f'<line x1="{_CENTER_XY[0]}" y1="{_CENTER_XY[1]}" x2="{x}" y2="{y}" '
        f'stroke="#30d15838" stroke-width="1.5"/>'
        for x, y in _PERSONA_XY.values()
    )
    nodes = ""
    for name, (x, y) in _PERSONA_XY.items():
        # Short two-line label
        parts = [c for c in __import__("re").findall(r"[A-Z][a-z]+", name)]
        line1 = parts[0] if parts else name
        line2 = parts[1] if len(parts) > 1 else ""
        done  = name in reactions
        fill   = "#1c3a24" if done else "#1a1a1c"
        stroke = "#30d158" if done else "#3a3a3c"
        nodes += (
            f'<circle cx="{x}" cy="{y}" r="22" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'<text x="{x}" y="{y - 5}" text-anchor="middle" fill="#f5f5f7" '
            f'font-size="8" font-family="-apple-system,sans-serif">{line1}</text>'
            f'<text x="{x}" y="{y + 8}" text-anchor="middle" fill="#aeaeb2" '
            f'font-size="7" font-family="-apple-system,sans-serif">{line2}</text>'
        )
    cx, cy = _CENTER_XY
    synthesis = (
        f'<polygon points="{cx},{cy-22} {cx+28},{cy} {cx},{cy+22} {cx-28},{cy}" '
        f'fill="#1a2a3a" stroke="#0a84ff" stroke-width="1.5"/>'
        f'<text x="{cx}" y="{cy-3}" text-anchor="middle" fill="#f5f5f7" '
        f'font-size="8" font-family="-apple-system,sans-serif">Synthesis</text>'
        f'<text x="{cx}" y="{cy+9}" text-anchor="middle" fill="#6e6e73" '
        f'font-size="7" font-family="-apple-system,sans-serif">Agent</text>'
    )
    return (
        f'<svg viewBox="0 0 400 276" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:420px;display:block;margin:0 auto">'
        f'{edges}{nodes}{synthesis}</svg>'
    )


def render_stakeholder_panel(state: Dict[str, Any]) -> str:
    reactions  = state.get("stakeholder_reactions", {})
    synthesis  = state.get("stakeholder_synthesis", "")
    svg        = _stakeholder_svg(reactions)

    reaction_items = ""
    if reactions:
        items = "".join(
            f'<div style="margin-bottom:8px">'
            f'<span style="font-size:11px;color:#30d158;font-weight:500">{name}</span>'
            f'<div style="font-size:12px;color:#aeaeb2;line-height:1.5;margin-top:2px">'
            f'{txt[:150]}{"…" if len(txt)>150 else ""}</div></div>'
            for name, txt in reactions.items()
        )
        reaction_items = (
            f'<div style="margin-top:14px;border-top:1px solid #1d1d1f;padding-top:14px">'
            f'{items}</div>'
        )
    synth_html = ""
    if synthesis:
        synth_html = (
            f'<div style="margin-top:12px;background:#1a1a1c;border-radius:8px;padding:12px">'
            f'<div style="font-size:11px;color:#0a84ff;margin-bottom:6px;font-weight:500">Synthesis</div>'
            f'<div style="font-size:12px;color:#aeaeb2;line-height:1.6">'
            f'{synthesis[:240]}{"…" if len(synthesis)>240 else ""}</div></div>'
        )
    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'6-Persona Reaction Network</div>{svg}{reaction_items}{synth_html}'
    )
```

- [ ] **Step 6: Append `render_planner_panel()`, `render_judge_panel()`, `render_report_panel()`**

```python
def render_planner_panel(state: Dict[str, Any]) -> str:
    plan  = state.get("dispatch_plan", "")
    lines = [l.strip() for l in plan.splitlines() if l.strip()][:8]
    items = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px">'
        f'<span style="color:#30d158;font-size:12px;flex-shrink:0;margin-top:2px">&#8250;</span>'
        f'<span style="font-size:13px;color:#aeaeb2;line-height:1.5">{l[:130]}</span>'
        f'</div>'
        for l in lines
    )
    if not items:
        items = '<div style="font-size:12px;color:#48484a">Generating dispatch plan…</div>'
    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'Dispatch plan summary</div>{items}'
    )


def render_judge_panel(state: Dict[str, Any]) -> str:
    verdict    = state.get("audit_verdict", "")
    retries    = state.get("audit_retries", 0)
    violations = state.get("audit_violations", [])

    if verdict == "pass":
        verdict_html = (
            f'<div style="background:#1c3a24;border-radius:10px;padding:14px 18px;'
            f'display:flex;align-items:center;gap:12px">'
            f'<span style="font-size:22px;color:#30d158">&#10003;</span>'
            f'<div><div style="font-size:14px;color:#30d158;font-weight:600">Plan Approved</div>'
            f'<div style="font-size:12px;color:#6e6e73;margin-top:2px">Passed after {retries} revision(s)</div>'
            f'</div></div>'
        )
    elif verdict == "fail":
        verdict_html = (
            f'<div style="background:#2a1a1a;border-radius:10px;padding:14px 18px;'
            f'display:flex;align-items:center;gap:12px">'
            f'<span style="font-size:22px;color:#ff453a">&#9888;</span>'
            f'<div><div style="font-size:14px;color:#ff453a;font-weight:600">Max retries reached</div>'
            f'<div style="font-size:12px;color:#6e6e73;margin-top:2px">'
            f'Proceeding with best available plan ({retries} attempt(s))</div>'
            f'</div></div>'
        )
    else:
        verdict_html = (
            f'<div style="background:#1a1a1c;border-radius:10px;padding:14px 18px">'
            f'<div style="font-size:13px;color:#6e6e73">Verifying plan…</div></div>'
        )

    violation_html = ""
    if violations:
        pills = "".join(
            f'<span style="display:inline-block;background:#2a1a1a;color:#ff9f0a;'
            f'border-radius:6px;padding:4px 10px;font-size:11px;margin:3px">{v[:80]}</span>'
            for v in violations
        )
        violation_html = f'<div style="margin-top:12px">{pills}</div>'

    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'Audit result</div>{verdict_html}{violation_html}'
    )


def render_report_panel(state: Dict[str, Any]) -> str:
    report_html = state.get("report_html", "")
    if not report_html:
        return _card(
            '<div style="font-size:12px;color:#48484a">Generating executive report…</div>'
        )
    return _card(
        f'<div style="font-size:12px;color:#6e6e73;margin-bottom:10px;font-weight:500">'
        f'Executive Report</div>'
        f'<div style="background:#1a1a1c;border-radius:10px;padding:14px">'
        f'<div style="font-size:12px;color:#30d158;font-weight:500;margin-bottom:6px">Report generated</div>'
        f'<div style="font-size:12px;color:#6e6e73">Full executive report rendered below the pipeline.</div>'
        f'</div>'
    )
```

- [ ] **Step 7: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/ui_helpers.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git add src/ui_helpers.py
git commit -m "feat: add per-step HTML panel renderers to ui_helpers"
```

---

### Task 3: Add `build_pipeline_html()` to `src/ui_helpers.py`

**Files:**
- Modify: `src/ui_helpers.py`

- [ ] **Step 1: Append the panel dispatcher and `build_pipeline_html()`**

```python
# ── Panel dispatcher ───────────────────────────────────────────────────────────

_PANEL_RENDERERS: Dict[str, Any] = {}  # populated after all renderers defined (below)


def _init_renderers() -> None:
    global _PANEL_RENDERERS
    _PANEL_RENDERERS = {
        "pdf_context":     render_pdf_context_panel,
        "csv_analysis":    render_csv_analysis_panel,
        "weather":         render_weather_panel,
        "what_if":         render_what_if_panel,
        "stakeholder_sim": render_stakeholder_panel,
        "planner":         render_planner_panel,
        "judge":           render_judge_panel,
        "report":          render_report_panel,
    }


def _get_panel(node_key: str, state: Dict[str, Any]) -> str:
    if not _PANEL_RENDERERS:
        _init_renderers()
    fn = _PANEL_RENDERERS.get(node_key)
    return fn(state) if fn else ""


# ── Pipeline HTML builder ──────────────────────────────────────────────────────

_DISRUPTION_LABEL: Dict[str, str] = {
    "demand_spike":      "Demand Spike",
    "driver_shortage":   "Driver Shortage",
    "warehouse_closure": "Warehouse Closure",
    "weather_event":     "Weather Event",
}


def build_pipeline_html(
    completed: List[str],
    active: Optional[str],
    accumulated: Dict[str, Any],
    disruption_type: str = "demand_spike",
) -> str:
    """Return a self-contained HTML document rendering the 8-step pipeline."""
    connector = (
        '<div style="width:2px;height:18px;background:#1d1d1f;margin:0 auto"></div>'
    )
    nodes_html = ""
    for i, (key, title, subtitle) in enumerate(NODE_STEPS):
        is_done   = key in completed
        is_active = key == active

        if is_active:
            ind_bg, ind_fg  = "#f5f5f7", "#0a0a0a"
            ind_text        = str(i + 1)
            border          = "#2a2a2e"
            bg              = "#141414"
            title_col       = "#f5f5f7"
            sub_col         = "#6e6e73"
            opacity         = "1"
        elif is_done:
            ind_bg, ind_fg  = "#1c3a24", "#30d158"
            ind_text        = "&#10003;"
            border          = "#1d1d1f"
            bg              = "#111"
            title_col       = "#aeaeb2"
            sub_col         = "#48484a"
            opacity         = "1"
        else:
            ind_bg, ind_fg  = "#1d1d1f", "#3a3a3c"
            ind_text        = str(i + 1)
            border          = "transparent"
            bg              = "transparent"
            title_col       = "#48484a"
            sub_col         = "#3a3a3c"
            opacity         = "0.4"

        content = _get_panel(key, accumulated) if (is_done or is_active) else ""

        node_html = (
            f'<div id="step-{key}" style="'
            f'width:100%;padding:18px 24px;border-radius:14px;'
            f'border:1px solid {border};background:{bg};opacity:{opacity};'
            f'transition:all 0.35s cubic-bezier(0.4,0,0.2,1)">'
            f'<div style="display:flex;align-items:center;gap:18px">'
            f'<div style="width:36px;height:36px;border-radius:50%;'
            f'background:{ind_bg};color:{ind_fg};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:13px;font-weight:600;flex-shrink:0">{ind_text}</div>'
            f'<div style="flex:1">'
            f'<div style="font-size:15px;font-weight:500;color:{title_col}">{title}</div>'
            f'<div style="font-size:12px;color:{sub_col};margin-top:3px">{subtitle}</div>'
            f'</div></div>{content}</div>'
        )
        nodes_html += node_html
        if i < len(NODE_STEPS) - 1:
            nodes_html += connector

    # Status bar content
    dlabel     = _DISRUPTION_LABEL.get(disruption_type, disruption_type)
    n_done     = len(completed)
    n_total    = len(NODE_STEPS)
    if active:
        status_text = f"Running &mdash; {dlabel}"
        dot_style   = (
            'width:7px;height:7px;border-radius:50%;background:#30d158;'
            'box-shadow:0 0 6px #30d15880;animation:pulse 2s infinite;flex-shrink:0'
        )
    else:
        status_text = "Complete" if completed else "Ready"
        dot_style   = 'width:7px;height:7px;border-radius:50%;background:#3a3a3c;flex-shrink:0'

    # Auto-scroll target
    scroll_id = f"step-{active}" if active else (f"step-{completed[-1]}" if completed else "")
    scroll_js = (
        f'<script>window.addEventListener("load",function(){{'
        f'var el=document.getElementById("{scroll_id}");'
        f'if(el)el.scrollIntoView({{behavior:"smooth",block:"center"}});}});</script>'
    ) if scroll_id else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #0a0a0a;
       font-family: -apple-system,"SF Pro Display","Helvetica Neue",sans-serif;
       padding: 12px 0 48px; }}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.35}} }}
</style>
</head>
<body>
<div style="max-width:660px;margin:0 auto;padding:0 20px">
  <div style="margin-bottom:14px;padding:10px 16px;background:#111;border-radius:10px;
              border:1px solid #1d1d1f;display:flex;align-items:center;gap:10px">
    <div style="{dot_style}"></div>
    <span style="font-size:12px;color:#aeaeb2;font-weight:500">{status_text}</span>
    <span style="margin-left:auto;font-size:11px;color:#48484a">{n_done}/{n_total} steps</span>
  </div>
  {nodes_html}
</div>
{scroll_js}
</body>
</html>"""
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/ui_helpers.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/ui_helpers.py
git commit -m "feat: add build_pipeline_html to ui_helpers"
```

---

### Task 4: Rewrite `src/app.py`

**Files:**
- Modify: `src/app.py`

- [ ] **Step 1: Write the new app.py**

Replace the entire file with:

```python
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
# 4 type buttons + spacer + Run button
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

st.markdown("---")  # thin divider

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

# Restored state after a previous run (page refresh)
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

    # Show step 1 as active immediately
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
                active = completed[-1] if completed else None  # e.g. email node
            _show_pipeline(completed, active, accumulated)

    # All done
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
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/app.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/app.py
git commit -m "feat: rewrite app.py — Apple dark UI, streaming pipeline, disruption level controls"
```

---

### Task 5: Integration test

**Files:** None (read-only verification)

- [ ] **Step 1: Kill any running Streamlit instance, then launch**

```bash
pkill -f "streamlit run" 2>/dev/null; sleep 1; bash run_app.sh &
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
```

Expected: `200`

- [ ] **Step 2: Verify the Python import chain**

```bash
cd /Users/giulioelmi/Desktop/MSBA_AI_Agents_Demo && \
  PYTHONPATH=src python3 -c "from ui_helpers import build_pipeline_html, NODE_STEPS, DISRUPTIONS, PAGE_CSS; html = build_pipeline_html([], None, {}, 'demand_spike'); assert '<!DOCTYPE html>' in html; assert 'step-pdf_context' in html; print('ui_helpers import OK')"
```

Expected: `ui_helpers import OK`

- [ ] **Step 3: Verify disruption level wiring (unit check)**

```bash
cd /Users/giulioelmi/Desktop/MSBA_AI_Agents_Demo && python3 - <<'EOF'
from ui_helpers import DISRUPTIONS
for key, cfg in DISRUPTIONS.items():
    assert "kind" in cfg, f"missing kind for {key}"
    assert "param" in cfg, f"missing param for {key}"
    assert "label" in cfg, f"missing label for {key}"
print("DISRUPTIONS structure OK")
EOF
```

Expected: `DISRUPTIONS structure OK`

- [ ] **Step 4: Manual browser check**

Open http://localhost:8501.

Verify:
- Dark background, no Streamlit chrome (header/footer/sidebar hidden)
- "SeeWeeS / Ops Intelligence" brand text
- 4 disruption type buttons: "● Demand Spike", "○ Driver Shortage", "○ Warehouse Closure", "○ Weather Event"
- A slider labeled "Level — Demand Spike" with format "×1.2"
- A "Run" button
- Pipeline area shows 8 dimmed steps in a centered vertical column

- [ ] **Step 5: Test type switching**

Click "○ Driver Shortage" → verify slider changes label to "Level — Driver Shortage" with `%` format.
Click "○ Warehouse Closure" → verify a selectbox replaces the slider.
Click "○ Weather Event" → verify integer slider 0–3.

- [ ] **Step 6: Run the pipeline end-to-end**

Click "● Demand Spike" → set multiplier to ×1.5 → click Run.

Verify:
- Step 1 immediately shows as active (white indicator, full opacity)
- Steps complete one by one with green checkmarks; pipeline auto-scrolls to active step
- Step 4 (What-If) shows baseline vs scenario KPI cards with colored deltas
- Step 5 (Stakeholder Sim) shows the SVG network with 6 persona circles (green when done) and a blue synthesis diamond
- Step 7 (Judge/Audit) shows a green "Plan Approved" block or an amber "Max retries" block
- After all 8 steps, the executive report renders below the pipeline

- [ ] **Step 7: Commit final verification note**

```bash
git add -A
git status
```

If clean (no untracked or modified files), the implementation is complete. If there are any uncommitted changes from debug edits, commit them:

```bash
git commit -am "chore: final cleanup after integration test"
```
