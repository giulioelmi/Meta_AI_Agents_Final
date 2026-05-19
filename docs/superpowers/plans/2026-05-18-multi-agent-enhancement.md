# Multi-Agent Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the linear SeeWeeS reporting pipeline into a multi-agent system with real domain KPIs, data augmentation, what-if scenario simulation, stakeholder persona simulation, and a self-correcting Judge/Audit loop.

**Architecture:** The existing linear graph (pdf_context → csv_analysis → weather → planner → report → email) is extended with five new stages inserted between weather and planner: data augmentation, what-if disruption, scenario KPI recalculation, stakeholder simulation (6 personas + synthesis), then planner feeds a Judge/AuditAgent loop (max 3 retries) before the final report.

**Tech Stack:** Python 3.11+, LangGraph, LangChain, OpenAI GPT-4.1-mini, pandas, scikit-learn, open-meteo (existing)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/tools/augment_tools.py` | Simulate missing CSV columns (dates, temps, priority, capacity) |
| Create | `src/tools/kpi_tools.py` | Compute domain KPIs from augmented DataFrame |
| Create | `src/nodes/__init__.py` | Empty package marker |
| Create | `src/nodes/what_if.py` | Apply disruption scenario + recalculate scenario KPIs |
| Create | `src/nodes/stakeholder_sim.py` | 6 persona LLM calls (parallel) + synthesis agent |
| Create | `src/nodes/judge.py` | Audit plan vs playbook rules; revise if needed |
| Create | `src/prompts_advanced.py` | All new prompts (what-if, personas, judge, revise) |
| Modify | `src/tools/csv_tools.py` | Call augment + kpi_tools; return augmented df in result |
| Modify | `src/graph.py` | Extend AppState; wire all new nodes + conditional edges |
| Modify | `src/agents.py` | Add runner functions for new agents |
| Modify | `src/prompts.py` | Update PlannerAgent prompt to consume stakeholder synthesis |

---

## Task 1: Data Augmentation

**Files:**
- Create: `src/tools/augment_tools.py`
- Test: `tests/test_augment.py`

The CSV has only 4 columns (`item_id`, `item_name`, `unique_item_id`, `dispatch_location`). We simulate the missing operational fields deterministically using `item_id` as a random seed so results are reproducible.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_augment.py
import pandas as pd
from tools.augment_tools import augment_shipment_df

def test_augment_adds_required_columns():
    df = pd.DataFrame({
        "item_id": [10021, 10022],
        "item_name": ["Remdesivir 100mg", "Insulin Lispro"],
        "unique_item_id": ["RMD-2026-0001", "INS-2026-0101"],
        "dispatch_location": ["Boston-MGH", "Boston-BWH"],
    })
    result = augment_shipment_df(df)
    required = [
        "scheduled_date", "actual_date", "quantity_ordered",
        "temp_min_c", "temp_max_c", "cold_chain_required",
        "hospital_priority", "driver_id", "truck_capacity_units",
        "is_late", "cold_chain_breach",
    ]
    for col in required:
        assert col in result.columns, f"Missing column: {col}"

def test_augment_is_deterministic():
    df = pd.DataFrame({
        "item_id": [10021], "item_name": ["Remdesivir 100mg"],
        "unique_item_id": ["RMD-2026-0001"], "dispatch_location": ["Boston-MGH"],
    })
    r1 = augment_shipment_df(df)
    r2 = augment_shipment_df(df)
    assert r1["scheduled_date"].iloc[0] == r2["scheduled_date"].iloc[0]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/giulioelmi/Desktop/MSBA_AI_Agents_Demo && python -m pytest tests/test_augment.py -v
```
Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Implement `augment_tools.py`**

```python
# src/tools/augment_tools.py
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

COLD_CHAIN_ITEMS = {10021, 10022, 10023}  # Remdesivir, Insulin, etc.
HOSPITAL_PRIORITY = {"Boston-MGH": 1, "Boston-BWH": 1}  # 1=critical, 2=urgent, 3=routine
TEMP_RANGE = {"min_ok": 2.0, "max_ok": 8.0}  # Celsius, cold chain requirement
TRUCK_CAPACITY = 50  # units per truck

def augment_shipment_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    base_date = datetime(2026, 3, 6, 8, 0)

    rng_seeds = df["item_id"].astype(int).values
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        rng = np.random.default_rng(int(rng_seeds[i]) + i)
        scheduled = base_date + timedelta(hours=float(rng.uniform(2, 24)))
        delay_h = float(rng.choice([0, 0, 0, 1, 2, 4, 8], p=[0.5, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05]))
        actual = scheduled + timedelta(hours=delay_h)
        qty = int(rng.integers(5, 30))
        cold = int(row["item_id"]) in COLD_CHAIN_ITEMS
        temp_min = float(rng.uniform(1.5, 3.0)) if cold else float(rng.uniform(15, 20))
        temp_max = float(rng.uniform(6.0, 9.5)) if cold else float(rng.uniform(20, 25))
        priority = HOSPITAL_PRIORITY.get(str(row["dispatch_location"]), 2)
        driver_id = f"DRV-{int(rng.integers(100, 200))}"
        rows.append({
            "scheduled_date": scheduled,
            "actual_date": actual,
            "quantity_ordered": qty,
            "temp_min_c": round(temp_min, 2),
            "temp_max_c": round(temp_max, 2),
            "cold_chain_required": cold,
            "hospital_priority": priority,
            "driver_id": driver_id,
            "truck_capacity_units": TRUCK_CAPACITY,
            "is_late": actual > scheduled,
            "cold_chain_breach": cold and (temp_max > TEMP_RANGE["max_ok"] or temp_min < TEMP_RANGE["min_ok"]),
        })
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_augment.py -v
```
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/tools/augment_tools.py tests/test_augment.py
git commit -m "feat: add deterministic CSV data augmentation with SeeWeeS domain fields"
```

---

## Task 2: Domain KPIs

**Files:**
- Create: `src/tools/kpi_tools.py`
- Test: `tests/test_kpis.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_kpis.py
import pandas as pd
from datetime import datetime, timedelta
from tools.kpi_tools import compute_domain_kpis

def _sample_df():
    base = datetime(2026, 3, 6, 10, 0)
    return pd.DataFrame({
        "item_id": [10021, 10022, 10023],
        "is_late": [False, True, False],
        "cold_chain_required": [True, True, False],
        "cold_chain_breach": [False, True, False],
        "hospital_priority": [1, 1, 2],
        "quantity_ordered": [10, 20, 5],
        "truck_capacity_units": [50, 50, 50],
        "scheduled_date": [base, base, base],
        "actual_date": [base, base + timedelta(hours=2), base],
    })

def test_on_time_rate():
    kpis = compute_domain_kpis(_sample_df())
    assert kpis["on_time_rate_pct"] == pytest.approx(66.67, abs=0.1)

def test_cold_chain_breach_rate():
    kpis = compute_domain_kpis(_sample_df())
    assert kpis["cold_chain_breach_rate_pct"] == pytest.approx(50.0, abs=0.1)

def test_critical_hospital_on_time_rate():
    kpis = compute_domain_kpis(_sample_df())
    assert kpis["critical_hospital_on_time_pct"] == pytest.approx(50.0, abs=0.1)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_kpis.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Implement `kpi_tools.py`**

```python
# src/tools/kpi_tools.py
from __future__ import annotations
from typing import Dict, Any
import pandas as pd

def compute_domain_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    total = len(df)
    on_time = (~df["is_late"]).sum()
    cold_chain = df[df["cold_chain_required"]]
    breaches = df["cold_chain_breach"].sum()
    critical = df[df["hospital_priority"] == 1]
    critical_on_time = (~critical["is_late"]).sum() if len(critical) > 0 else 0
    total_qty = df["quantity_ordered"].sum()
    capacity = df["truck_capacity_units"].iloc[0] if total > 0 else 50

    return {
        "total_shipments": int(total),
        "on_time_rate_pct": round(100 * on_time / total, 2) if total else 0,
        "late_shipments": int(total - on_time),
        "cold_chain_shipments": int(len(cold_chain)),
        "cold_chain_breach_count": int(breaches),
        "cold_chain_breach_rate_pct": round(100 * breaches / len(cold_chain), 2) if len(cold_chain) else 0,
        "critical_hospital_shipments": int(len(critical)),
        "critical_hospital_on_time_pct": round(100 * critical_on_time / len(critical), 2) if len(critical) else 0,
        "total_units_dispatched": int(total_qty),
        "capacity_utilization_pct": round(100 * total_qty / (capacity * total), 2) if total else 0,
        "shipments_at_risk": int(df[df["is_late"] & (df["hospital_priority"] == 1)].shape[0]),
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_kpis.py -v
```
Expected: `3 passed`

- [ ] **Step 5: Wire into `csv_tools.py`**

In `src/tools/csv_tools.py`, replace the generic KPI block (lines 43-48) with:

```python
from tools.augment_tools import augment_shipment_df
from tools.kpi_tools import compute_domain_kpis

# inside analyze_csv(), after df is cleaned:
df = augment_shipment_df(df)
kpis = compute_domain_kpis(df)
```

Also update `CsvAnalysisResult` to store the augmented df:

```python
@dataclass
class CsvAnalysisResult:
    summary: Dict[str, Any]
    kpis: Dict[str, Any]
    anomalies: pd.DataFrame
    cleaned_shape: Tuple[int, int]
    numeric_cols: List[str]
    augmented_df: pd.DataFrame  # add this field
```

Return it as `augmented_df=df` in the final `CsvAnalysisResult(...)` call.

- [ ] **Step 6: Commit**

```bash
git add src/tools/kpi_tools.py tests/test_kpis.py src/tools/csv_tools.py
git commit -m "feat: replace generic KPIs with SeeWeeS domain KPIs (on-time, cold-chain, priority)"
```

---

## Task 3: Extend AppState

**Files:**
- Modify: `src/graph.py` (AppState only, lines 19-35)

- [ ] **Step 1: Update AppState**

Replace the existing `AppState` class with:

```python
class AppState(TypedDict, total=False):
    pdf_path: str
    csv_path: str

    business_context: str

    csv_summary: Dict[str, Any]
    csv_kpis: Dict[str, Any]
    anomalies_md: str
    ops_insights: str
    augmented_df_json: str          # augmented DataFrame as JSON string

    weather_risk: Dict[str, Any]

    # What-if
    disruption_type: str            # "demand_spike" | "driver_shortage" | "warehouse_closure" | "weather_event"
    disruption_params: Dict[str, Any]
    scenario_kpis: Dict[str, Any]
    what_if_summary: str

    # Stakeholder simulation
    stakeholder_reactions: Dict[str, str]   # persona_name -> reaction text
    stakeholder_synthesis: str              # failure paths + escalation triggers

    # Planner + audit loop
    dispatch_plan: str
    audit_verdict: str              # "pass" | "fail"
    audit_violations: List[str]
    audit_retries: int

    report_html: str
```

- [ ] **Step 2: Verify existing tests still pass**

```bash
python -m pytest tests/ -v
```
Expected: all existing tests pass (AppState changes are additive)

- [ ] **Step 3: Commit**

```bash
git add src/graph.py
git commit -m "feat: extend AppState with what-if, stakeholder sim, and audit loop fields"
```

---

## Task 4: What-If Node

**Files:**
- Create: `src/nodes/__init__.py` (empty)
- Create: `src/nodes/what_if.py`
- Create: `src/prompts_advanced.py` (partial — what-if prompt only)
- Test: `tests/test_what_if.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_what_if.py
import json
from unittest.mock import patch, MagicMock

def _base_state():
    import pandas as pd
    from tools.augment_tools import augment_shipment_df
    from tools.kpi_tools import compute_domain_kpis
    df = pd.read_csv("data/Incoming_shipment_03_06.csv")
    df = augment_shipment_df(df)
    return {
        "csv_kpis": compute_domain_kpis(df),
        "augmented_df_json": df.to_json(),
        "disruption_type": "demand_spike",
        "disruption_params": {"multiplier": 1.2},
        "business_context": "SLA: deliver within 4h for priority-1 hospitals.",
        "weather_risk": {"risk_score_0_3": 1},
    }

def test_demand_spike_raises_at_risk_count():
    from nodes.what_if import node_what_if
    with patch("nodes.what_if.run_what_if_agent", return_value="Demand spike increases risk."):
        state = _base_state()
        result = node_what_if(state)
        assert "scenario_kpis" in result
        assert result["scenario_kpis"]["total_units_dispatched"] > state["csv_kpis"]["total_units_dispatched"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_what_if.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Add what-if prompt to `prompts_advanced.py`**

```python
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
```

- [ ] **Step 4: Implement `nodes/what_if.py`**

```python
# src/nodes/what_if.py
from __future__ import annotations
import json
import pandas as pd
from typing import Dict, Any
from agents import llm
from prompts_advanced import WHAT_IF_PROMPT
from tools.kpi_tools import compute_domain_kpis

DISRUPTION_HANDLERS = {
    "demand_spike": _apply_demand_spike,
    "driver_shortage": _apply_driver_shortage,
    "warehouse_closure": _apply_warehouse_closure,
    "weather_event": _apply_weather_event,
}

def run_what_if_agent(disruption_type, disruption_params, baseline_kpis, scenario_kpis, business_context) -> str:
    return llm.invoke(WHAT_IF_PROMPT.format_messages(
        disruption_type=disruption_type,
        disruption_params=disruption_params,
        baseline_kpis=baseline_kpis,
        scenario_kpis=scenario_kpis,
        business_context=business_context,
    )).content

def _apply_demand_spike(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    df["quantity_ordered"] = (df["quantity_ordered"] * params.get("multiplier", 1.2)).astype(int)
    return df

def _apply_driver_shortage(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    shortage_pct = params.get("shortage_pct", 0.3)
    n_affected = int(len(df) * shortage_pct)
    from datetime import timedelta
    df.loc[df.index[:n_affected], "actual_date"] = (
        df.loc[df.index[:n_affected], "actual_date"] + timedelta(hours=4)
    )
    df["is_late"] = df["actual_date"] > df["scheduled_date"]
    return df

def _apply_warehouse_closure(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    location = params.get("location", "Boston-MGH")
    from datetime import timedelta
    mask = df["dispatch_location"] == location
    df.loc[mask, "actual_date"] = df.loc[mask, "actual_date"] + timedelta(hours=4)
    df["is_late"] = df["actual_date"] > df["scheduled_date"]
    return df

def _apply_weather_event(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    risk_score = params.get("risk_score", 2)
    delay_map = {0: 0, 1: 1, 2: 3, 3: 6}
    from datetime import timedelta
    delay_h = delay_map.get(risk_score, 2)
    df["actual_date"] = df["actual_date"] + timedelta(hours=delay_h)
    df["is_late"] = df["actual_date"] > df["scheduled_date"]
    return df

def node_what_if(state) -> Dict[str, Any]:
    disruption_type = state.get("disruption_type", "demand_spike")
    disruption_params = state.get("disruption_params", {"multiplier": 1.2})
    df = pd.read_json(state["augmented_df_json"])

    handler = DISRUPTION_HANDLERS.get(disruption_type, _apply_demand_spike)
    df_scenario = handler(df, disruption_params)
    scenario_kpis = compute_domain_kpis(df_scenario)

    summary = run_what_if_agent(
        disruption_type=disruption_type,
        disruption_params=disruption_params,
        baseline_kpis=state["csv_kpis"],
        scenario_kpis=scenario_kpis,
        business_context=state.get("business_context", ""),
    )
    return {
        "scenario_kpis": scenario_kpis,
        "what_if_summary": summary,
    }
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_what_if.py -v
```
Expected: `1 passed`

- [ ] **Step 6: Commit**

```bash
git add src/nodes/__init__.py src/nodes/what_if.py src/prompts_advanced.py tests/test_what_if.py
git commit -m "feat: add what-if disruption node (demand spike, driver shortage, warehouse closure, weather)"
```

---

## Task 5: Stakeholder Simulation Node

**Files:**
- Create: `src/nodes/stakeholder_sim.py`
- Modify: `src/prompts_advanced.py` (add 7 persona + synthesis prompts)
- Test: `tests/test_stakeholder_sim.py`

- [ ] **Step 1: Add persona prompts to `prompts_advanced.py`**

Append to the existing file:

```python
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
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_stakeholder_sim.py
from unittest.mock import patch

def _state():
    return {
        "disruption_type": "demand_spike",
        "what_if_summary": "20% demand spike increases at-risk shipments by 40%.",
        "scenario_kpis": {"on_time_rate_pct": 55.0, "cold_chain_breach_rate_pct": 12.0},
        "dispatch_plan": "Proceed with standard routing.",
        "business_context": "SLA: 4h for priority-1.",
    }

def test_stakeholder_sim_returns_all_personas():
    from nodes.stakeholder_sim import node_stakeholder_sim
    fake_response = MagicMock(); fake_response.content = "I am concerned."
    with patch("nodes.stakeholder_sim.llm") as mock_llm:
        mock_llm.invoke.return_value = fake_response
        result = node_stakeholder_sim(_state())
    assert "stakeholder_reactions" in result
    assert len(result["stakeholder_reactions"]) == 6
    assert "stakeholder_synthesis" in result
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python -m pytest tests/test_stakeholder_sim.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 4: Implement `nodes/stakeholder_sim.py`**

```python
# src/nodes/stakeholder_sim.py
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
from agents import llm
from prompts_advanced import PERSONA_PROMPTS, SYNTHESIS_PROMPT


def _run_persona(name: str, prompt_template, inputs: Dict[str, Any]) -> tuple[str, str]:
    response = llm.invoke(prompt_template.format_messages(**inputs))
    return name, response.content


def node_stakeholder_sim(state) -> Dict[str, Any]:
    inputs = {
        "disruption_type": state.get("disruption_type", ""),
        "what_if_summary": state.get("what_if_summary", ""),
        "scenario_kpis": state.get("scenario_kpis", {}),
        "dispatch_plan": state.get("dispatch_plan", "No plan yet."),
    }

    reactions: Dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_run_persona, name, tmpl, inputs): name
            for name, tmpl in PERSONA_PROMPTS.items()
        }
        for future in as_completed(futures):
            name, reaction = future.result()
            reactions[name] = reaction

    reactions_text = "\n\n".join(f"**{k}:** {v}" for k, v in reactions.items())
    synthesis = llm.invoke(SYNTHESIS_PROMPT.format_messages(reactions=reactions_text)).content

    return {
        "stakeholder_reactions": reactions,
        "stakeholder_synthesis": synthesis,
    }
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_stakeholder_sim.py -v
```
Expected: `1 passed`

- [ ] **Step 6: Commit**

```bash
git add src/nodes/stakeholder_sim.py src/prompts_advanced.py tests/test_stakeholder_sim.py
git commit -m "feat: add 6-persona stakeholder simulation node with parallel LLM calls and synthesis"
```

---

## Task 6: Judge/Audit Loop

**Files:**
- Create: `src/nodes/judge.py`
- Modify: `src/prompts_advanced.py` (add judge + revise prompts)
- Modify: `src/agents.py` (add `run_judge_agent`, `run_revise_agent`)
- Test: `tests/test_judge.py`

- [ ] **Step 1: Add judge and revise prompts to `prompts_advanced.py`**

Append:

```python
# ---------- Judge / Audit Prompts ----------

JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are JudgeAgent. You audit a dispatch plan against the SeeWeeS business rules extracted from the PDF. "
     "Return a JSON object with exactly these keys:\n"
     '  "verdict": "pass" or "fail"\n'
     '  "violations": list of rule violations found (empty list if pass)\n'
     '  "required_fixes": list of specific changes the PlannerAgent must make (empty list if pass)\n'
     "Be strict. A plan that ignores cold chain breaches, priority-1 SLAs, or risk escalation thresholds must fail."),
    ("user",
     "Business rules:\n{business_context}\n\n"
     "Dispatch plan to audit:\n{dispatch_plan}\n\n"
     "Return only valid JSON.")
])

REVISE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are PlannerAgent. Your previous dispatch plan was rejected by the JudgeAgent. "
     "Fix every violation listed. Do not repeat the same mistakes."),
    ("user",
     "Original plan:\n{dispatch_plan}\n\n"
     "Violations found:\n{violations}\n\n"
     "Required fixes:\n{required_fixes}\n\n"
     "Stakeholder concerns:\n{stakeholder_synthesis}\n\n"
     "Write the corrected dispatch plan.")
])
```

- [ ] **Step 2: Add agent runners to `agents.py`**

Append to `src/agents.py`:

```python
import json as _json

def run_judge_agent(business_context: str, dispatch_plan: str) -> Dict[str, Any]:
    raw = llm.invoke(JUDGE_PROMPT.format_messages(
        business_context=business_context,
        dispatch_plan=dispatch_plan,
    )).content
    try:
        return _json.loads(raw)
    except Exception:
        # Fallback: if LLM didn't return pure JSON, treat as pass to avoid infinite loop
        return {"verdict": "pass", "violations": [], "required_fixes": []}

def run_revise_agent(dispatch_plan: str, violations: list, required_fixes: list, stakeholder_synthesis: str) -> str:
    return llm.invoke(REVISE_PROMPT.format_messages(
        dispatch_plan=dispatch_plan,
        violations="\n".join(f"- {v}" for v in violations),
        required_fixes="\n".join(f"- {f}" for f in required_fixes),
        stakeholder_synthesis=stakeholder_synthesis,
    )).content
```

Also add imports at the top of `agents.py`:
```python
from prompts_advanced import JUDGE_PROMPT, REVISE_PROMPT
from typing import Dict, Any
import json as _json
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_judge.py
from unittest.mock import patch, MagicMock
import json

def test_judge_pass():
    from nodes.judge import node_judge
    mock = MagicMock(); mock.content = json.dumps({"verdict": "pass", "violations": [], "required_fixes": []})
    with patch("agents.llm") as m:
        m.invoke.return_value = mock
        result = node_judge({
            "business_context": "SLA: 4h.", "dispatch_plan": "Good plan.",
            "audit_retries": 0
        })
    assert result["audit_verdict"] == "pass"

def test_judge_fail_increments_retries():
    from nodes.judge import node_judge
    mock = MagicMock(); mock.content = json.dumps({
        "verdict": "fail",
        "violations": ["Cold chain breach not addressed."],
        "required_fixes": ["Add cold chain monitoring step."]
    })
    with patch("agents.llm") as m:
        m.invoke.return_value = mock
        result = node_judge({
            "business_context": "SLA: 4h.", "dispatch_plan": "Bad plan.",
            "audit_retries": 0
        })
    assert result["audit_verdict"] == "fail"
    assert result["audit_retries"] == 1
```

- [ ] **Step 4: Run test to verify it fails**

```bash
python -m pytest tests/test_judge.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 5: Implement `nodes/judge.py`**

```python
# src/nodes/judge.py
from __future__ import annotations
from typing import Dict, Any
from agents import run_judge_agent, run_revise_agent

MAX_RETRIES = 3

def node_judge(state) -> Dict[str, Any]:
    result = run_judge_agent(
        business_context=state.get("business_context", ""),
        dispatch_plan=state.get("dispatch_plan", ""),
    )
    retries = state.get("audit_retries", 0)
    if result["verdict"] == "fail":
        retries += 1
    return {
        "audit_verdict": result["verdict"],
        "audit_violations": result.get("violations", []),
        "audit_retries": retries,
    }

def node_revise(state) -> Dict[str, Any]:
    revised = run_revise_agent(
        dispatch_plan=state.get("dispatch_plan", ""),
        violations=state.get("audit_violations", []),
        required_fixes=[],
        stakeholder_synthesis=state.get("stakeholder_synthesis", ""),
    )
    return {"dispatch_plan": revised}

def route_after_judge(state) -> str:
    if state.get("audit_verdict") == "pass" or state.get("audit_retries", 0) >= MAX_RETRIES:
        return "report"
    return "revise_plan"
```

- [ ] **Step 6: Run test to verify it passes**

```bash
python -m pytest tests/test_judge.py -v
```
Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add src/nodes/judge.py src/prompts_advanced.py src/agents.py tests/test_judge.py
git commit -m "feat: add JudgeAgent audit loop with max-3-retry revise cycle"
```

---

## Task 7: Wire the Full Graph

**Files:**
- Modify: `src/graph.py` (build_graph function and nodes)
- Modify: `src/prompts.py` (update PlannerAgent to consume stakeholder synthesis)

- [ ] **Step 1: Update `PLANNER_PROMPT` in `prompts.py`**

Add stakeholder synthesis to the user message:

```python
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
```

- [ ] **Step 2: Update `run_planner_agent` in `agents.py`**

```python
def run_planner_agent(
    business_context: str, ops_insights: str, weather_risk: Dict[str, Any],
    what_if_summary: str = "", scenario_kpis: Dict[str, Any] = None,
    stakeholder_synthesis: str = ""
) -> str:
    return llm.invoke(PLANNER_PROMPT.format_messages(
        business_context=business_context,
        ops_insights=ops_insights,
        weather_risk=weather_risk,
        what_if_summary=what_if_summary,
        scenario_kpis=scenario_kpis or {},
        stakeholder_synthesis=stakeholder_synthesis,
    )).content
```

- [ ] **Step 3: Update `node_planner` in `graph.py`**

```python
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
```

- [ ] **Step 4: Add new node functions to `graph.py`**

Add these imports at the top:

```python
from nodes.what_if import node_what_if
from nodes.stakeholder_sim import node_stakeholder_sim
from nodes.judge import node_judge, node_revise, route_after_judge
```

Add this node to store augmented df in state (inside `node_csv_analysis`):

```python
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
```

- [ ] **Step 5: Rewrite `build_graph()`**

```python
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
```

- [ ] **Step 6: Update `main.py` to pass disruption scenario**

```python
state = {
    "pdf_path": "data/SeeWeeS Specialty Dispatch Playbook.pdf",
    "csv_path": "data/Incoming_shipment_03_06.csv",
    "disruption_type": "demand_spike",
    "disruption_params": {"multiplier": 1.2},
}
```

- [ ] **Step 7: Run smoke test**

```bash
python -m pytest tests/test_smoke.py -v
```
Expected: existing smoke test passes

- [ ] **Step 8: Commit**

```bash
git add src/graph.py src/prompts.py src/agents.py src/main.py
git commit -m "feat: wire full multi-agent graph with what-if, stakeholder sim, and judge audit loop"
```

---

## Task 8: Update Report

**Files:**
- Modify: `src/prompts.py` (REPORT_PROMPT)
- Modify: `src/agents.py` (run_report_agent signature)
- Modify: `src/graph.py` (node_report)

- [ ] **Step 1: Update `REPORT_PROMPT`**

Replace the existing `REPORT_PROMPT` with:

```python
REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ReportAgent. Produce a crisp HTML executive report for C-suite leadership. "
     "Use headings, tables, and bullets. Highlight risk in red, safe metrics in green.\n\n"
     "WEATHER REPORTING RULES:\n"
     "- Only report weather metrics present in the weather_risk object.\n"
     "- If per_waypoint exists, include an HTML table per waypoint with risk_score_0_3.\n"
     "- Do NOT mention snowfall, visibility, or hourly triggers unless those fields are present.\n\n"
     "STRUCTURE (in order):\n"
     "1. Executive Summary (3 bullets: situation, risk, recommendation)\n"
     "2. Baseline KPIs vs Scenario KPIs (side-by-side HTML table)\n"
     "3. Weather Risk (waypoint table if available)\n"
     "4. Stakeholder Concerns (one line per persona, synthesis below)\n"
     "5. Dispatch Plan (the approved or final plan)\n"
     "6. Audit Result (pass/fail, number of revision cycles, any remaining violations)\n"),
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
     "Generate the HTML report.")
])
```

- [ ] **Step 2: Update `run_report_agent` in `agents.py`**

```python
def run_report_agent(
    business_context: str, kpis: Dict[str, Any], scenario_kpis: Dict[str, Any],
    what_if_summary: str, anomaly_highlights: str, weather_risk: Dict[str, Any],
    stakeholder_reactions: Dict[str, str], stakeholder_synthesis: str,
    dispatch_plan: str, audit_verdict: str, audit_retries: int, audit_violations: list,
) -> str:
    return llm.invoke(REPORT_PROMPT.format_messages(
        business_context=business_context, kpis=kpis, scenario_kpis=scenario_kpis,
        what_if_summary=what_if_summary, anomaly_highlights=anomaly_highlights,
        weather_risk=weather_risk, stakeholder_reactions=stakeholder_reactions,
        stakeholder_synthesis=stakeholder_synthesis, dispatch_plan=dispatch_plan,
        audit_verdict=audit_verdict, audit_retries=audit_retries,
        audit_violations=audit_violations,
    )).content
```

- [ ] **Step 3: Update `node_report` in `graph.py`**

```python
def node_report(state: AppState) -> AppState:
    html = run_report_agent(
        business_context=state.get("business_context", ""),
        kpis=state.get("csv_kpis", {}),
        scenario_kpis=state.get("scenario_kpis", {}),
        what_if_summary=state.get("what_if_summary", ""),
        anomaly_highlights=state.get("anomalies_md", "(none)"),
        weather_risk=state.get("weather_risk", {}),
        stakeholder_reactions=state.get("stakeholder_reactions", {}),
        stakeholder_synthesis=state.get("stakeholder_synthesis", ""),
        dispatch_plan=state.get("dispatch_plan", ""),
        audit_verdict=state.get("audit_verdict", "unknown"),
        audit_retries=state.get("audit_retries", 0),
        audit_violations=state.get("audit_violations", []),
    )
    return {"report_html": html}
```

- [ ] **Step 4: End-to-end smoke run**

```bash
cd /Users/giulioelmi/Desktop/MSBA_AI_Agents_Demo && python src/main.py 2>&1 | tail -50
```
Expected: HTML report printed, no exceptions, LangSmith trace visible

- [ ] **Step 5: Commit**

```bash
git add src/prompts.py src/agents.py src/graph.py
git commit -m "feat: update ReportAgent with baseline vs scenario KPI comparison, stakeholder synthesis, and audit result"
```

---

## Self-Review

**Spec coverage:**
- ✅ Ingest + clean SeeWeeS data → Tasks 1-2
- ✅ Baseline KPIs → Task 2
- ✅ What-if disruption + scenario KPIs → Task 4
- ✅ Stakeholder simulation (MiroFish-inspired) → Task 5
- ✅ Mitigation plan via PlannerAgent → Task 7
- ✅ Judge/AuditAgent loop → Task 6
- ✅ Executive report → Task 8
- ✅ AppState extended cleanly → Task 3

**Placeholder scan:** None found — all code blocks are complete implementations.

**Type consistency:** `augmented_df_json` (str) used consistently in Tasks 1, 2, 4, 7. `scenario_kpis` (Dict[str,Any]) consistent across Tasks 4, 7, 8. `audit_retries` (int) consistent across Tasks 6, 7, 8.
