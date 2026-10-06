import os
import pandas as pd
import numpy as np
from historical_engine import (
    load_past_session, get_telemetry_trace, get_track_circuit_coords, get_performance_rankings
)

DATA_DIR = "precomputed_data"
os.makedirs(DATA_DIR, exist_ok=True)

RACES = [
    "Australia", "China", "Japan", "Miami", "Canada",
    "Monaco", "Barcelona", "Austria", "Silverstone", "Spa",
    "Hungary", "Zandvoort", "Monza", "Madrid", "Baku", "Malaysia"
]

DRIVERS = ["PIA", "NOR", "VER", "HAM", "LEC", "RUS", "ALO", "SAI", "ALB", "GAS"]

print("⚡ Pre-computing all tabs (Telemetry, GPS, Rankings, Pace)...")

for gp in RACES:
    print(f"\nProcessing {gp}...")
    try:
        session = load_past_session(2026, gp, "Q")
        
        # 1. Circuit coordinates (Tab 3)
        coords = get_track_circuit_coords(session)
        if not coords.empty:
            coords.to_parquet(f"{DATA_DIR}/{gp}_circuit.parquet")

        # 2. Driver Telemetry (Tab 1)
        for dvr in DRIVERS:
            df_tel, lap_str, comp = get_telemetry_trace(session, dvr)
            if not df_tel.empty:
                df_tel.to_parquet(f"{DATA_DIR}/{gp}_{dvr}.parquet")

        # 3. Sector Rankings (Tab 2)
        rank_tables, _ = get_performance_rankings(session)
        if rank_tables:
            for key in ["s1", "s2", "s3", "fastest", "theo"]:
                if key in rank_tables and not rank_tables[key].empty:
                    rank_tables[key].to_parquet(f"{DATA_DIR}/{gp}_rank_{key}.parquet")
            print("  ✓ Saved sector ranking tables")

        # 4. Oscar Pace Matrix Laps (Tab 4)
        p_laps = session.laps.pick_drivers("PIA").copy()
        if not p_laps.empty:
            # Keep only the essential columns to keep the file tiny (~10 KB)
            cols = ["LapNumber", "Compound", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time", "TyreLife", "PitInTime", "PitOutTime"]
            existing_cols = [c for c in cols if c in p_laps.columns]
            p_mini = p_laps[existing_cols].copy()
            
            # Convert timedeltas to float seconds for seamless Parquet serialization
            for t_col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
                if t_col in p_mini.columns:
                    p_mini[f"{t_col}_s"] = p_mini[t_col].dt.total_seconds()
            
            p_mini["PitIn"] = p_mini["PitInTime"].notnull() if "PitInTime" in p_mini.columns else False
            p_mini["PitOut"] = p_mini["PitOutTime"].notnull() if "PitOutTime" in p_mini.columns else False
            
            p_mini.to_parquet(f"{DATA_DIR}/{gp}_PIA_laps.parquet")
            print("  ✓ Saved Oscar pace matrix laps")

    except Exception as e:
        print(f"  ❌ Skipping {gp}: {e}")

print("\n✨ All tab data exported successfully!")
