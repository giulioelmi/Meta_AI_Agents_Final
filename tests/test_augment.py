import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
    assert r1["quantity_ordered"].iloc[0] == r2["quantity_ordered"].iloc[0]

def test_augment_cold_chain_items_flagged():
    df = pd.DataFrame({
        "item_id": [10021, 10099],  # 10021 is cold chain, 10099 is not
        "item_name": ["Remdesivir 100mg", "Bandages"],
        "unique_item_id": ["RMD-2026-0001", "BND-2026-0001"],
        "dispatch_location": ["Boston-MGH", "Boston-MGH"],
    })
    result = augment_shipment_df(df)
    assert result.loc[result["item_id"] == 10021, "cold_chain_required"].iloc[0] == True
    assert result.loc[result["item_id"] == 10099, "cold_chain_required"].iloc[0] == False

def test_augment_priority_1_for_known_hospitals():
    df = pd.DataFrame({
        "item_id": [10021], "item_name": ["Remdesivir 100mg"],
        "unique_item_id": ["RMD-2026-0001"], "dispatch_location": ["Boston-MGH"],
    })
    result = augment_shipment_df(df)
    assert result["hospital_priority"].iloc[0] == 1
