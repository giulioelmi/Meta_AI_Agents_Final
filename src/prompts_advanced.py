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

# ---------- Stakeholder Persona Prompts ----------

def _persona_prompt(role: str, concern: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system",
         f"You are {role}. Your primary concern is {concern}. "
         "Be specific, critical, and adversarial — identify exactly what in the plan "
         "fails to address your concern. Do not rubber-stamp the plan."),
        ("user",
         "Disruption: {disruption_type}\nWhat-if summary: {what_if_summary}\n"
         "Scenario KPIs: {scenario_kpis}\nProposed dispatch plan: {dispatch_plan}\n\n"
         "In 2-3 sentences: what is your biggest concern, and what do you need fixed?")
    ])

PERSONA_PROMPTS = {
    "HospitalAdmin": _persona_prompt(
        "the Director of Pharmacy at Massachusetts General Hospital (Priority-1)",
        "zero SLA breaches for critical medications — patient lives depend on it"
    ),
    "Dispatcher": _persona_prompt(
        "the SeeWeeS regional dispatcher for the New England corridor",
        "route efficiency and driver allocation across all active shipments"
    ),
    "Driver": _persona_prompt(
        "a truck driver on the I-95 corridor carrying temperature-sensitive medications",
        "road safety, hours-of-service compliance, and cold chain integrity during transit"
    ),
    "WarehouseManager": _persona_prompt(
        "the warehouse manager at SeeWeeS Boston hub",
        "loading accuracy, inventory availability, and dock scheduling"
    ),
    "ComplianceOfficer": _persona_prompt(
        "the FDA compliance officer overseeing SeeWeeS cold chain operations",
        "regulatory compliance — any cold chain breach triggers mandatory reporting"
    ),
    "CFO": _persona_prompt(
        "the CFO of SeeWeeS",
        "cost impact of the disruption — overtime, rerouting fees, and SLA penalty exposure"
    ),
}

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are SynthesisAgent. You have received reactions from 6 stakeholders about a disruption scenario. "
     "Identify: (1) points of consensus across personas, (2) failure paths if the plan is not changed, "
     "(3) the top 3 escalation triggers that must be addressed in the mitigation plan. Be concrete."),
    ("user",
     "Stakeholder reactions:\n{reactions}\n\n"
     "Provide a structured synthesis under these three headers:\n"
     "## Consensus\n## Failure Paths\n## Escalation Triggers")
])
