# src/prompts_advanced.py
from langchain_core.prompts import ChatPromptTemplate

WHAT_IF_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ScenarioAgent. Given a disruption scenario and its KPI impact, write a concise 3-bullet "
     "operational summary explaining what changed and why it matters for SeeWeeS dispatch decisions."),
    ("user",
     "Disruption: {disruption_type} with params {disruption_params}\n\n"
     "Baseline KPIs:\n{baseline_kpis}\n\n"
     "Scenario KPIs:\n{scenario_kpis}\n\n"
     "Business context:\n{business_context}\n\n"
     "Summarize the impact in 3 bullets.")
])
