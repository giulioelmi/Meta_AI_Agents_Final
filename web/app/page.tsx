"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  CloudLightning,
  Map,
  PackagePlus,
  RefreshCcw,
  ShieldCheck,
  Truck,
  Warehouse,
  X
} from "lucide-react";
import { scenarios, type Scenario } from "../lib/scenarios";

function formatValue(value: number, suffix: string) {
  return `${value.toLocaleString()}${suffix}`;
}

function riskClass(kind: Scenario["kind"]) {
  if (kind === "weather") return "weather";
  if (kind === "demand") return "demand";
  return "resource";
}

function statusIcon(status: string) {
  if (status === "approved") return <ShieldCheck size={17} />;
  if (status === "rerun") return <RefreshCcw size={17} />;
  return <CheckCircle2 size={17} />;
}

function riskTagClass(risk: string) {
  if (risk === "Critical") return "demand";
  if (risk === "High") return "resource";
  if (risk === "Moderate") return "weather";
  return "ok";
}

function getMonitoringRecommendations(scenario: Scenario) {
  if (scenario.kind === "weather") {
    return [
      "Track route weather and risk-score changes before releasing the 48-hour dispatch plan.",
      "Notify hospital receiving teams that the risk-2 scenario makes all priority-1 shipments timing-sensitive."
    ];
  }

  if (scenario.kind === "resource") {
    return [
      "Monitor driver coverage before Day0 release because the shortage pushes at-risk shipments from 19 to 35.",
      "Recheck priority-1 hospital assignments before approving any lower-priority dispatch moves."
    ];
  }

  if (scenario.kind === "closure") {
    return [
      "Track Boston-MGH recovery status because the closure scenario pushes at-risk shipments from 19 to 46.",
      "Confirm alternate handling for priority-1 shipments before lower-risk volume is released."
    ];
  }

  return [
    "Watch capacity utilization as the demand multiplier raises dispatched units from 1,392 to 1,634.",
    "Confirm incremental demand does not hide the existing 60 percent cold-chain breach rate."
  ];
}

function getTriggerSummary(scenario: Scenario) {
  const rerunStep = scenario.agentTimeline.find((step) => step.status === "rerun");
  return rerunStep
    ? `${rerunStep.name} triggered fallback after JudgeAgent found a planning rule issue: ${rerunStep.detail}`
    : "JudgeAgent cleared the first planner draft with no rerun required, so the plan can move straight into the report.";
}

function getSummaryImpact(scenario: Scenario) {
  if (scenario.kind === "weather") {
    return "The business risk is timing collapse: the teammate scenario applies a three-hour weather delay that makes every shipment late in the deterministic result.";
  }

  if (scenario.kind === "resource") {
    return "The business risk is driver coverage: fewer available drivers sharply reduces priority-1 hospital on-time performance.";
  }

  if (scenario.kind === "closure") {
    return "The business risk is continuity at Boston-MGH: a local closure delay creates severe priority-1 exposure even though total shipment volume is unchanged.";
  }

  return "The business risk is capacity pressure: the demand spike raises dispatched units and utilization while the lateness and cold-chain breach profile remains unchanged.";
}

function getKpiImpactNote(scenario: Scenario) {
  const onTimeDrop = scenario.baseline.onTimeRate - scenario.disrupted.onTimeRate;
  const extraRiskShipments = scenario.disrupted.atRiskShipments - scenario.baseline.atRiskShipments;
  const unitShift = scenario.disrupted.totalUnitsDispatched - scenario.baseline.totalUnitsDispatched;
  if (unitShift > 0 && onTimeDrop === 0) {
    return `The simulated disruption keeps on-time performance at ${scenario.disrupted.onTimeRate}% but adds ${unitShift.toLocaleString()} units and raises capacity utilization to ${scenario.disrupted.capacityUtilization}%.`;
  }
  return `The simulated disruption lowers on-time performance by ${onTimeDrop.toFixed(2)} points and adds ${extraRiskShipments} at-risk shipments before the approved contingency plan is applied.`;
}

const corridorDetails = {
  boston: {
    code: "C1_I95_NJ_BOS",
    label: "Boston",
    fullName: "I-95 to Boston hospitals"
  },
  philly: {
    code: "C2_NJ_PHL",
    label: "Philadelphia",
    fullName: "NJ to Philadelphia hospitals"
  }
};

export default function Home() {
  const [selectedId, setSelectedId] = useState(scenarios[0].id);
  const [isBriefOpen, setIsBriefOpen] = useState(false);
  const scenario = useMemo(
    () => scenarios.find((item) => item.id === selectedId) ?? scenarios[0],
    [selectedId]
  );
  const Icon = scenario.icon;
  const corridorMode =
    scenario.kind === "weather" ? "weather" : scenario.kind === "demand" ? "demand" : "resource";
  const corridorPressure = // Retained for future detailed corridor views.
    scenario.kind === "weather"
      ? {
          boston: "Risk-2 weather delay",
          philly: "Weather timing exposure"
        }
      : scenario.kind === "resource"
        ? {
            boston: "Driver coverage constrained",
            philly: "Driver coverage monitored"
          }
        : scenario.kind === "closure"
          ? {
              boston: "Boston-MGH closure exposure",
              philly: "Spillover monitored"
            }
        : {
            boston: "Demand volume pressure",
            philly: "Capacity utilization monitored"
          };
  const RouteIcon =
    scenario.kind === "weather"
      ? CloudLightning
      : scenario.kind === "resource"
        ? Truck
        : scenario.kind === "closure"
          ? Warehouse
          : PackagePlus;
  const bostonActive = scenario.kind === "weather" || scenario.kind === "resource" || scenario.kind === "demand" || scenario.kind === "closure";
  const phillyActive = scenario.kind === "weather" || scenario.kind === "resource" || scenario.kind === "demand";
  const monitoringRecommendations = getMonitoringRecommendations(scenario);
  const judgeResult = scenario.agentTimeline.some((item) => item.status === "rerun") ? "Rerun approved" : "Clear";

  useEffect(() => {
    if (!isBriefOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsBriefOpen(false);
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isBriefOpen]);

  return (
    <main className="app-shell">
      <div className="dashboard report-dashboard">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark" aria-hidden="true">
              <Activity size={25} strokeWidth={2.6} />
            </div>
            <div>
              <p className="eyebrow">SeeWeeS Specialty</p>
              <h1>Dispatch Report</h1>
              <p className="topline">
                Compare baseline dispatch, teammate what-if results, and the JudgeAgent-approved fallback plan for a 48-hour specialty distribution window.
              </p>
            </div>
          </div>
          <div className="top-actions">
            <span className={`tag ${riskClass(scenario.kind)}`}>{scenario.disruptionType}</span>
            <button
              type="button"
              className="details-button"
              aria-label="Open full scenario brief"
              onClick={() => setIsBriefOpen(true)}
            >
              Full brief <ArrowUpRight size={15} />
            </button>
          </div>
        </header>

        <nav className="scenario-tabs" aria-label="Disruption scenarios">
          {scenarios.map((item) => {
            const ScenarioIcon = item.icon;
            return (
              <button
                type="button"
                key={item.id}
                className={`scenario-tab ${item.id === selectedId ? "active" : ""}`}
                onClick={() => setSelectedId(item.id)}
              >
                <ScenarioIcon size={18} />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>

        <article className="report-flow">
          <section className="report-section" aria-labelledby="summary-title">
            <div className="report-section-head">
              <span className="section-number">1</span>
              <div>
                <h2 id="summary-title">Dispatch Plan Summary</h2>
                <p>{scenario.summary}</p>
              </div>
            </div>
            <p className="section-note">{getSummaryImpact(scenario)}</p>
            <div className="summary-grid">
              <div className="summary-card">
                <span><Icon size={15} /> Disruption</span>
                <strong>{scenario.kind}</strong>
                <p>{scenario.disruptionType}</p>
              </div>
              <div className="summary-card">
                <span><CheckCircle2 size={15} /> Baseline</span>
                <strong>{scenario.baseline.onTimeRate}%</strong>
                <p>{scenario.baseline.atRiskShipments} at-risk shipments</p>
              </div>
              <div className="summary-card">
                <span><AlertTriangle size={15} /> Disrupted</span>
                <strong>{scenario.disrupted.onTimeRate}%</strong>
                <p>{scenario.disrupted.atRiskShipments} at-risk shipments</p>
              </div>
              <div className="summary-card">
                <span><ShieldCheck size={15} /> JudgeAgent</span>
                <strong>{judgeResult}</strong>
                <p>Final plan approved for report release</p>
              </div>
            </div>
          </section>

          <section className="report-section split-section" aria-labelledby="monitoring-title">
            <div>
              <div className="report-section-head">
                <span className="section-number">2</span>
                <div>
                  <h2 id="monitoring-title">Monitoring Recommendations</h2>
                  <p>
                    These signals explain what operations should keep watching while the scenario is active. They connect the visual corridor state to the practical dispatch decisions leadership would expect in the generated report.
                  </p>
                </div>
              </div>
              <ul className="compact-list">
                {monitoringRecommendations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div
              className={`corridor-map ${corridorMode}`}
              aria-label={`48-hour network from Newark DC to ${corridorDetails.boston.fullName} and ${corridorDetails.philly.fullName}. ${corridorPressure.boston}; ${corridorPressure.philly}.`}
            >
              <div className="corridor-title">
                <span>48h network</span>
              </div>
              <div className="mini-network">
                <div className="route-node origin" title="Newark NJ distribution center">
                  <span className="node-icon"><Map size={19} /></span>
                  <strong>Newark DC</strong>
                </div>

                <div className={`route-path path-boston ${bostonActive ? "active" : ""}`} aria-hidden="true" />
                <div className={`route-path path-philly ${phillyActive ? "active" : ""}`} aria-hidden="true" />

                <div
                  className={`route-node destination boston ${bostonActive ? "active" : ""}`}
                  title={`${corridorDetails.boston.code}: ${corridorPressure.boston}`}
                >
                  <span className="scenario-badge"><RouteIcon size={18} /></span>
                  <strong>{corridorDetails.boston.label}</strong>
                </div>

                <div
                  className={`route-node destination philly ${phillyActive ? "active" : ""}`}
                  title={`${corridorDetails.philly.code}: ${corridorPressure.philly}`}
                >
                  <span className="scenario-badge"><RouteIcon size={18} /></span>
                  <strong>{corridorDetails.philly.label}</strong>
                </div>
              </div>
            </div>
          </section>

          <section className="report-section" aria-labelledby="triggers-title">
            <div className="report-section-head">
              <span className="section-number">3</span>
              <div>
                <h2 id="triggers-title">Contingency Triggers & Actions</h2>
                <p>{getTriggerSummary(scenario)}</p>
              </div>
            </div>
            <p className="section-note">
              Why this matters: the fallback loop turns the scenario from a static what-if into an auditable recommendation that can be rerun before stakeholders see the final report.
            </p>
            <div className="action-grid">
              {scenario.contingencyPlan.slice(0, 3).map((action, index) => (
                <div className="action-card" key={action}>
                  <span>{index + 1}</span>
                  <p>{action}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="report-section" aria-labelledby="impact-title">
            <div className="report-section-head">
              <span className="section-number">4</span>
              <div>
                <h2 id="impact-title">KPI Impact Summary</h2>
                <p>
                  Baseline and disrupted performance are shown side by side so the business cost of the selected scenario is visible before opening the full technical brief.
                </p>
              </div>
            </div>
            <p className="section-note">{getKpiImpactNote(scenario)}</p>
            <div className="impact-grid">
              <div className="impact-row">
                <span>On-time rate</span>
                <strong>{scenario.baseline.onTimeRate}% → {scenario.disrupted.onTimeRate}%</strong>
              </div>
              <div className="impact-row">
                <span>At-risk shipments</span>
                <strong>{scenario.baseline.atRiskShipments} → {scenario.disrupted.atRiskShipments}</strong>
              </div>
              <div className="impact-row">
                <span>Late shipments</span>
                <strong>{formatValue(scenario.baseline.lateShipments, "")} → {formatValue(scenario.disrupted.lateShipments, "")}</strong>
              </div>
              <div className="impact-row">
                <span>Capacity utilization</span>
                <strong>{scenario.baseline.capacityUtilization}% → {scenario.disrupted.capacityUtilization}%</strong>
              </div>
            </div>
          </section>
        </article>
      </div>
      {isBriefOpen ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => setIsBriefOpen(false)}
        >
          <section
            className="brief-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="brief-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <p className="eyebrow">{scenario.disruptionType}</p>
                <h2 id="brief-modal-title">{scenario.name}</h2>
              </div>
              <button
                type="button"
                className="modal-close"
                aria-label="Close detailed scenario brief"
                onClick={() => setIsBriefOpen(false)}
              >
                <X size={19} />
              </button>
            </div>

            <p className="modal-intro">{scenario.summary}</p>

            <div className="modal-metrics" aria-label="Baseline and disrupted metrics">
              <div>
                <span>Baseline</span>
                <strong>{scenario.baseline.onTimeRate}%</strong>
                <p>{scenario.baseline.atRiskShipments} at-risk shipments</p>
              </div>
              <div>
                <span>Disrupted</span>
                <strong>{scenario.disrupted.onTimeRate}%</strong>
                <p>{scenario.disrupted.atRiskShipments} at-risk shipments</p>
              </div>
              <div>
                <span>Cold-chain breach</span>
                <strong>{scenario.disrupted.coldChainBreachRate}%</strong>
                <p>unchanged in teammate what-if handler</p>
              </div>
            </div>

            <div className="modal-sections">
              <section>
                <h3>Recommended 48-hour Allocation</h3>
                <div className="table-wrap">
                  <table className="allocation-table">
                    <thead>
                      <tr>
                        <th>Day</th>
                        <th>Corridor</th>
                        <th>Drivers</th>
                        <th>Standard trucks</th>
                        <th>Temp trucks</th>
                        <th>Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scenario.allocation.map((row) => (
                        <tr key={`${row.day}-${row.corridor}`}>
                          <td>{row.day}</td>
                          <td>{row.corridor}</td>
                          <td>{row.drivers}</td>
                          <td>{row.standardTrucks}</td>
                          <td>{row.tempTrucks}</td>
                          <td><span className={`tag ${riskTagClass(row.risk)}`}>{row.risk}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section>
                <h3>Agent Flow</h3>
                <div className="modal-flow">
                  {scenario.agentTimeline.map((step) => (
                    <div className="modal-flow-step" key={step.name}>
                      <span className={`flow-dot ${step.status}`} />
                      <div>
                        <strong>{step.name}</strong>
                        <p>{step.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <h3>JudgeAgent Findings</h3>
                <ul className="modal-list">
                  {scenario.judgeFindings.map((finding) => (
                    <li key={finding}>{finding}</li>
                  ))}
                </ul>
              </section>

              <section>
                <h3>Final Contingency Plan</h3>
                <ul className="modal-list">
                  {scenario.contingencyPlan.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </section>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
