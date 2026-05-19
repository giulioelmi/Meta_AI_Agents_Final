from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Set, Dict

COLD_CHAIN_ITEMS: Set[int] = {10021, 10022, 10023, 10024, 10025}
HOSPITAL_PRIORITY: Dict[str, int] = {
    "Boston-MGH": 1,
    "Boston-BWH": 1,
}
TEMP_RANGE = {"min_ok": 2.0, "max_ok": 8.0}
TRUCK_CAPACITY = 50

def augment_shipment_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    base_date = datetime(2026, 3, 6, 8, 0)
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        seed = int(row["item_id"]) + i
        rng = np.random.default_rng(seed)
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
