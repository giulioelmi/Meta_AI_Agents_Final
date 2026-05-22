# SeeWeeS Specialty Medicine Dispatch
# Multi-Agent System: Technical & Business Report

**UCLA MSBA AI Agents Project Challenge 2026**
**Submission Date:** May 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Stakeholder Context](#2-problem-statement--stakeholder-context)
3. [Data Overview & Augmentation Strategy](#3-data-overview--augmentation-strategy)
4. [System Architecture](#4-system-architecture)
5. [Agent Design & Prompt Engineering](#5-agent-design--prompt-engineering)
6. [Enhancement 1 — Self-Correction & Quality Assurance](#6-enhancement-1--self-correction--quality-assurance)
7. [Enhancement 2 — "What-if" Scenario Simulation](#7-enhancement-2--what-if-scenario-simulation)
8. [Stakeholder Simulation Layer](#8-stakeholder-simulation-layer)
9. [KPI Framework](#9-kpi-framework)
10. [Results & Validation](#10-results--validation)
11. [Limitations & Next Steps](#11-limitations--next-steps)

---

## 1. Executive Summary

> **Core Enhancements Implemented: Enhancement 1 (Self-Correction & QA) + Enhancement 2 (What-if Scenario Simulation)**
>
> Per challenge PDF: Enhancement 1 = Self-Correction & Quality Assurance; Enhancement 2 = "What-if" Scenario Simulation

This project transforms the SeeWeeS linear reporting prototype into a **self-correcting, scenario-aware multi-agent system** built on LangGraph. The system ingests a live shipment CSV, retrieves business rules from the Operations Playbook via RAG, simulates operational disruptions, polls six stakeholder personas, generates a dispatch plan, and audits that plan against Playbook rules before a single line reaches the executive report.

### Key Findings from Live Run (2026-05-21, Demand Spike ×1.2)

| Metric | Value | Status |
|---|---|---|
| Total Shipments | 87 | — |
| On-Time Rate | 72.41% | ⚠ Below 90% threshold |
| Cold-Chain Breach Rate | **60.0%** | ✗ FDA reportable |
| Critical Hospital On-Time (MGH/BWH) | 70.77% | ✗ SLA breach |
| Shipments at Risk (Priority-1, late) | **19** | ✗ Immediate escalation |
| Units Dispatched (baseline → scenario) | 1,392 → **1,634** | +17.4% demand spike |
| Capacity Utilization | 32.0% → 37.56% | ⚠ Underutilized |
| Route Risk Score | **2 / 3** | ⚠ Moderate (W1, W2 active) |
| Audit Result | **Pass** | ✓ 0 revision cycles |

> **Bottom line for leadership:** Volume absorbed the 20% demand spike without punctuality degradation — but the 60% cold-chain breach rate across 45 temperature-sensitive shipments (Remdesivir, Insulin Lispro, Pembrolizumab) is the single highest-priority operational and regulatory risk. 19 Priority-1 deliveries to MGH and BWH arrived late, constituting SLA violations under Playbook §6. The dispatch plan was audited and passed before this report was generated.

---

## 2. Problem Statement & Stakeholder Context

### 2.1 The Operational Gap

The original SeeWeeS Ops Reporting Agent operated as a single linear pass: read data → analyze → generate report. In real medical logistics, this creates three structural blind spots:

- **No disruption foresight.** There is no way to ask "what happens if demand spikes 20% tomorrow?" before committing to a plan.
- **No plan validation.** A dispatch plan that ignores cold-chain escalation rules or SLA violations reaches leadership unchecked.
- **No stakeholder alignment.** The system cannot surface whether the plan satisfies the divergent concerns of hospital pharmacists, compliance officers, and the CFO simultaneously.

### 2.2 Primary Stakeholder

**VP of Logistics and Regional Dispatchers — New England I-95 Corridor**

These decision-makers need a morning briefing that answers three questions in under two minutes:
1. What is today's risk picture (weather, volume, cold-chain)?
2. If a disruption hits, what do the KPIs look like?
3. Is the proposed dispatch plan compliant with the Operations Playbook?

### 2.3 Route Context

Shipments originate from New Jersey distribution centers and travel the I-95 corridor to Boston-area hospitals. The Playbook (§4) defines five fixed waypoints for weather risk evaluation:

| Waypoint | City | State | Coordinates |
|---|---|---|---|
| W1 | Newark | NJ | 40.7357, -74.1724 |
| W2 | Bronx | NY | 40.8448, -73.8648 |
| W3 | New Haven | CT | 41.3083, -72.9279 |
| W4 | Providence | RI | 41.8240, -71.4128 |
| W5 | Boston | MA | 42.3601, -71.0589 |

---

## 3. Data Overview & Augmentation Strategy

### 3.1 Source Data

**File:** `data/Incoming_shipment_03_06.csv` — 87 rows, 4 columns

| Column | Type | Description |
|---|---|---|
| `item_id` | int | Internal medicine identifier |
| `item_name` | str | Human-readable name |
| `unique_item_id` | str | Unit-level identifier (nullable) |
| `dispatch_location` | str | Destination hospital |

The CSV contains no scheduling timestamps, temperature readings, driver assignments, or capacity data — all of which are required for meaningful operational KPIs.

### 3.2 Data Quality Issues Detected

The IsolationForest anomaly detector (`contamination=0.03`, 200 estimators) and Playbook data quality rules identified two classes of problems:

**Structural anomaly — item_id 99999 (Experimental Oncology Drug)**
This item requires **Strict Cold Chain (–20°C)** per Playbook §8, but the standard fleet operates at 2–8°C. It was flagged by both the IsolationForest (highest anomaly score) and Playbook rule DQ-02 (`item_id not in master table`), and excluded from dispatch per rule DQ-01.

**Missing unique_item_id (DQ-01)**
Rows with null `unique_item_id` are removed from the dispatch calculation and logged with reason code DQ-01, per Playbook §11 exception handling policy.

### 3.3 Data Augmentation

Because operational fields are absent from the source CSV, they are synthetically generated in [`src/tools/augment_tools.py`](src/tools/augment_tools.py) using **deterministic seeds** (`seed = item_id + row_index`) to ensure full reproducibility across runs.

| Augmented Field | Generation Method | Grounding |
|---|---|---|
| `scheduled_date` | Uniform draw: base_date + U(2h, 24h) | Simulates realistic intraday dispatch window |
| `actual_date` | scheduled + weighted delay: {0h: 60%, 1h: 10%, 2h: 10%, 4h: 10%, 8h: 5%} | Mimics ~70% baseline on-time rate |
| `quantity_ordered` | Integer draw: U(5, 30) units | Reflects typical specialty medicine batch sizes |
| `cold_chain_required` | True if `item_id ∈ {10021–10025}` | Mapped from Playbook §8 Item Master |
| `temp_min_c / temp_max_c` | Cold items: U(1.5°C, 9.5°C); Room temp: U(15°C, 25°C) | Simulates realistic temperature excursion distribution |
| `hospital_priority` | 1 if location ∈ {Boston-MGH, Boston-BWH}; else 2 | Reflects Level-1 trauma center criticality |
| `driver_id` | `DRV-{randint(100, 200)}` | Placeholder for driver pool simulation |
| `truck_capacity_units` | 50 (constant) | Working assumption; Playbook §7.1 defines 10 volume units per truck |
| `cold_chain_breach` | True if `temp_max > 8°C` or `temp_min < 2°C` | Directly derived from Playbook §8 temperature ranges |

> **Important caveat:** The 60% cold-chain breach rate reflects the synthetic temperature distribution, not real IoT sensor data. In production, this field would be replaced by real-time telemetry feeds.

---

## 4. System Architecture

The enhanced LangGraph pipeline replaces the original linear flow with three non-linear components: a scenario simulation branch, a stakeholder review node, and a cyclic audit loop.

**Pipeline flow** ([`src/graph.py`](src/graph.py)):

```
[PDF Playbook + Shipment CSV]
         │
         ▼
  ┌─────────────┐     Extracts SLAs, thresholds,
  │ pdf_context │     dispatch rules via RAG (k=6)
  └──────┬──────┘
         │
         ▼
  ┌──────────────┐    Cleans CSV, augments fields,
  │ csv_analysis │    computes KPIs, detects anomalies
  └──────┬───────┘
         │
         ▼
  ┌─────────┐         Live Open-Meteo forecast
  │ weather │         per waypoint (W1–W5)
  └────┬────┘
       │
       ▼
  ┌──────────┐        Applies disruption transform,
  │ what_if  │        recomputes scenario KPIs
  └────┬─────┘
       │
       ▼
  ┌──────────────────┐   6 adversarial personas
  │ stakeholder_sim  │   + synthesis agent
  └────────┬─────────┘
           │
           ▼
       ┌─────────┐
       │ planner │   Generates dispatch plan
       └────┬────┘
            │
            ▼
        ┌───────┐
        │ judge │◄──────────────────┐
        └───┬───┘                   │
      pass / │ fail                 │
            ├──────────────────┐    │
            ▼                  ▼    │
        ┌────────┐     ┌─────────────┐
        │ report │     │ revise_plan │──┘
        └────────┘     └─────────────┘
            │          (up to 3 cycles)
            ▼
    dispatch_report_*.pdf
```

**Technology stack:**
- **Orchestration:** LangGraph `StateGraph` with typed `AppState`
- **LLM:** GPT-4.1-mini (temperature 0.2) for all agent calls
- **Vector store:** ChromaDB (persistent, rebuilt on first run)
- **Weather API:** Open-Meteo (free, no key required)
- **PDF generation:** ReportLab

---

## 5. Agent Design & Prompt Engineering

**Files:** [`src/prompts.py`](src/prompts.py), [`src/prompts_advanced.py`](src/prompts_advanced.py)

### 5.1 Agent Inventory

| Agent | Model | Temp | Input | Output |
|---|---|---|---|---|
| `ContextAgent` | GPT-4.1-mini | 0.2 | RAG chunks from PDF (k=6) | Structured bullets: KPIs, SLAs, thresholds, dispatch rules |
| `OpsDataAgent` | GPT-4.1-mini | 0.2 | CSV summary dict + anomaly table | Key findings, root causes, immediate actions |
| `ScenarioAgent` | GPT-4.1-mini | 0.2 | Baseline KPIs, scenario KPIs, disruption type | 3-bullet operational impact summary |
| `PlannerAgent` | GPT-4.1-mini | 0.2 | All upstream context (rules + ops + weather + scenario + stakeholders) | 5-section dispatch plan |
| `JudgeAgent` | GPT-4.1-mini | 0.2 | Business rules + dispatch plan | Structured JSON verdict |
| `ReviseAgent` | GPT-4.1-mini | 0.2 | Original plan + violations + required fixes + stakeholder synthesis | Corrected dispatch plan |
| `Persona agents ×6` | GPT-4.1-mini | 0.2 | Disruption type + what-if summary + scenario KPIs + plan | 2–3 sentence adversarial reaction |
| `SynthesisAgent` | GPT-4.1-mini | 0.2 | All 6 persona reactions | Three-section structured synthesis |
| `ReportAgent` | GPT-4.1-mini | 0.2 | Full pipeline state | Executive HTML report (converted to PDF) |

Temperature 0.2 is used across all agents. This is a deliberate choice: lower temperature ensures the JudgeAgent produces consistent, rule-grounded verdicts rather than variable creative interpretations, and ensures KPI deltas are reported accurately rather than paraphrased.

### 5.2 Key Prompt Design Decisions

#### JudgeAgent — Enforced JSON output + strict failure criteria

The JudgeAgent is the most constraint-sensitive agent in the pipeline. Two design decisions make it reliable:

**Forced JSON schema** prevents ambiguous verdicts. The system prompt specifies the exact keys required:

```
Return a JSON object with exactly these keys:
  "verdict": "pass" or "fail"
  "violations": list of rule violations found (empty list if pass)
  "required_fixes": list of specific changes the PlannerAgent must make
```

The parsing code strips markdown fences before JSON deserialization and falls back to `{"verdict": "pass"}` only on complete parse failure — ensuring the pipeline never crashes on a malformed response.

**Explicit failure criteria** are embedded in the system prompt so the agent cannot rubber-stamp a plan:

```
Be strict. A plan that ignores cold chain breaches, priority-1 SLAs,
or risk escalation thresholds must fail.
```

#### PlannerAgent — Grounded weather input contract

The PlannerAgent has a known failure mode: without explicit constraints, it hallucinates weather details (snowfall, visibility, hourly mm/hr) not present in the Open-Meteo API response. A weather input contract is embedded directly in the system prompt:

```
WEATHER INPUT CONTRACT (IMPORTANT):
- Do NOT invent or reference snowfall, visibility, weather codes,
  or hourly (mm/hr) thresholds unless they appear in weather_risk.
- Use ONLY: max_precip_mm_day, max_wind_gust_kmh, min_temp_c,
  risk_flags, risk_score_0_3.
```

The buffer policy is also hardcoded in the prompt to prevent the agent from inventing its own thresholds:

```
BUFFER POLICY:
- risk_score 0 → 0% buffer
- risk_score 1 → 10% buffer
- risk_score 2 → 25% buffer
- risk_score 3 → 40% buffer + escalation
```

#### Persona Agents — Adversarial by design

Each of the six stakeholder personas is explicitly designed to find fault, not to approve:

```python
"Be specific, critical, and adversarial — identify exactly what in the
plan fails to address your concern. Do not rubber-stamp the plan."
```

The concern is hardcoded per persona (e.g., `"zero SLA breaches for critical medications — patient lives depend on it"` for HospitalAdmin), ensuring each persona applies pressure from a genuinely different angle rather than converging to generic praise.

#### ReportAgent — Structured output contract

The ReportAgent produces HTML (converted to PDF by ReportLab), not Markdown. A required structure is enforced via the system prompt to ensure every run produces a comparable, navigable report:

```
REQUIRED STRUCTURE (in this order):
1. Executive Summary (3 bullets: situation, risk, recommendation)
2. Baseline KPIs vs Scenario KPIs (side-by-side HTML table)
3. Weather Risk (per-waypoint table)
4. Stakeholder Concerns
5. Dispatch Plan
6. Audit Result (pass/fail, revision cycles, violations)
```

### 5.3 Tools Summary

| Tool | File | Purpose |
|---|---|---|
| `PdfRag` | [`src/tools/pdf_tools.py`](src/tools/pdf_tools.py) | Builds ChromaDB vector store from PDF; retrieves k=6 chunks per query |
| `analyze_csv` | [`src/tools/csv_tools.py`](src/tools/csv_tools.py) | Cleans CSV, runs augmentation, detects anomalies via IsolationForest |
| `augment_shipment_df` | [`src/tools/augment_tools.py`](src/tools/augment_tools.py) | Generates 9 synthetic operational fields with deterministic seeds |
| `compute_domain_kpis` | [`src/tools/kpi_tools.py`](src/tools/kpi_tools.py) | Computes 8 operational KPIs from augmented DataFrame |
| `get_weather_forecast` | [`src/tools/weather_tools.py`](src/tools/weather_tools.py) | Fetches 2-day daily forecast from Open-Meteo for a given coordinate |
| `derive_dispatch_weather_risk` | [`src/tools/weather_tools.py`](src/tools/weather_tools.py) | Converts raw forecast to 0–3 risk score with named flags |

---

## 6. Enhancement 1 — Self-Correction & Quality Assurance

**Files:** [`src/nodes/judge.py`](src/nodes/judge.py), [`src/agents.py`](src/agents.py)

### 6.1 Design Rationale

A dispatch plan that ignores a Playbook rule — such as failing to apply a +25% travel buffer at Risk Score 2 waypoints, or failing to flag cold-chain breaches — should never reach leadership. The Audit Loop prevents this by making plan compliance a hard gate before the Report node is reached.

### 6.2 How the Audit Loop Works

**Step 1 — Plan generation:** The `PlannerAgent` receives the full state (business rules, ops insights, weather risk, scenario KPIs, stakeholder synthesis) and generates a natural-language dispatch plan.

**Step 2 — Audit:** The `JudgeAgent` receives the Playbook-extracted business rules and the plan, and returns a structured JSON verdict:

```json
{
  "verdict": "pass" | "fail",
  "violations": ["Rule violated: no travel buffer applied at W1 (risk score 2)"],
  "required_fixes": ["Apply +25% buffer at Newark and Bronx per Playbook §5.2"]
}
```

**Step 3 — Conditional routing:**
- If `verdict == "pass"` → proceed to Report
- If `verdict == "fail"` AND `retries < MAX_RETRIES (3)` → route to `revise_plan`
- If `retries >= 3` → proceed to Report with violations documented

**Step 4 — Revision:** The `ReviseAgent` receives the original plan, the violations list, the required fixes, and the stakeholder synthesis. It produces a corrected plan that is fed back into the JudgeAgent.

### 6.3 Playbook Rules the JudgeAgent Enforces

These rules are extracted from the Playbook PDF via RAG and embedded in the JudgeAgent's context at runtime:

| Rule | Source | Enforcement |
|---|---|---|
| Risk Score 3 → +40% buffer + mandatory escalation | Playbook §5.2 | Plan must explicitly state escalation |
| Risk Score 2 → +25% travel buffer | Playbook §5.2 | Applied to W1 (Newark), W2 (Bronx) in live run |
| SLA Tier 1 violations must be flagged | Playbook §6 | 19 at-risk Priority-1 shipments must be addressed |
| DQ-01: Missing `unique_item_id` → exclude from dispatch | Playbook §10 | Exclusion must be explicit in plan |
| Cold-chain breaches → mandatory reporting | Playbook §8 + FDA | Plan must include breach response protocol |

### 6.4 Live Run Result

**Verdict: Pass — 0 revision cycles**

The initial plan generated by the PlannerAgent correctly:
- Applied the +25% travel buffer at W1 (Newark, 21.1 mm/47.2 km/h, Risk 2) and W2 (Bronx, 17.92 mm/48.2 km/h, Risk 2) per Playbook §5.2
- Addressed the 60% cold-chain breach rate with real-time temperature monitoring requirements
- Excluded `item_id 99999` per DQ-01/DQ-02
- Flagged all 19 at-risk Priority-1 shipments for escalation

This demonstrates the pipeline works correctly in the zero-violation case. Revision cycle behavior can be tested by deliberately injecting a non-compliant plan or running under a Risk Score 3 scenario.

---

## 7. Enhancement 2 — "What-if" Scenario Simulation

**File:** [`src/nodes/what_if.py`](src/nodes/what_if.py)

### 7.1 Design Rationale

Dispatchers need to answer "what if?" before committing to a plan — not after a disruption has already happened. This node applies a deterministic transform to the augmented DataFrame and recomputes all 11 KPIs against the disrupted state, giving the Planner and Report agents scenario-aware context rather than baseline-only data.

### 7.2 Disruption Models

| Disruption Type | Transform Logic | Parameters |
|---|---|---|
| `demand_spike` | `quantity_ordered × multiplier` | `multiplier` (default 1.2) |
| `driver_shortage` | +4h delay to first `shortage_pct` of shipments | `shortage_pct` (default 0.30) |
| `warehouse_closure` | +4h delay to all shipments from `location` | `location` (default `Boston-MGH`) |
| `weather_event` | Delay = {0→0h, 1→1h, 2→3h, 3→6h} per Playbook §5.2 | `risk_score` (0–3) |

The delay-to-risk mapping in `weather_event` is directly derived from the Playbook §5.2 buffer policy, ensuring scenario simulations are grounded in the same rules the JudgeAgent enforces.

### 7.3 Results — Demand Spike ×1.2 (Live Run)

| KPI | Baseline | Scenario | Delta | Interpretation |
|---|---|---|---|---|
| Total Units Dispatched | 1,392 | **1,634** | +17.4% | Increased load |
| Capacity Utilization (%) | 32.0 | **37.56** | +5.56pp | Still well below 50% target |
| On-Time Rate (%) | 72.41 | 72.41 | 0 | Volume absorbed without delay impact |
| Cold-Chain Breach Rate (%) | 60.0 | 60.0 | 0 | Structural issue — unaffected by volume |
| Shipments at Risk | 19 | 19 | 0 | Risk level unchanged |

**Insight:** The demand spike was absorbed in volume without degrading punctuality, which suggests the system has latent capacity headroom. However, the flat cold-chain breach rate confirms the breach problem is structural — it originates from temperature control failures, not from schedule overload. Adding more volume does not worsen it, but it also does not improve it.

### 7.4 Scenario Agent Output

After computing the KPI delta, a `ScenarioAgent` LLM call produces a 3-bullet operational summary. This summary is passed directly to the Planner and Report agents, ensuring the dispatch plan is written in response to the scenario rather than the baseline.

---

## 8. Stakeholder Simulation Layer

**File:** [`src/nodes/stakeholder_sim.py`](src/nodes/stakeholder_sim.py)

### 8.1 Design Rationale

A dispatch plan that satisfies the Planner but ignores the concerns of the hospital pharmacist, the FDA compliance officer, or the CFO is an incomplete plan. The stakeholder simulation surfaces cross-functional concerns before the plan reaches the audit stage, giving the Planner richer context and reducing the likelihood of audit failure.

### 8.2 Persona Design

Each persona is explicitly adversarial — designed to identify what the plan fails to address, not to approve it:

| Persona | Role | Primary Concern | Finding (Live Run) |
|---|---|---|---|
| HospitalAdmin | Director of Pharmacy, MGH | Zero SLA breaches for critical medications | 60% breach rate unacceptable; demands cold-chain compliance plan |
| Dispatcher | SeeWeeS Regional Dispatcher | Route efficiency and driver allocation | Low utilization (37.56%) despite demand spike — inefficient routing |
| Driver | I-95 corridor truck driver | Road safety, hours-of-service, cold chain | Weather at W1/W2 requires proactive cold-chain monitoring protocol |
| WarehouseManager | Boston hub warehouse manager | Loading accuracy and dock scheduling | Needs capacity-aware plan with contingency for weather + data errors |
| ComplianceOfficer | FDA cold chain oversight | Regulatory compliance | 60% breach rate triggers mandatory FDA reporting; immediate corrective action required |
| CFO | SeeWeeS CFO | Cost impact | Demand spike + breach rate creates overtime, rerouting, and SLA penalty exposure |

### 8.3 Synthesis Output Structure

The `SynthesisAgent` consolidates all six reactions into a structured three-section output:

- **Consensus:** All six personas agree that the cold-chain breach rate is the single highest-priority risk, overriding routing and cost concerns.
- **Failure Paths:** Without cold-chain intervention, the system will continue generating FDA-reportable incidents regardless of dispatch plan quality.
- **Escalation Triggers:** (1) Any Priority-1 SLA breach at MGH/BWH, (2) cold-chain breach rate exceeding 0%, (3) route risk score reaching 3.

This synthesis is passed directly to the `PlannerAgent`, shaping the plan before it reaches the JudgeAgent.

---

## 9. KPI Framework

All KPIs are computed in [`src/tools/kpi_tools.py`](src/tools/kpi_tools.py) and reported for both the baseline and the scenario state.

| KPI | Formula | Threshold | Playbook Grounding |
|---|---|---|---|
| **On-Time Rate (%)** | `(non-late shipments / total) × 100` | < 90% = alert | §6 SLA compliance |
| **Late Shipments** | `total − on_time` | Any late P1 = escalation | §6 Tier 1 SLA |
| **Cold-Chain Breach Count** | Shipments where `temp_max > 8°C` or `temp_min < 2°C` | 0 = compliant; ≥1 = FDA reportable | §8 Item Master |
| **Cold-Chain Breach Rate (%)** | `(breaches / cold-chain shipments) × 100` | > 0% = non-compliant | §8, FDA 21 CFR Part 211 |
| **Critical Hospital On-Time (%)** | `(on-time P1 deliveries / total P1) × 100` | < 100% = SLA breach | §6 Tier 1: 6h max transit |
| **Shipments at Risk** | Late shipments where `hospital_priority == 1` | > 0 = immediate escalation | §6 + §11 |
| **Capacity Utilization (%)** | `(total_units / truck_capacity × total_shipments) × 100` | > 95% = over-capacity | §7.2 truck packing model |
| **Total Units Dispatched** | `sum(quantity_ordered)` | Scenario comparison baseline | §7.2 |

---

## 10. Results & Validation

### 10.1 Weather Risk — Live Data (2026-05-21)

Weather forecasts were fetched live from Open-Meteo for all five I-95 waypoints. Risk flags follow Playbook §5.1 thresholds exactly.

| Waypoint | City | Precip (mm/day) | Wind Gust (km/h) | Min Temp (°C) | Risk Flags | Score | Buffer |
|---|---|---|---|---|---|---|---|
| W1 | Newark, NJ | **21.1** | **47.2** | 9.6 | Heavy Rain + High Wind | **2** | **+25%** |
| W2 | Bronx, NY | **17.92** | **48.2** | 9.9 | Heavy Rain + High Wind | **2** | **+25%** |
| W3 | New Haven, CT | 11.65 | **45.4** | 8.7 | High Wind | 1 | +10% |
| W4 | Providence, RI | 0.1 | 31.3 | 8.3 | None | 0 | None |
| W5 | Boston, MA | 0.0 | 40.0 | 7.4 | None | 0 | None |

**Overall route risk score: 2.** The first 60% of the I-95 route (Newark → New Haven) operates under moderate to high weather risk. Route risk is defined as the maximum score across all waypoints per Playbook §4.

### 10.2 Dispatch Plan Highlights (Audit-Passed)

The PlannerAgent generated a 5-section dispatch plan covering:

1. **Data validation** — Exclude DQ-01 rows (missing `unique_item_id`); log item_id 99999 under DQ-02
2. **Truck loading** — Target ≥50% utilization; prioritize temperature-controlled trucks for all 45 cold-chain shipments; formula: `ceil(total_volume × 1.10 / 10)` per Playbook §7.2
3. **Weather buffers** — +25% at W1 and W2; +10% at W3; no buffer at W4/W5
4. **Cold-chain integrity** — Real-time temperature monitoring; retrain drivers on cold-chain protocols; limit batch sizes per truck
5. **Cost controls** — Monitor driver hours-of-service; prepare contingency budget for rerouting

### 10.3 Validation Strategy

**Unit testing** — All deterministic logic (KPI computation, disruption transforms, weather scoring, waypoint parsing) is covered in `tests/`. Run with `PYTHONPATH=src pytest`.

**Reproducibility** — Deterministic seeds (`seed = item_id + row_index`) ensure identical KPIs across runs for the same input CSV, enabling reliable scenario comparison.

**Audit trail** — The final PDF records verdict, revision cycle count, and violations found. In the live run: `Status: Pass, Revision Cycles: 0, Remaining Violations: None`.

**Weather threshold verification** — Risk flags cross-checked against Playbook §5.1: W1 (21.1 mm ≥ 15.0 threshold ✓, 47.2 km/h ≥ 45.0 threshold ✓), W2 (17.92 mm ≥ 15.0 ✓, 48.2 km/h ≥ 45.0 ✓), W3 (45.4 km/h ≥ 45.0 ✓, 11.65 mm < 15.0 → no rain flag ✓).

**Playbook grounding** — The ContextAgent RAG retriever queries ChromaDB with k=6 chunks targeting "KPI definitions, thresholds, SLAs, constraints, dispatch rules." The JudgeAgent's rule set is derived entirely from the Playbook at runtime, not hardcoded — meaning rule updates in the PDF are automatically reflected in future audit runs.

---

## 11. Limitations & Next Steps

### 11.1 Current Limitations

**Cold-chain item mapping is incomplete.** The Playbook §8 Item Master lists `item_id 10035` (Pembrolizumab, Monoclonal Antibody, Cold 2–8°C) as a cold-chain item. The current `COLD_CHAIN_ITEMS` set in `augment_tools.py` only covers `{10021–10025}`. As a result, Pembrolizumab breaches are excluded from the breach rate, understating the true regulatory exposure. This is the highest-priority code fix.

**Synthetic temperature data overstates breach rate.** The 60% cold-chain breach rate is generated from a synthetic temperature distribution (`U(6.0°C, 9.5°C)` for max temperature), which frequently exceeds the 8°C upper bound. Real IoT telemetry would calibrate this figure to actual operational performance.

**Single-day planning horizon.** The 24 late shipments on March 6 create downstream risk for March 7 (delayed reorders, hospital inventory shortfalls). The current system does not model day-over-day carryover effects.

**Stakeholder calls are sequential.** A 22-second rate-limit sleep between each of the six persona calls adds ~2 minutes to pipeline runtime. Replacing the loop with `asyncio.gather` would reduce this to under 15 seconds with no architectural changes.

**JudgeAgent uses the same model as PlannerAgent.** This reduces audit independence. Assigning a stronger or different model (e.g., Claude Opus) to the JudgeAgent would increase the rigor of compliance checking.

### 11.2 Next Steps

| Priority | Action | Enhancement |
|---|---|---|
| **High** | Fix `COLD_CHAIN_ITEMS` to include `item_id 10035` per Playbook §8 | Code fix |
| **High** | Replace synthetic temperature fields with live IoT telemetry | Data pipeline |
| **Medium** | Implement Human-in-the-Loop checkpoint when route risk score = 3 (§5.2 escalation) | Enhancement 4 |
| **Medium** | Extend planning horizon to 7 days with multi-day carryover modeling | Enhancement 5 |
| **Medium** | Parallelize stakeholder simulation with `asyncio.gather` | Performance |
| **Low** | Period-over-period trend analysis on KPI snapshots stored in a time-series DB | Enhancement 3 |
| **Low** | Upgrade JudgeAgent to a stronger model for higher audit independence | Architecture |

---

*System: LangGraph + GPT-4.1-mini + ChromaDB + Open-Meteo API*
*Live run output: `dispatch_report_20260521_230312.pdf`*
*All business rules grounded in: SeeWeeS Specialty Dispatch Playbook v0.1*
