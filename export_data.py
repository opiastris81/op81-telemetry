import os
import pandas as pd
import numpy as np
from historical_engine import (
    load_past_session, get_telemetry_trace, get_track_circuit_coords
)

DATA_DIR = "precomputed_data"
os.makedirs(DATA_DIR, exist_ok=True)

RACES = [
    "Australia", "China", "Japan", "Miami", "Canada",
    "Monaco", "Barcelona", "Austria", "Silverstone", "Spa",
    "Hungary", "Zandvoort", "Monza", "Madrid", "Baku", "Malaysia"
]

DRIVERS = ["PIA", "NOR", "VER", "HAM", "LEC", "RUS", "ALO", "SAI", "ALB", "GAS"]

print("⚡ Starting export using existing historical_engine...")

for gp in RACES:
    print(f"\nProcessing {gp}...")
    try:
        # Load qualifying (or race if qualifying is unavailable)
        session = load_past_session(2026, gp, "Q")
        
        # 1. Circuit coordinates
        coords = get_track_circuit_coords(session)
        if not coords.empty:
            coords.to_parquet(f"{DATA_DIR}/{gp}_circuit.parquet")
            print(f"  ✓ Saved circuit coordinates ({len(coords)} points)")
        else:
            print("  ⚠️ Circuit coords were empty")

        # 2. Telemetry per driver
        saved_drivers = 0
        for dvr in DRIVERS:
            df_tel, lap_str, comp = get_telemetry_trace(session, dvr)
            if not df_tel.empty:
                df_tel.to_parquet(f"{DATA_DIR}/{gp}_{dvr}.parquet")
                saved_drivers += 1
        print(f"  ✓ Saved telemetry for {saved_drivers} drivers")

    except Exception as e:
        print(f"  ❌ Error processing {gp}: {e}")

print("\n✨ Export complete! Inspecting precomputed_data/:")
files = os.listdir(DATA_DIR)
print(f"Total files created: {len(files)}")
if files:
    for f in sorted(files)[:8]:
        print("  -", f)
