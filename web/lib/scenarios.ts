import {
  AlertTriangle,
  CloudLightning,
  type LucideIcon,
  PackagePlus,
  Truck,
  Warehouse
} from "lucide-react";

export type ScenarioKind = "weather" | "resource" | "demand" | "closure";

export type MetricSet = {
  totalShipments: number;
  onTimeRate: number;
  lateShipments: number;
  atRiskShipments: number;
  coldChainBreachRate: number;
  criticalHospitalOnTimeRate: number;
  totalUnitsDispatched: number;
  capacityUtilization: number;
};

export type AllocationRow = {
  day: "Day0" | "Day1";
  corridor: string;
  drivers: number;
  standardTrucks: number;
  tempTrucks: number;
  risk: "Low" | "Moderate" | "High" | "Critical";
};

export type AgentStep = {
  name: string;
  status: "complete" | "rerun" | "approved";
  detail: string;
};

export type Scenario = {
  id: string;
  name: string;
  kind: ScenarioKind;
  icon: LucideIcon;
  disruptionType: string;
  summary: string;
  baseline: MetricSet;
  disrupted: MetricSet;
  allocation: AllocationRow[];
  agentTimeline: AgentStep[];
  judgeFindings: string[];
  contingencyPlan: string[];
};

const baselineMetrics: MetricSet = {
  totalShipments: 87,
  onTimeRate: 72.41,
  lateShipments: 24,
  atRiskShipments: 19,
  coldChainBreachRate: 60,
  criticalHospitalOnTimeRate: 70.77,
  totalUnitsDispatched: 1392,
  capacityUtilization: 32
};

export const scenarios: Scenario[] = [
  {
    id: "demand-spike",
    name: "Demand Spike",
    kind: "demand",
    icon: PackagePlus,
    disruptionType: "Demand Spike x1.2",
    summary:
      "The teammate pipeline increases shipment quantity by 20 percent. On-time performance stays flat in the deterministic run, but total units and capacity utilization rise, creating a planning pressure point before the final dispatch recommendation.",
    baseline: baselineMetrics,
    disrupted: {
      ...baselineMetrics,
      totalUnitsDispatched: 1634,
      capacityUtilization: 37.56
    },
    allocation: [
      { day: "Day0", corridor: "C1_I95_NJ_BOS", drivers: 4, standardTrucks: 2, tempTrucks: 2, risk: "High" },
      { day: "Day0", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 0, risk: "Moderate" },
      { day: "Day1", corridor: "C1_I95_NJ_BOS", drivers: 4, standardTrucks: 2, tempTrucks: 1, risk: "High" },
      { day: "Day1", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 1, risk: "Moderate" }
    ],
    agentTimeline: [
      { name: "CSV Analysis", status: "complete", detail: "Computed baseline KPIs from 87 shipment rows." },
      { name: "What-If Simulation", status: "complete", detail: "Applied demand_spike with multiplier 1.2 to quantity_ordered." },
      { name: "Stakeholder Sim", status: "complete", detail: "Modeled priority-1 hospital and operations concerns." },
      { name: "PlannerAgent", status: "complete", detail: "Built a recovery plan around capacity pressure and priority shipments." },
      { name: "JudgeAgent", status: "approved", detail: "Audited the plan before executive report generation." }
    ],
    judgeFindings: [
      "Demand spike changes unit volume and capacity utilization, not lateness in the deterministic handler.",
      "Priority-1 hospital shipments remain the tie-breaker when capacity becomes constrained.",
      "The report should call out that cold-chain breach rate remains 60 percent in this scenario."
    ],
    contingencyPlan: [
      "Protect priority-1 hospital shipments before assigning incremental demand to lower-risk volume.",
      "Use the capacity utilization increase as the trigger for early carrier confirmation.",
      "Escalate any new cold-chain volume that cannot be assigned compliant equipment.",
      "Keep the JudgeAgent audit as the final gate before releasing the executive report."
    ]
  },
  {
    id: "driver-shortage",
    name: "Driver Shortage",
    kind: "resource",
    icon: Truck,
    disruptionType: "Driver Shortage: 30% unavailable",
    summary:
      "The teammate pipeline delays the first 30 percent of shipment rows by four hours. This reduces on-time performance and materially increases at-risk priority shipments, making driver coverage the main operational constraint.",
    baseline: baselineMetrics,
    disrupted: {
      ...baselineMetrics,
      onTimeRate: 52.87,
      lateShipments: 41,
      atRiskShipments: 35,
      criticalHospitalOnTimeRate: 46.15
    },
    allocation: [
      { day: "Day0", corridor: "C1_I95_NJ_BOS", drivers: 3, standardTrucks: 2, tempTrucks: 2, risk: "Critical" },
      { day: "Day0", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 0, risk: "Moderate" },
      { day: "Day1", corridor: "C1_I95_NJ_BOS", drivers: 3, standardTrucks: 2, tempTrucks: 1, risk: "High" },
      { day: "Day1", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 1, risk: "Moderate" }
    ],
    agentTimeline: [
      { name: "CSV Analysis", status: "complete", detail: "Loaded baseline dispatch and cold-chain KPI profile." },
      { name: "What-If Simulation", status: "complete", detail: "Applied driver_shortage with 30 percent unavailable drivers." },
      { name: "Stakeholder Sim", status: "complete", detail: "Surfaced hospital, dispatcher, driver, compliance, and CFO concerns." },
      { name: "PlannerAgent", status: "rerun", detail: "Initial plan required audit attention around priority-1 lateness exposure." },
      { name: "JudgeAgent", status: "approved", detail: "Approved the corrected plan after rule validation." }
    ],
    judgeFindings: [
      "At-risk shipments rise from 19 to 35 under the driver shortage scenario.",
      "Critical-hospital on-time performance falls from 70.77 percent to 46.15 percent.",
      "Cold-chain breach rate remains unchanged, so the report should not attribute compliance improvement to this scenario."
    ],
    contingencyPlan: [
      "Reassign available drivers to priority-1 Boston hospital loads first.",
      "Defer lower-priority specialty shipments that can tolerate later delivery windows.",
      "Escalate driver coverage gaps before the Day0 release cutoff.",
      "Require JudgeAgent confirmation that any revised route respects priority-1 SLA rules."
    ]
  },
  {
    id: "warehouse-closure",
    name: "Warehouse Closure",
    kind: "closure",
    icon: Warehouse,
    disruptionType: "Warehouse Closure: Boston-MGH",
    summary:
      "The teammate pipeline adds a four-hour delay to shipments dispatched from Boston-MGH. This creates the largest non-weather deterioration in the local result set, especially for priority-1 hospital service.",
    baseline: baselineMetrics,
    disrupted: {
      ...baselineMetrics,
      onTimeRate: 41.38,
      lateShipments: 51,
      atRiskShipments: 46,
      criticalHospitalOnTimeRate: 29.23
    },
    allocation: [
      { day: "Day0", corridor: "C1_I95_NJ_BOS", drivers: 4, standardTrucks: 2, tempTrucks: 2, risk: "Critical" },
      { day: "Day0", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 0, risk: "Moderate" },
      { day: "Day1", corridor: "C1_I95_NJ_BOS", drivers: 4, standardTrucks: 2, tempTrucks: 1, risk: "High" },
      { day: "Day1", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 1, risk: "Low" }
    ],
    agentTimeline: [
      { name: "CSV Analysis", status: "complete", detail: "Identified Boston-MGH as a priority-1 dispatch location." },
      { name: "What-If Simulation", status: "complete", detail: "Applied warehouse_closure to Boston-MGH shipments." },
      { name: "Stakeholder Sim", status: "complete", detail: "Prioritized hospital receiving and warehouse recovery concerns." },
      { name: "PlannerAgent", status: "rerun", detail: "Fallback planning focused on the priority-1 service collapse." },
      { name: "JudgeAgent", status: "approved", detail: "Approved plan after routing and escalation checks." }
    ],
    judgeFindings: [
      "At-risk shipments rise from 19 to 46 when Boston-MGH shipments are delayed.",
      "Critical-hospital on-time performance falls to 29.23 percent.",
      "The report should emphasize warehouse continuity and hospital communication rather than generic volume growth."
    ],
    contingencyPlan: [
      "Escalate Boston-MGH closure impact to operations leadership and hospital receiving teams.",
      "Prioritize alternate dispatch handling for priority-1 hospital shipments.",
      "Hold lower-risk shipments until the warehouse recovery window is confirmed.",
      "Use JudgeAgent validation to confirm the revised plan addresses priority-1 SLA exposure."
    ]
  },
  {
    id: "weather-event",
    name: "Weather Event",
    kind: "weather",
    icon: CloudLightning,
    disruptionType: "Weather Event: risk 2/3",
    summary:
      "The teammate pipeline applies a three-hour delay across the scenario when weather risk is set to 2. In the deterministic results, this pushes every shipment late and makes all priority-1 shipments at risk.",
    baseline: baselineMetrics,
    disrupted: {
      ...baselineMetrics,
      onTimeRate: 0,
      lateShipments: 87,
      atRiskShipments: 65,
      criticalHospitalOnTimeRate: 0
    },
    allocation: [
      { day: "Day0", corridor: "C1_I95_NJ_BOS", drivers: 4, standardTrucks: 2, tempTrucks: 2, risk: "Critical" },
      { day: "Day0", corridor: "C2_NJ_PHL", drivers: 2, standardTrucks: 2, tempTrucks: 0, risk: "High" },
      { day: "Day1", corridor: "C1_I95_NJ_BOS", drivers: 3, standardTrucks: 1, tempTrucks: 1, risk: "Critical" },
      { day: "Day1", corridor: "C2_NJ_PHL", drivers: 3, standardTrucks: 3, tempTrucks: 1, risk: "High" }
    ],
    agentTimeline: [
      { name: "Weather Risk", status: "complete", detail: "Evaluated route weather exposure before scenario simulation." },
      { name: "What-If Simulation", status: "complete", detail: "Applied weather_event with risk score 2 and a three-hour delay." },
      { name: "Stakeholder Sim", status: "complete", detail: "Raised hospital, driver safety, compliance, and cost concerns." },
      { name: "PlannerAgent", status: "rerun", detail: "Initial plan required stronger escalation for full late-shipment exposure." },
      { name: "JudgeAgent", status: "approved", detail: "Approved the corrected plan after weather-risk validation." }
    ],
    judgeFindings: [
      "On-time rate falls from 72.41 percent to 0 percent under the risk-2 weather delay.",
      "All 65 priority-1 hospital shipments become at-risk in the scenario output.",
      "Cold-chain breach rate remains 60 percent, so weather impact should be framed around timing and risk escalation."
    ],
    contingencyPlan: [
      "Escalate the weather event before dispatch release and confirm hospital receiving windows.",
      "Prioritize priority-1 shipments for earliest safe departure once weather risk clears.",
      "Communicate full late-shipment exposure in the executive report rather than masking residual risk.",
      "Use JudgeAgent to confirm the final plan includes weather-risk escalation language."
    ]
  }
];

export const scenarioIcons = {
  weather: CloudLightning,
  resource: Truck,
  demand: AlertTriangle,
  closure: Warehouse
};
