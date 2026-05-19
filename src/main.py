from __future__ import annotations
import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

from tools.report_output import write_report_pdf

STEP_NAMES = [
    "pdf_context",
    "csv_analysis",
    "weather",
    "what_if",
    "stakeholder_sim",
    "planner",
    "judge",
    "report",
]

STEP_LABELS = {
    "pdf_context":     "PDF Context",
    "csv_analysis":    "CSV Analysis",
    "weather":         "Weather Risk",
    "what_if":         "What-If Simulation",
    "stakeholder_sim": "Stakeholder Sim",
    "planner":         "Planner",
    "judge":           "Judge / Audit",
    "report":          "Executive Report",
}

DISRUPTION_DEFAULTS: dict = {
    "demand_spike":      {"multiplier": 1.2},
    "driver_shortage":   {"shortage_pct": 0.30},
    "warehouse_closure": {"location": "Boston-MGH"},
    "weather_event":     {"risk_score": 2},
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SeeWeeS multi-agent ops pipeline")
    p.add_argument(
        "--disruption",
        default="demand_spike",
        choices=list(DISRUPTION_DEFAULTS),
        help="Type of disruption to simulate (default: demand_spike)",
    )
    p.add_argument("--multiplier",   type=float, default=None, help="Demand multiplier (demand_spike)")
    p.add_argument("--shortage-pct", type=int,   default=None, help="Drivers unavailable 10-80 (driver_shortage)")
    p.add_argument("--location",                 default=None, help="Closed warehouse (warehouse_closure)")
    p.add_argument("--risk-score",   type=int,   default=None, help="Weather risk 0-3 (weather_event)")
    return p.parse_args()


def build_params(args: argparse.Namespace) -> dict:
    params = dict(DISRUPTION_DEFAULTS[args.disruption])
    if args.disruption == "demand_spike"      and args.multiplier   is not None:
        params["multiplier"]   = args.multiplier
    if args.disruption == "driver_shortage"   and args.shortage_pct is not None:
        params["shortage_pct"] = args.shortage_pct / 100
    if args.disruption == "warehouse_closure" and args.location      is not None:
        params["location"]     = args.location
    if args.disruption == "weather_event"     and args.risk_score    is not None:
        params["risk_score"]   = args.risk_score
    return params


def fmt_disruption(dtype: str, params: dict) -> str:
    if dtype == "demand_spike":
        return f"Demand Spike x{params.get('multiplier', 1.2):.1f}"
    if dtype == "driver_shortage":
        return f"Driver Shortage  {int(params.get('shortage_pct', 0.3) * 100)}% unavailable"
    if dtype == "warehouse_closure":
        return f"Warehouse Closure  {params.get('location', '')}"
    if dtype == "weather_event":
        return f"Weather Event  risk {params.get('risk_score', 2)}/3"
    return dtype


def print_summary(final: dict, disruption_type: str, total_elapsed: float) -> None:
    baseline = final.get("csv_kpis", {})
    scenario = final.get("scenario_kpis", {})
    verdict  = final.get("audit_verdict", "unknown")
    retries  = final.get("audit_retries", 0)

    print("\n" + "-" * 50)
    print("Results")
    print("-" * 50)

    if baseline and scenario:
        b_on  = baseline.get("on_time_rate_pct", 0)
        s_on  = scenario.get("on_time_rate_pct", 0)
        b_br  = baseline.get("cold_chain_breach_rate_pct", 0)
        s_br  = scenario.get("cold_chain_breach_rate_pct", 0)
        b_rk  = baseline.get("shipments_at_risk", 0)
        s_rk  = scenario.get("shipments_at_risk", 0)

        def arrow(delta: float, lower_better: bool = False) -> str:
            up   = delta > 0
            good = up if not lower_better else not up
            sym  = "up" if up else "down"
            sign = "+" if delta > 0 else ""
            return f"{sym} {sign}{delta:.1f}%  {'OK' if good else '!!'}"

        print(f"  On-time rate:     {b_on:.1f}% -> {s_on:.1f}%   {arrow(s_on - b_on)}")
        print(f"  Cold chain breach:{b_br:.1f}% -> {s_br:.1f}%   {arrow(s_br - b_br, lower_better=True)}")
        print(f"  At-risk shipments:{b_rk} -> {s_rk}")

    audit_str = "PASSED" if verdict == "pass" else f"MAX RETRIES ({retries})"
    print(f"\n  Audit:   {audit_str} after {retries} revision(s)")
    print(f"  Runtime: {total_elapsed:.1f}s")

    report_text = final.get("report_text", "")
    if report_text:
        out_path = write_report_pdf(report_text=report_text, output_dir=os.getcwd())
        print(f"  Report:  {os.path.normpath(out_path)}")

    print()


def main() -> None:
    args   = parse_args()
    params = build_params(args)
    if not os.getenv("OPENAI_API_KEY"):
        print("\nError: Missing OpenAI credentials.")
        print("Set OPENAI_API_KEY in your shell or in .env before running.")
        print("Example:")
        print("  cp .env.example .env")
        print("  # then add OPENAI_API_KEY=your_key_here")
        raise SystemExit(1)

    from graph import build_graph

    print()
    print("SeeWeeS Ops Intelligence")
    print("=" * 50)
    print(f"  {fmt_disruption(args.disruption, params)}")
    print()

    app = build_graph()

    init_state = {
        "pdf_path": os.path.join(os.path.dirname(__file__), "..", "data",
                                 "SeeWeeS Specialty Dispatch Playbook.pdf"),
        "csv_path": os.path.join(os.path.dirname(__file__), "..", "data",
                                 "Incoming_shipment_03_06.csv"),
        "disruption_type":   args.disruption,
        "disruption_params": params,
    }

    total   = len(STEP_NAMES)
    step_n  = {name: i + 1 for i, name in enumerate(STEP_NAMES)}
    t_start = time.time()
    t_step  = time.time()
    final: dict = {}

    # Print first step header before streaming starts
    first_label = STEP_LABELS[STEP_NAMES[0]]
    print(f"  [1/{total}] {first_label:<24}", end="", flush=True)

    try:
        for event in app.stream(init_state, stream_mode="updates"):
            for node_name, state_update in event.items():
                final.update(state_update)

                if node_name not in step_n:
                    continue

                elapsed = time.time() - t_step
                t_step  = time.time()
                n       = step_n[node_name]

                # Extra annotation for judge
                extra = ""
                if node_name == "judge":
                    v = state_update.get("audit_verdict", "")
                    r = state_update.get("audit_retries", 0)
                    if v == "pass":
                        extra = f"  passed"
                    else:
                        extra = f"  retrying ({r}/{3})"

                print(f"done  {elapsed:5.1f}s{extra}")

                # Print next step header (if not the last step)
                if n < total:
                    next_name  = STEP_NAMES[n]
                    next_label = STEP_LABELS[next_name]
                    # judge can loop back; re-print its header on retry
                    if node_name == "judge" and state_update.get("audit_verdict") != "pass":
                        print(f"  [{n}/{total}] {'Revise + Re-audit':<24}", end="", flush=True)
                    else:
                        print(f"  [{n + 1}/{total}] {next_label:<24}", end="", flush=True)

    except Exception as exc:
        print(f"\n\nError: {exc}")
        raise

    print_summary(final, args.disruption, time.time() - t_start)


if __name__ == "__main__":
    main()
