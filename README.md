# SeeWeeS Multi-Agent Ops Reporting System
### UCLA MSBA AI Agents Project Challenge 2026
 
## Executive Summary
 
SeeWeeS is a specialty medicine distributor responsible for time-critical deliveries across hospital networks in the northeastern U.S. The core operational challenge: dispatch decisions must account for shipment data, contractual SLAs, real-time weather risk, and resource constraints — all simultaneously. The original prototype handled this in a single linear pass, with no ability to handle disruptions, validate its own output, or simulate what-if scenarios.
 
This project transforms that prototype into a **robust multi-agent LangGraph system** targeting two key enhancements from the project brief:
 
- **Enhancement #1 — Self-Correction & Quality Assurance:** An Audit Loop where a Judge Agent reviews the Planner's dispatch plan against PDF-extracted business rules and cycles back for revision before any report is finalized.
- **Enhancement #2 — What-If Scenario Simulation:** A What-If Agent that applies operational disruptions (demand spikes, driver shortages, warehouse closures, weather events) and computes scenario-specific KPI deltas and contingency recommendations.
**Primary stakeholder:** SeeWeeS Operations Leadership (VP of Logistics / Dispatch Managers) who need fast, grounded, decision-ready reports when disruptions occur.

## Key Assumptions
 
**Logistics & Operations**
- All shipments in `Incoming_shipment_03_06.csv` (86 shipments) are assumed to be active and unconfirmed unless flagged otherwise.
- Hospital priority levels are inferred from shipment urgency flags and SLA windows in the Dispatch Playbook PDF; no external hospital ranking data is used.
- Route waypoints (e.g., I-95 corridor checkpoints) are parsed from the PDF playbook and used as latitude/longitude inputs to the weather API.

**Weather Risk**
- Weather risk scores (0–3) are derived from Open-Meteo forecast data at parsed route waypoints.
- A risk score of 2 triggers a warning in the plan; a score of 3 mandates escalation per the SeeWeeS Dispatch Playbook business rule: *"Must escalate if Risk Score is 3."*
- Fallback coordinates (`WEATHER_LAT=40.7282`, `WEATHER_LON=-74.0776`) represent the Newark, NJ corridor hub when waypoints cannot be parsed from the PDF.

**What-If Disruptions**
- `demand_spike`: multiplies expected shipment volume by the provided `--multiplier` (default 1.2×).
- `driver_shortage`: removes the specified `--shortage-pct` percentage of available drivers uniformly at random.
- `warehouse_closure`: marks the specified `--location` warehouse as unavailable and re-routes affected shipments.
- `weather_event`: injects a synthetic weather risk score of `--risk-score` onto all active routes.
  
**Data Availability**
- No live ERP or TMS data is available; all inputs are static CSV and PDF files.
- Stakeholder personas (Operations Manager, Compliance Officer, CFO) are simulated via LLM prompting rather than real human input.
- ChromaDB is used as a local vector store for RAG over PDF documents; the index is rebuilt on each run if not cached.

## KPI Definitions
 
| KPI | Formula | Risk Threshold |
|---|---|---|
| **On-Time Delivery Rate (OTD)** | `Shipments delivered within SLA window / Total shipments` | < 95% = at risk |
| **Disruption Impact Score** | `(Scenario KPI − Baseline KPI) / Baseline KPI × 100` | > 10% delta = escalate |
| **Route Weather Risk** | Max Open-Meteo risk score across all waypoints on a route (0–3) | ≥ 2 = warning; 3 = mandatory escalation |
| **Driver Utilization Rate** | `Assigned shipments / Available driver capacity` | > 90% = overloaded |
| **Audit Pass Rate** | `Plans passing Judge Agent on first review / Total plans generated` | < 80% = prompt/logic review needed |
 
## Project Structure

```text
data/
  Incoming_shipment_03_06.csv       Raw shipment data (86 shipments)
  SeeWeeS Specialty Dispatch Playbook.pdf
  About SeeWeeS Specialty distribution.pdf
src/main.py            CLI entry point
src/graph.py           LangGraph workflow
src/agents.py          LLM agent wrappers
src/prompts*.py        Agent prompt templates
src/nodes/             What-if, stakeholder, and audit nodes
src/tools/             PDF, CSV, KPI, weather, and report helpers
tests/                 Unit tests for deterministic logic
requirements.txt       Python dependencies
.env.example           Environment variable template
```

Generated files such as `dispatch_report_*.pdf`, `chroma_db/`, `__pycache__/`, and `.pytest_cache/` are intentionally ignored.

## Agentic Flow

The system is a directed LangGraph workflow with a **cyclic audit loop** — a deliberate departure from linear pipelines. The cycle between Judge and Revise ensures the final dispatch plan is grounded in the business rules extracted from the PDF before any output reaches the report layer.

```mermaid
flowchart TD
    Start([CLI run with disruption scenario])
    Inputs[(PDF playbook + shipment CSV)]
    PDF[PDF Context Agent<br/>RAG extracts SLAs, rules, thresholds]
    CSV[Ops Analysis Agent<br/>Computes KPIs and anomaly highlights]
    Weather[Weather Risk Node<br/>Checks route waypoint forecast risk]
    WhatIf[What-If Agent<br/>Applies disruption and compares scenario KPIs]
    Stakeholders[Stakeholder Simulation<br/>Runs persona reactions in parallel]
    Planner[Planner Agent<br/>Creates dispatch recovery plan]
    Judge[Judge / Audit Agent<br/>Checks plan against business rules]
    Revise[Revise Agent<br/>Fixes audit violations]
    Report[Report Agent<br/>Builds executive report text]
    PDFOut[(dispatch_report_YYYYMMDD_HHMMSS.pdf)]

    Start --> Inputs
    Inputs --> PDF
    PDF --> CSV
    CSV --> Weather
    Weather --> WhatIf
    WhatIf --> Stakeholders
    Stakeholders --> Planner
    Planner --> Judge
    Judge -- pass or max retries --> Report
    Judge -- fail and retries remain --> Revise
    Revise --> Judge
    Report --> PDFOut
```

## Requirements

Use Python 3.11 or newer. The app requires:

- an OpenAI API key
- internet access for OpenAI and Open-Meteo API calls

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your API key:

```text
OPENAI_API_KEY="your_openai_api_key_here"
```

Optional overrides (all have sensible defaults):

| Variable | Default | Purpose |
|---|---|---|
| `WEATHER_TZ` | `America/New_York` | Timezone for Open-Meteo forecasts |
| `WEATHER_LAT` | `40.7282` | Fallback latitude if PDF waypoints cannot be parsed |
| `WEATHER_LON` | `-74.0776` | Fallback longitude |

## Run

```bash
python src/main.py --disruption demand_spike
```

Supported scenarios:

```bash
python src/main.py --disruption demand_spike --multiplier 1.3
python src/main.py --disruption driver_shortage --shortage-pct 30
python src/main.py --disruption warehouse_closure --location Boston-MGH
python src/main.py --disruption weather_event --risk-score 2
```

The command prints each pipeline step and writes `dispatch_report_YYYYMMDD_HHMMSS.pdf` to the project folder.

## Test

```bash
PYTHONPATH=src pytest
```

# SeeWeeS Dispatch Report Dashboard

Standalone Next.js prototype for the UCLA MSBA AI Agents Project Challenge dashboard.

The dashboard uses static KPI snapshots from the completed teammate LangGraph pipeline. It does not import Python code, CSV files, PDFs, generated reports, or anything outside this `web/` folder, so the folder can be moved into another repository and still run independently.

## Local Development

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Build

```bash
npm run build
```

## Vercel

Deploy this folder as the Vercel project root.

## Data Source

The static scenario data lives in `lib/scenarios.ts` and reflects these teammate pipeline scenarios:

- Demand Spike x1.2
- Driver Shortage: 30% unavailable
- Warehouse Closure: Boston-MGH
- Weather Event: risk 2/3

If the Python pipeline outputs new KPI results later, update `lib/scenarios.ts` and rebuild the app.

## Notes

Do not commit `.env` or API keys. The PDF vector index in `chroma_db/` is a local cache and can be rebuilt by rerunning the app.
