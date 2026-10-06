import os
import fastf1
import pandas as pd
import numpy as np

CACHE_DIR = os.path.expanduser("~/f1-telemetry-tool/f1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

CURRENT_SESSION = None
CURRENT_SESSION_KEY = None

def load_past_session(year: int, grand_prix: str, session_type: str = "Q"):
    global CURRENT_SESSION, CURRENT_SESSION_KEY
    key = f"{year}_{grand_prix}_{session_type}"
    if CURRENT_SESSION_KEY == key and CURRENT_SESSION is not None:
        return CURRENT_SESSION

    print(f"[Pit Wall Engine] Ingesting {year} {grand_prix} [{session_type}]...")
    session = fastf1.get_session(year, grand_prix, session_type)
    session.load(telemetry=True, laps=True, weather=True)
    CURRENT_SESSION = session
    CURRENT_SESSION_KEY = key
    return session

def get_performance_rankings(session):
    """
    Computes the 5 Middle Zone tables from the pit wall screen:
    1. S1 Rankings  2. S2 Rankings  3. S3 Rankings  4. Fastest Lap  5. Theoretical Best Lap
    """
    laps = session.laps.dropna(subset=["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]).copy()
    if laps.empty:
        return {}, pd.DataFrame()

    laps["S1_s"] = laps["Sector1Time"].dt.total_seconds()
    laps["S2_s"] = laps["Sector2Time"].dt.total_seconds()
    laps["S3_s"] = laps["Sector3Time"].dt.total_seconds()
    laps["Lap_s"] = laps["LapTime"].dt.total_seconds()

    # Driver-level best splits
    drivers = laps["Driver"].unique()
    records = []
    for d in drivers:
        d_laps = laps[laps["Driver"] == d]
        b_s1 = d_laps["S1_s"].min()
        b_s2 = d_laps["S2_s"].min()
        b_s3 = d_laps["S3_s"].min()
        b_lap = d_laps["Lap_s"].min()
        theo = b_s1 + b_s2 + b_s3
        records.append({
            "Driver": d,
            "Best_S1": b_s1,
            "Best_S2": b_s2,
            "Best_S3": b_s3,
            "Best_Lap": b_lap,
            "Theoretical": theo,
            "Potential_Gain": b_lap - theo
        })

    rank_df = pd.DataFrame(records)

    def fmt(sec):
        if pd.isna(sec): return "--"
        m = int(sec // 60)
        s = sec % 60
        return f"{m}:{s:06.3f}" if m > 0 else f"{s:.3f}"

    tables = {
        "s1": rank_df[["Driver", "Best_S1"]].sort_values("Best_S1").head(5).assign(Best_S1=lambda df: df["Best_S1"].apply(fmt)),
        "s2": rank_df[["Driver", "Best_S2"]].sort_values("Best_S2").head(5).assign(Best_S2=lambda df: df["Best_S2"].apply(fmt)),
        "s3": rank_df[["Driver", "Best_S3"]].sort_values("Best_S3").head(5).assign(Best_S3=lambda df: df["Best_S3"].apply(fmt)),
        "fastest": rank_df[["Driver", "Best_Lap"]].sort_values("Best_Lap").head(5).assign(Best_Lap=lambda df: df["Best_Lap"].apply(fmt)),
        "theo": rank_df[["Driver", "Theoretical", "Potential_Gain"]].sort_values("Theoretical").head(5).assign(
            Theoretical=lambda df: df["Theoretical"].apply(fmt),
            Potential_Gain=lambda df: df["Potential_Gain"].apply(lambda v: f"-{v:.3f}s")
        )
    }
    return tables, laps

def get_track_circuit_coords(session):
    """Pulls 2D GPS coordinates (X, Y) from fastest overall lap to draw track map."""
    try:
        fastest_lap = session.laps.pick_fastest()
        pos = fastest_lap.get_pos_data()
        return pos[["X", "Y"]].copy()
    except Exception:
        return pd.DataFrame()

def get_telemetry_trace(session, driver_code: str):
    """Pulls distance-aligned telemetry for a driver's fastest lap."""
    try:
        driver_code = driver_code.strip().upper()
        laps = session.laps.pick_drivers(driver_code)
        if laps.empty:
            return pd.DataFrame(), "--", "--"

        fastest = laps.pick_fastest()
        tel = fastest.get_car_data().add_distance()
        
        df = pd.DataFrame({
            "distance": tel["Distance"],
            "speed": tel["Speed"],
            "throttle": tel["Throttle"],
            "brake": tel["Brake"],
            "gear": tel["nGear"],
            "rpm": tel["RPM"],
            "drs": tel["DRS"]
        })
        sec = fastest["LapTime"].total_seconds()
        lap_time = f"{int(sec//60)}:{sec%60:06.3f}"
        return df, lap_time, fastest["Compound"]
    except Exception:
        return pd.DataFrame(), "--", "--"

def get_session_weather(session):
    """Pulls atmospheric conditions from session start to finish."""
    try:
        w = session.weather_data
        if w.empty: return {}
        last = w.iloc[-1]
        return {
            "air_temp": f"{last['AirTemp']:.1f}°C",
            "track_temp": f"{last['TrackTemp']:.1f}°C",
            "humidity": f"{last['Humidity']:.0f}%",
            "pressure": f"{last['Pressure']:.1f} mbar",
            "wind_speed": f"{last['WindSpeed']:.1f} m/s",
            "wind_direction": f"{int(last['WindDirection'])}°",
            "rainfall": "RAINING" if last["Rainfall"] else "DRY"
        }
    except Exception:
        return {}

import fastf1
import pandas as pd
from datetime import datetime

STATS_CACHE_FILE = "oscar_2026_stats.csv"

def get_or_update_oscar_campaign():
    """
    Scans the 2026 calendar, fetches completed race/sprint results for Oscar Piastri,
    and returns a cumulative DataFrame. Caches to CSV for speed.
    """
    now = datetime.utcnow()
    schedule = fastf1.get_event_schedule(2026)
    
    records = []
    cum_pts = 0

    for _, event in schedule.iterrows():
        # Skip events that have not occurred yet
        event_date = pd.to_datetime(event["Session5DateUtc"]) if pd.notnull(event.get("Session5DateUtc")) else pd.to_datetime(event["EventDate"])
        if pd.isnull(event_date) or event_date.tz_localize(None) > now:
            continue

        round_num = event["RoundNumber"]
        event_name = f"R{round_num:02d} {event['EventName'].replace(' Grand Prix', '')}"

        # 1. Check for Sprint Race if applicable
        if event.get("EventFormat") in ["sprint", "sprint_shootout", "sprint_qualifying"]:
            try:
                s_sess = fastf1.get_session(2026, round_num, "Sprint")
                s_sess.load(telemetry=False, laps=False, weather=False)
                res = s_sess.results
                pia_row = res[res["Abbreviation"] == "PIA"]
                if not pia_row.empty:
                    row = pia_row.iloc[0]
                    pts = float(row["Points"])
                    cum_pts += int(pts)
                    grid = f"P{int(row['GridPosition'])}" if pd.notnull(row['GridPosition']) else "--"
                    fin = f"P{int(row['Position'])}" if pd.notnull(row['Position']) and row['Status'] == 'Finished' else str(row['Status'])
                    records.append({
                        "Event": event_name,
                        "Session": "Sprint Race",
                        "Grid": grid,
                        "Finish": fin,
                        "Points": f"+{int(pts)}" if pts > 0 else "0",
                        "CumPoints": cum_pts,
                        "Note": "Sprint Pts" if pts > 0 else "--"
                    })
            except Exception:
                pass

        # 2. Grand Prix Main Race
        try:
            r_sess = fastf1.get_session(2026, round_num, "R")
            r_sess.load(telemetry=False, laps=False, weather=False)
            res = r_sess.results
            pia_row = res[res["Abbreviation"] == "PIA"]
            if not pia_row.empty:
                row = pia_row.iloc[0]
                pts = float(row["Points"])
                cum_pts += int(pts)
                grid = f"P{int(row['GridPosition'])}" if pd.notnull(row['GridPosition']) else "--"
                fin = f"P{int(row['Position'])}" if pd.notnull(row['Position']) and row['Status'] == 'Finished' else str(row['Status'])
                
                note = "Points" if pts > 0 else "--"
                if fin in ["P1"]: note = "Win"
                elif fin in ["P2", "P3"]: note = "Podium"
                elif "DNS" in fin: note = "DNS"
                elif "DNF" in fin or "Collision" in str(row['Status']): note = "DNF"

                records.append({
                    "Event": event_name,
                    "Session": "Grand Prix",
                    "Grid": grid,
                    "Finish": fin,
                    "Points": f"+{int(pts)}" if pts > 0 else "0",
                    "CumPoints": cum_pts,
                    "Note": note
                })
        except Exception:
            pass

    if records:
        df = pd.DataFrame(records)
        df.to_csv(STATS_CACHE_FILE, index=False)
        return df

    # Fallback to local cache if offline
    try:
        return pd.read_csv(STATS_CACHE_FILE)
    except Exception:
        return pd.DataFrame()
