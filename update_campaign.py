import os
import pandas as pd
import fastf1

CACHE_FILE = "oscar_2026_stats.csv"

# Current baseline up to Round 16
BASELINE = [
    {"Event": "R01 Australia", "Session": "Grand Prix", "Grid": "P5", "Finish": "DNS", "Points": "0", "CumPoints": 0, "Note": "DNS"},
    {"Event": "R02 China", "Session": "Sprint Race", "Grid": "P8", "Finish": "P6", "Points": "+3", "CumPoints": 3, "Note": "Sprint Pts"},
    {"Event": "R02 China", "Session": "Grand Prix", "Grid": "P5", "Finish": "DNS", "Points": "0", "CumPoints": 3, "Note": "DNS"},
    {"Event": "R03 Japan", "Session": "Grand Prix", "Grid": "P3", "Finish": "P2", "Points": "+18", "CumPoints": 21, "Note": "Podium"},
    {"Event": "R04 Miami", "Session": "Sprint Race", "Grid": "P3", "Finish": "P2", "Points": "+7", "CumPoints": 28, "Note": "Sprint Podium"},
    {"Event": "R04 Miami", "Session": "Grand Prix", "Grid": "P7", "Finish": "P3", "Points": "+15", "CumPoints": 43, "Note": "Podium"},
    {"Event": "R05 Canada", "Session": "Sprint Race", "Grid": "P4", "Finish": "P4", "Points": "+5", "CumPoints": 48, "Note": "Sprint Pts"},
    {"Event": "R05 Canada", "Session": "Grand Prix", "Grid": "P4", "Finish": "P11", "Points": "0", "CumPoints": 48, "Note": "Finished"},
    {"Event": "R06 Monaco", "Session": "Grand Prix", "Grid": "P7", "Finish": "P4", "Points": "+12", "CumPoints": 60, "Note": "Points"},
    {"Event": "R07 Barcelona", "Session": "Grand Prix", "Grid": "P7", "Finish": "P5", "Points": "+10", "CumPoints": 70, "Note": "Points"},
    {"Event": "R08 Austria", "Session": "Grand Prix", "Grid": "P7", "Finish": "P4", "Points": "+12", "CumPoints": 82, "Note": "Points"},
    {"Event": "R09 Silverstone", "Session": "Sprint Race", "Grid": "P7", "Finish": "P7", "Points": "+2", "CumPoints": 84, "Note": "Sprint Pts"},
    {"Event": "R09 Silverstone", "Session": "Grand Prix", "Grid": "P8", "Finish": "P11", "Points": "0", "CumPoints": 84, "Note": "Finished"},
    {"Event": "R10 Spa", "Session": "Grand Prix", "Grid": "P6", "Finish": "P5", "Points": "+10", "CumPoints": 94, "Note": "Points"},
    {"Event": "R11 Hungary", "Session": "Grand Prix", "Grid": "P3", "Finish": "DNF", "Points": "0", "CumPoints": 94, "Note": "Contact + PU"},
    {"Event": "R12 Zandvoort", "Session": "Sprint Race", "Grid": "P4", "Finish": "P5", "Points": "+4", "CumPoints": 98, "Note": "Sprint Pts"},
    {"Event": "R12 Zandvoort", "Session": "Grand Prix", "Grid": "P4", "Finish": "P6", "Points": "+8", "CumPoints": 106, "Note": "Points"},
    {"Event": "R13 Monza", "Session": "Grand Prix", "Grid": "P6", "Finish": "P5", "Points": "+10", "CumPoints": 116, "Note": "Points"},
    {"Event": "R14 Madrid", "Session": "Grand Prix", "Grid": "P7", "Finish": "P8", "Points": "+4", "CumPoints": 120, "Note": "Points"},
    {"Event": "R15 Baku", "Session": "Grand Prix", "Grid": "P3", "Finish": "P13", "Points": "0", "CumPoints": 120, "Note": "Finished"},
    {"Event": "R16 Sepang", "Session": "Grand Prix", "Grid": "P6", "Finish": "P6", "Points": "+8", "CumPoints": 128, "Note": "Points"},
]

def add_round(event_name, session_type, grid, finish, points, note=""):
    # Load current file or initialize from baseline
    df = pd.read_csv(CACHE_FILE) if os.path.exists(CACHE_FILE) else pd.DataFrame(BASELINE)
    
    last_cum = df["CumPoints"].iloc[-1]
    new_cum = last_cum + int(points)
    
    new_row = {
        "Event": event_name,
        "Session": session_type,
        "Grid": f"P{grid}" if str(grid).isdigit() else str(grid),
        "Finish": f"P{finish}" if str(finish).isdigit() else str(finish),
        "Points": f"+{points}" if int(points) > 0 else "0",
        "CumPoints": new_cum,
        "Note": note or ("Podium" if finish in [1, 2, 3, "P1", "P2", "P3"] else "Points" if int(points) > 0 else "Finished")
    }
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CACHE_FILE, index=False)
    print(f"✓ Added {event_name} [{session_type}]: Finish {new_row['Finish']}, Total Points = {new_cum}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 6:
        print("Usage: python3 update_campaign.py '<Event>' '<Session>' <Grid> <Finish> <Points> ['<Note>']")
        print("Example: python3 update_campaign.py 'R17 COTA' 'Sprint Race' 3 2 7 'Sprint Podium'")
        sys.exit(0)
    
    evt, sess, grd, fin, pts = sys.argv[1:6]
    note = sys.argv[6] if len(sys.argv) > 6 else ""
    add_round(evt, sess, grd, fin, pts, note)
