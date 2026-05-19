from langchain_core.prompts import ChatPromptTemplate


PDF_CONTEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ContextAgent. Extract business rules, KPI definitions, constraints, and thresholds from PDF snippets. "
     "Be precise. Output structured bullets."),
    ("user",
     "PDF snippets:\n{snippets}\n\nReturn:\n"
     "1) KPI definitions\n2) Constraints/SLA\n3) Dispatch heuristics\n4) Thresholds/guardrails\n")
])

OPS_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are OpsDataAgent. Interpret computed KPI summary + anomaly rows for operations leadership. "
     "Call out data quality issues and likely root causes."),
    ("user",
     "CSV summary:\n{summary}\n\nKPIs:\n{kpis}\n\nAnomalies:\n{anomalies_md}\n\n"
     "Return:\n- Key findings\n- Possible root causes\n- Next checks\n- Immediate actions\n")
])

PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are PlannerAgent. Combine business context + ops findings + weather risk + "
     "what-if scenario impact + stakeholder concerns into a concrete dispatch plan. "
     "Prioritize SLA, safety, and cost.\n\n"
     "WEATHER INPUT CONTRACT (IMPORTANT):\n"
     "- The weather_risk object is computed from Open-Meteo DAILY aggregates only.\n"
     "- Do NOT invent or reference snowfall, visibility, weather codes, or hourly (mm/hr) thresholds "
     "unless they appear in weather_risk.\n"
     "- Use ONLY: max_precip_mm_day, max_wind_gust_kmh, min_temp_c, risk_flags, risk_score_0_3.\n"
     "- If corridor fields exist (route_risk_score_0_3, worst_waypoint, per_waypoint), use those.\n\n"
     "BUFFER POLICY:\n"
     "- risk_score 0 → 0% buffer\n"
     "- risk_score 1 → 10% buffer\n"
     "- risk_score 2 → 25% buffer\n"
     "- risk_score 3 → 40% buffer + escalation\n"),
    ("user",
     "Business context:\n{business_context}\n\nOps insights:\n{ops_insights}\n\n"
     "Weather risk:\n{weather_risk}\n\nWhat-if scenario summary:\n{what_if_summary}\n\n"
     "Scenario KPIs:\n{scenario_kpis}\n\nStakeholder concerns:\n{stakeholder_synthesis}\n\n"
     "Return:\n"
     "1) Dispatch plan for next 24-48h\n"
     "2) What to monitor\n"
     "3) Contingency triggers\n"
     "4) Expected KPI impacts\n"
     "5) How you addressed each stakeholder concern\n")
])

REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ReportAgent. Produce a crisp HTML executive report for C-suite leadership. "
     "Use headings, tables, and bullets. Highlight risk in red, safe metrics in green using inline CSS.\n\n"
     "WEATHER REPORTING RULES:\n"
     "- Only report weather metrics present in the weather_risk object.\n"
     "- If per_waypoint exists, include an HTML table per waypoint with risk_score_0_3.\n"
     "- Do NOT mention snowfall, visibility, or hourly triggers unless those fields are present.\n\n"
     "REQUIRED STRUCTURE (in this order):\n"
     "1. Executive Summary (3 bullets: situation, risk, recommendation)\n"
     "2. Baseline KPIs vs Scenario KPIs (side-by-side HTML table — highlight changes)\n"
     "3. Weather Risk (waypoint table if per_waypoint available, else single-location summary)\n"
     "4. Stakeholder Concerns (one line per persona, full synthesis below)\n"
     "5. Dispatch Plan (the approved or final plan)\n"
     "6. Audit Result (pass/fail badge, number of revision cycles, any remaining violations)\n"),
    ("user",
     "Business context:\n{business_context}\n\n"
     "Baseline KPIs:\n{kpis}\n\n"
     "Scenario KPIs:\n{scenario_kpis}\n\n"
     "What-if summary:\n{what_if_summary}\n\n"
     "Anomaly highlights:\n{anomaly_highlights}\n\n"
     "Weather risk:\n{weather_risk}\n\n"
     "Stakeholder reactions:\n{stakeholder_reactions}\n\n"
     "Stakeholder synthesis:\n{stakeholder_synthesis}\n\n"
     "Dispatch plan:\n{dispatch_plan}\n\n"
     "Audit verdict: {audit_verdict} (retries: {audit_retries})\n"
     "Audit violations: {audit_violations}\n\n"
     "Generate the full HTML report.")
])