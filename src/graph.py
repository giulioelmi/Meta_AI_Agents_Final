from __future__ import annotations

import os
import re
from typing import TypedDict, Dict, Any, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from tools.pdf_tools import PdfRag
from tools.csv_tools import analyze_csv
from tools.weather_tools import get_weather_forecast, derive_dispatch_weather_risk
from tools.email_tools import send_email_smtp
from agents import run_context_agent, run_ops_agent, run_planner_agent, run_report_agent
from nodes.what_if import node_what_if
from nodes.stakeholder_sim import node_stakeholder_sim
from nodes.judge import node_judge, node_revise, route_after_judge

load_dotenv()


class AppState(TypedDict, total=False):
    pdf_path: str
    csv_path: str

    business_context: str

    csv_summary: Dict[str, Any]
    csv_kpis: Dict[str, Any]
    anomalies_md: str
    ops_insights: str
    augmented_df_json: str          # augmented DataFrame serialized as JSON string

    weather_risk: Dict[str, Any]

    # What-if scenario
    disruption_type: str            # "demand_spike" | "driver_shortage" | "warehouse_closure" | "weather_event"
    disruption_params: Dict[str, Any]
    scenario_kpis: Dict[str, Any]
    what_if_summary: str

    # Stakeholder simulation
    stakeholder_reactions: Dict[str, str]   # persona_name -> reaction text
    stakeholder_synthesis: str

    # Planner + audit loop
    dispatch_plan: str
    audit_verdict: str              # "pass" | "fail"
    audit_violations: List[str]
    audit_retries: int

    report_html: str


def node_pdf_context(state: AppState) -> AppState:
    rag = PdfRag(persist_dir="chroma_db")
    vectordb = rag.build(state["pdf_path"])
    retriever = rag.retriever(vectordb, k=6)

    query = "Extract KPI definitions, thresholds, SLAs, constraints, dispatch rules, exceptions."
    docs = retriever.invoke(query)
    snippets = "\n\n---\n\n".join(d.page_content for d in docs)

    business_context = run_context_agent(snippets)
    return {"business_context": business_context}


def node_csv_analysis(state: AppState) -> AppState:
    res = analyze_csv(state["csv_path"])

    anomalies_md = "(none detected or insufficient numeric data)"
    if not res.anomalies.empty:
        anomalies_md = res.anomalies.head(12).to_markdown(index=False)

    ops_insights = run_ops_agent(summary=res.summary, kpis=res.kpis, anomalies_md=anomalies_md)

    return {
        "csv_summary": res.summary,
        "csv_kpis": res.kpis,
        "anomalies_md": anomalies_md,
        "ops_insights": ops_insights,
        "augmented_df_json": res.augmented_df.to_json(),
    }


# --- Waypoint parsing helpers (extract W1..W5 rows from PDF-retrieved text) ---
WAYPOINT_RE = re.compile(
    r"(W[1-9]\d*)\s+([A-Za-z][A-Za-z\s\-\.,]*)\s+([A-Z]{2})\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)",
    re.MULTILINE
)


def _parse_waypoints_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract rows like:
      W1 Newark NJ 40.7357 -74.1724
      W3 New Haven CT 41.3083 -72.9279
    from arbitrary text. Returns sorted list by waypoint number.
    """
    wps: List[Dict[str, Any]] = []
    for m in WAYPOINT_RE.finditer(text):
        wid, city, state, lat, lon = m.groups()
        wps.append(
            {
                "id": wid.strip(),
                "city": city.strip(),
                "state": state.strip(),
                "lat": float(lat),
                "lon": float(lon),
            }
        )

    def wp_key(w: Dict[str, Any]) -> int:
        n = re.sub(r"\D", "", w["id"])
        return int(n) if n else 0

    wps.sort(key=wp_key)
    return wps


def node_weather(state: AppState) -> AppState:
    tz = os.getenv("WEATHER_TZ", "America/New_York")

    # Retrieve waypoint table from the PDF using PdfRag
    rag = PdfRag(persist_dir="chroma_db")
    vectordb = rag.build(state["pdf_path"])
    retriever = rag.retriever(vectordb, k=20)

    wp_query = (
    "Find the section titled 'Route Definition' or 'Waypoints' or 'I-95 Corridor Waypoints'. "
    "Return the waypoint list including W1, W2, W3, W4, W5 and their latitude and longitude."
    )
    docs = retriever.invoke(wp_query)
    wp_text = "\n".join(d.page_content for d in docs)
    print("\n===== WAYPOINT RETRIEVAL (RAW) =====")
    print(wp_text[:1200])
    print("===================================\n")
    waypoints = _parse_waypoints_from_text(wp_text)

    # Fallback if parsing is weak or incomplete
    if len(waypoints) < 5:
        print(f"Waypoint extraction failed (found {len(waypoints)}). Falling back to WEATHER_LAT/LON.")
        lat = os.getenv("WEATHER_LAT", "40.7282")
        lon = os.getenv("WEATHER_LON", "-74.0776")
        forecast = get_weather_forecast(lat, lon, tz)
        risk = derive_dispatch_weather_risk(forecast)
        print("\n===== WEATHER_RISK DEBUG (FALLBACK) =====")
        print(forecast)
        print(risk)
        print("=========================================\n")
        return {"weather_risk": risk}

    # Compute per-waypoint risk and roll up to route-level risk (max score)
    per_waypoint: List[Dict[str, Any]] = []
    worst: Dict[str, Any] | None = None
    max_score = -1

    for wp in waypoints:
        forecast = get_weather_forecast(str(wp["lat"]), str(wp["lon"]), tz)
        risk = derive_dispatch_weather_risk(forecast)
        enriched = {"waypoint": wp["id"], "city": wp["city"], "state": wp["state"], **risk}
        per_waypoint.append(enriched)

        if enriched.get("risk_score_0_3", -1) > max_score:
            max_score = enriched["risk_score_0_3"]
            worst = enriched

    route_risk: Dict[str, Any] = {
        "route_risk_score_0_3": max_score,
        "worst_waypoint": worst,
        "per_waypoint": per_waypoint,
    }

    # Backwards compatibility (expose worst waypoint metrics using the original schema)
    if worst:
        route_risk.update(
            {
                "max_precip_mm_day": worst.get("max_precip_mm_day"),
                "max_wind_gust_kmh": worst.get("max_wind_gust_kmh"),
                "min_temp_c": worst.get("min_temp_c"),
                "risk_flags": worst.get("risk_flags"),
                "risk_score_0_3": worst.get("risk_score_0_3"),
            }
        )
    print("\n===== WEATHER_RISK DEBUG =====")
    print(route_risk)
    print("================================\n")
    return {"weather_risk": route_risk}


def node_planner(state: AppState) -> AppState:
    plan = run_planner_agent(
        business_context=state.get("business_context", ""),
        ops_insights=state.get("ops_insights", ""),
        weather_risk=state.get("weather_risk", {}),
        what_if_summary=state.get("what_if_summary", ""),
        scenario_kpis=state.get("scenario_kpis", {}),
        stakeholder_synthesis=state.get("stakeholder_synthesis", ""),
    )
    return {"dispatch_plan": plan, "audit_retries": 0}


def node_report(state: AppState) -> AppState:
    html = run_report_agent(
        business_context=state.get("business_context", ""),
        kpis=state.get("csv_kpis", {}),
        anomaly_highlights=state.get("anomalies_md", "(none)"),
        weather_risk=state.get("weather_risk", {}),
        dispatch_plan=state.get("dispatch_plan", ""),
    )
    return {"report_html": html}


def node_email(state: AppState) -> AppState:
    to_email = os.getenv("REPORT_EMAIL_TO", "").strip()
    if not to_email:
        print("REPORT_EMAIL_TO not set -> skipping email send.")
        return {}

    subject = "MSBA Ops Multi-Agent Dispatch Report"
    send_email_smtp(subject=subject, html_body=state["report_html"], to_email=to_email)
    return {}


def build_graph():
    g = StateGraph(AppState)

    g.add_node("pdf_context",      node_pdf_context)
    g.add_node("csv_analysis",     node_csv_analysis)
    g.add_node("weather",          node_weather)
    g.add_node("what_if",          node_what_if)
    g.add_node("stakeholder_sim",  node_stakeholder_sim)
    g.add_node("planner",          node_planner)
    g.add_node("judge",            node_judge)
    g.add_node("revise_plan",      node_revise)
    g.add_node("report",           node_report)
    g.add_node("email",            node_email)

    g.set_entry_point("pdf_context")
    g.add_edge("pdf_context",     "csv_analysis")
    g.add_edge("csv_analysis",    "weather")
    g.add_edge("weather",         "what_if")
    g.add_edge("what_if",         "stakeholder_sim")
    g.add_edge("stakeholder_sim", "planner")
    g.add_edge("planner",         "judge")
    g.add_conditional_edges("judge", route_after_judge, {
        "report":      "report",
        "revise_plan": "revise_plan",
    })
    g.add_edge("revise_plan",     "judge")
    g.add_edge("report",          "email")
    g.add_edge("email",           END)

    return g.compile()