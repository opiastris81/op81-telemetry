import base64
import json
import zlib
import threading
from collections import deque
import pandas as pd
from signalrcore.hub_connection_builder import HubConnectionBuilder

driver_telemetry = {}
telemetry_lock = threading.Lock()

# Global states for track status and weather
current_track_status = {
    "status": "1",
    "message": "ALL CLEAR"
}

current_weather = {
    "air_temp": "--",
    "track_temp": "--",
    "rainfall": "--",
    "humidity": "--",
    "wind_speed": "--"
}

def decode_f1_payload(raw_b64: str) -> dict:
    try:
        compressed_bytes = base64.b64decode(raw_b64)
        decompressed = zlib.decompress(compressed_bytes, -zlib.MAX_WBITS)
        return json.loads(decompressed.decode("utf-8"))
    except Exception:
        return {}

def process_car_data_payload(payload: dict):
    entries = payload.get("Entries", [])
    with telemetry_lock:
        for entry in entries:
            utc_timestamp = entry.get("Utc")
            cars = entry.get("Cars", {})
            for car_number, car_data in cars.items():
                channels = car_data.get("Channels", {})
                if not channels:
                    continue

                point = {
                    "utc": utc_timestamp,
                    "speed": float(channels.get("0", 0.0)),
                    "rpm": int(channels.get("2", 0)),
                    "gear": int(channels.get("3", 0)),
                    "throttle": float(channels.get("4", 0.0)),
                    "brake": float(channels.get("5", 0.0)),
                    "drs": int(channels.get("45", 0)),
                }

                if car_number not in driver_telemetry:
                    driver_telemetry[car_number] = deque(maxlen=600)
                driver_telemetry[car_number].append(point)

def on_feed(data):
    if not data or len(data) < 2:
        return
    topic = data[0]
    raw_payload = data[1]

    if topic == "CarData.z":
        decoded = decode_f1_payload(raw_payload)
        process_car_data_payload(decoded)

    elif topic == "TrackStatus":
        global current_track_status
        status_data = raw_payload if isinstance(raw_payload, dict) else {}
        code = str(status_data.get("Status", "1"))
        msg = str(status_data.get("Message", "AllClear"))
        with telemetry_lock:
            current_track_status["status"] = code
            current_track_status["message"] = msg

    elif topic == "WeatherData":
        # Raw payload contains trackside sensor values
        global current_weather
        weather_data = raw_payload if isinstance(raw_payload, dict) else {}
        with telemetry_lock:
            current_weather["air_temp"] = str(weather_data.get("AirTemp", "--"))
            current_weather["track_temp"] = str(weather_data.get("TrackTemp", "--"))
            current_weather["rainfall"] = str(weather_data.get("Rainfall", "0"))
            current_weather["humidity"] = str(weather_data.get("Humidity", "--"))
            current_weather["wind_speed"] = str(weather_data.get("WindSpeed", "--"))

def start_f1_listener():
    url = "https://livetiming.formula1.com/signalrcore"
    hub_connection = (
        HubConnectionBuilder()
        .with_url(url, options={"verify_ssl": True})
        .build()
    )
    hub_connection.on("feed", on_feed)

    def on_open():
        print("[Live Client] Subscribing to CarData, TrackStatus, and WeatherData...")
        hub_connection.send("Subscribe", [["CarData.z", "TrackStatus", "WeatherData", "Heartbeat"]])

    hub_connection.on_open(on_open)
    t = threading.Thread(target=hub_connection.start, daemon=True)
    t.start()
    return hub_connection

def get_track_status():
    with telemetry_lock:
        return current_track_status.copy()

def get_live_weather():
    with telemetry_lock:
        return current_weather.copy()

def get_processed_trace(driver_num: str):
    with telemetry_lock:
        if driver_num not in driver_telemetry or len(driver_telemetry[driver_num]) < 2:
            return pd.DataFrame()
        raw_list = list(driver_telemetry[driver_num])

    df = pd.DataFrame(raw_list)
    df["utc"] = pd.to_datetime(df["utc"])
    df["dt"] = df["utc"].diff().dt.total_seconds().fillna(0.0)
    v_ms = df["speed"] / 3.6
    v_avg = (v_ms + v_ms.shift(1).fillna(v_ms)) / 2.0
    df["delta_dist"] = v_avg * df["dt"]
    df["distance"] = df["delta_dist"].cumsum()
    return df
