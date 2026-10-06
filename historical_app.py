import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

from historical_engine import (
    load_past_session, get_performance_rankings, get_track_circuit_coords,
    get_telemetry_trace, get_session_weather
)

app = dash.Dash(__name__)
server = app.server
app.title = "OP81 PITWALL"

# Official High-Resolution Transparent Assets
OSCAR_AVATAR_URL = "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png"
MCLAREN_CAR_URL = "https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/mclaren.png"
MCLAREN_LOGO_URL = "https://media.formula1.com/content/dam/fom-website/teams/2024/mclaren-logo.png"

DRIVER_COLORS = {
    "PIA": "#ffa4d9", "NOR": "#00e5ff",
    "LEC": "#e8002d", "HAM": "#b40023",
    "RUS": "#00d2be", "ANT": "#22ada0",
    "VER": "#1e41ff", "HAD": "#4e62cd",
    "ALO": "#229971", "STR": "#006945",
    "ALB": "#006cbd", "SAI": "#008af2",
    "GAS": "#00a0de", "COL": "#4790ac",
    "LIN": "#6692ff", "LAW": "#4178ff",
    "BOR": "#999999", "HUL": "#5b5b5b",
    "BEA": "#b6babd", "OCO": "#e10600",
    "BOT": "#e2aa00", "PER": "#c09d32",
}

RIVAL_OPTIONS = [
    {"label": "NOR - Lando Norris", "value": "NOR"},
    {"label": "VER - Max Verstappen", "value": "VER"},
    {"label": "HAM - Lewis Hamilton", "value": "HAM"},
    {"label": "LEC - Charles Leclerc", "value": "LEC"},
    {"label": "RUS - George Russell", "value": "RUS"},
    {"label": "ANT - Kimi Antonelli", "value": "ANT"},
    {"label": "HAD - Isack Hadjar", "value": "HAD"},
    {"label": "LAW - Liam Lawson", "value": "LAW"},
    {"label": "GAS - Pierre Gasly", "value": "GAS"},
    {"label": "ALO - Fernando Alonso", "value": "ALO"},
    {"label": "SAI - Carlos Sainz", "value": "SAI"},
    {"label": "ALB - Alex Albon", "value": "ALB"},
    {"label": "COL - Franco Colapinto", "value": "COL"},
    {"label": "LIN - Arvid Lindblad", "value": "LIN"},
    {"label": "BOR - Gabriel Bortoleto", "value": "BOR"},
    {"label": "HUL - Nico Hülkenberg", "value": "HUL"},
    {"label": "BEA - Oliver Bearman", "value": "BEA"},
    {"label": "OCO - Esteban Ocon", "value": "OCO"},
    {"label": "STR - Lance Stroll", "value": "STR"},
    {"label": "BOT - Valtteri Bottas", "value": "BOT"},
    {"label": "PER - Sergio Pérez", "value": "PER"},
]

RACES_2026 = [
    {"label": "R01 - Australia (Albert Park)", "value": "Australia"},
    {"label": "R02 - China (Shanghai)", "value": "China"},
    {"label": "R03 - Japan (Suzuka)", "value": "Japan"},
    {"label": "R04 - Miami (Miami)", "value": "Miami"},
    {"label": "R05 - Canada (Montreal)", "value": "Canada"},
    {"label": "R06 - Monaco (Monte Carlo)", "value": "Monaco"},
    {"label": "R07 - Barcelona-Catalunya", "value": "Barcelona"},
    {"label": "R08 - Austria (Red Bull Ring)", "value": "Austria"},
    {"label": "R09 - Great Britain (Silverstone)", "value": "Silverstone"},
    {"label": "R10 - Belgium (Spa)", "value": "Spa"},
    {"label": "R11 - Hungary (Hungaroring)", "value": "Hungary"},
    {"label": "R12 - Netherlands (Zandvoort)", "value": "Zandvoort"},
    {"label": "R13 - Italy (Monza)", "value": "Monza"},
    {"label": "R14 - Spain (Madrid)", "value": "Madrid"},
    {"label": "R15 - Azerbaijan (Baku)", "value": "Baku"},
    {"label": "R16 - Bahrain (Sepang)", "value": "Malaysia"},
    {"label": "R17 - Singapore (Marina Bay)", "value": "Singapore"},
    {"label": "R18 - USA (Austin)", "value": "United States"},
    {"label": "R19 - Mexico (Mexico City)", "value": "Mexico"},
    {"label": "R20 - Brazil (Interlagos)", "value": "Brazil"},
    {"label": "R21 - Las Vegas", "value": "Las Vegas"},
    {"label": "R22 - Qatar (Lusail)", "value": "Qatar"},
    {"label": "R23 - Abu Dhabi (Yas Marina)", "value": "Abu Dhabi"},
]

CIRCUIT_STRATEGY_PROFILES = {
    "Australia":   {"green": "20.8s", "sc": "11.2s", "pit_limit": "80 km/h"},
    "China":       {"green": "23.2s", "sc": "13.1s", "pit_limit": "80 km/h"},
    "Japan":       {"green": "22.4s", "sc": "12.6s", "pit_limit": "80 km/h"},
    "Miami":       {"green": "20.1s", "sc": "11.5s", "pit_limit": "80 km/h"},
    "Canada":      {"green": "18.5s", "sc": "10.4s", "pit_limit": "80 km/h"},
    "Monaco":      {"green": "25.0s", "sc": "15.2s", "pit_limit": "60 km/h"},
    "Barcelona":   {"green": "22.6s", "sc": "12.8s", "pit_limit": "80 km/h"},
    "Austria":     {"green": "20.5s", "sc": "11.4s", "pit_limit": "80 km/h"},
    "Silverstone": {"green": "19.8s", "sc": "10.9s", "pit_limit": "80 km/h"},
    "Spa":         {"green": "22.9s", "sc": "12.7s", "pit_limit": "80 km/h"},
    "Hungary":     {"green": "21.6s", "sc": "12.1s", "pit_limit": "80 km/h"},
    "Zandvoort":   {"green": "20.2s", "sc": "11.6s", "pit_limit": "60 km/h"},
    "Monza":       {"green": "24.5s", "sc": "14.5s", "pit_limit": "80 km/h"},
    "Madrid":      {"green": "22.0s", "sc": "12.3s", "pit_limit": "80 km/h"},
    "Baku":        {"green": "21.2s", "sc": "11.8s", "pit_limit": "80 km/h"},
    "Malaysia":    {"green": "23.8s", "sc": "13.4s", "pit_limit": "80 km/h"},
}

def make_rank_table(df, title, header_col):
    return html.Div(
        style={"backgroundColor": "#0d1015", "border": "1px solid #1a202c", "padding": "8px", "borderRadius": "4px", "minWidth": "160px", "flex": "1"},
        children=[
            html.H5(title, style={"color": "#ffa4d9", "fontSize": "10px", "margin": "0 0 6px 0", "fontWeight": "800", "letterSpacing": "0.5px"}),
            dash_table.DataTable(
                columns=[{"name": "DVR", "id": "Driver"}, {"name": header_col, "id": df.columns[1]}],
                data=df.to_dict("records"),
                style_header={"backgroundColor": "#13171e", "color": "#7e889b", "fontSize": "10px", "border": "none", "fontWeight": "bold"},
                style_cell={"backgroundColor": "#090a0d", "color": "#fff", "fontSize": "11px", "padding": "5px 6px", "border": "1px solid #141820", "textAlign": "center"}
            )
        ]
    )

app.layout = html.Div(
    style={
        "backgroundColor": "#060709", "color": "#e1e4ea",
        "fontFamily": "'JetBrains Mono', -apple-system, BlinkMacSystemFont, monospace",
        "padding": "12px 18px", "minHeight": "100vh", "boxSizing": "border-box"
    },
    children=[
        # TOP SLIM HEADER WITH AVATAR & BRANDING
        html.Div(
            style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "backgroundColor": "#0d1015", "border": "1px solid #1a202c", "padding": "8px 16px",
                "borderRadius": "5px", "marginBottom": "10px"
            },
            children=[
                # Left Title + Oscar Profile Avatar
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "10px"},
                    children=[
                        html.Img(
                            src=OSCAR_AVATAR_URL,
                            style={
                                "height": "36px", "width": "36px", "borderRadius": "50%",
                                "border": "2px solid #ffa4d9", "backgroundColor": "#13171e",
                                "objectFit": "cover"
                            }
                        ),
                        html.Div([
                            html.Span("oscar piastri #81 telemetry! // ", style={"color": "#ffa4d9", "fontWeight": "800", "fontSize": "14px", "letterSpacing": "0.5px"}),
                            html.Span("dev. by opiastris81", style={"color": "#fff", "fontWeight": "700", "fontSize": "14px", "letterSpacing": "0.5px"}),
                        ])
                    ]
                ),
                # Right Dropdowns and Ingest Button
                html.Div(
                    style={"display": "flex", "gap": "10px", "alignItems": "center"},
                    children=[
                        dcc.Dropdown(
                            id="gp-select",
                            options=RACES_2026,
                            value=None,
                            placeholder="select grand prix...",
                            clearable=True,
                            style={"width": "230px", "color": "#000", "fontSize": "12px"}
                        ),
                        dcc.Dropdown(
                            id="session-select",
                            options=[
                                {"label": "race", "value": "R"},
                                {"label": "quali", "value": "Q"},
                                {"label": "sprint", "value": "S"},
                                {"label": "sprint quali", "value": "SQ"},
                                {"label": "fp3", "value": "FP3"},
                                {"label": "fp2", "value": "FP2"},
                                {"label": "fp1", "value": "FP1"}
                            ],
                            value=None,
                            placeholder="select session...",
                            clearable=True,
                            style={"width": "170px", "color": "#000", "fontSize": "12px"}
                        ),
                        html.Button("LOAD", id="load-btn", n_clicks=0, style={"backgroundColor": "#ffa4d9", "color": "#000", "border": "none", "fontWeight": "800", "fontSize": "11px", "padding": "6px 14px", "cursor": "pointer", "borderRadius": "3px"}),
                        html.Div(id="load-status", style={"fontSize": "11px", "color": "#00e676", "marginLeft": "6px"})
                    ]
                )
            ]
        ),

        # MAIN CONSOLE GRID
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "220px 1fr", "gap": "10px"},
            children=[
                # LEFT SIDEBAR
                html.Div(
                    style={"display": "flex", "flexDirection": "column", "gap": "8px"},
                    children=[
                        # Meteorology Box
                        html.Div(
                            style={"backgroundColor": "#0d1015", "border": "1px solid #1a202c", "padding": "10px 12px", "borderRadius": "4px"},
                            children=[
                                html.H4("METEOROLOGY", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "800", "margin": "0 0 8px 0", "letterSpacing": "0.5px"}),
                                html.Div(id="weather-panel", style={"fontSize": "11px", "display": "flex", "flexDirection": "column", "gap": "5px"})
                            ]
                        ),
                        # Dynamic Strategy Window Box
                        html.Div(
                            style={"backgroundColor": "#0d1015", "border": "1px solid #1a202c", "padding": "10px 12px", "borderRadius": "4px"},
                            children=[
                                html.H4("STRATEGY WINDOW", style={"color": "#ffa4d9", "fontSize": "10px", "fontWeight": "800", "margin": "0 0 8px 0", "letterSpacing": "0.5px"}),
                                html.Div(id="strategy-panel", style={"fontSize": "11px"})
                            ]
                        ),
                        # Drivers Target Box with Dropdown Selector + Car Graphic
                        html.Div(
                            style={"backgroundColor": "#0d1015", "border": "1px solid #1a202c", "padding": "10px 12px", "borderRadius": "4px"},
                            children=[
                                html.H4("CAR PROFILES", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "800", "margin": "0 0 6px 0", "letterSpacing": "0.5px"}),
                                html.Div([html.Span("DRIVER: "), html.B("PIA #81", style={"color": "#ffa4d9"})], style={"fontSize": "11px", "marginBottom": "6px"}),
                                html.Div([
                                    html.Label("OTHER: ", style={"color": "#e7f9ff", "fontSize": "10px", "fontWeight": "700", "marginBottom": "3px", "display": "block"}),
                                    dcc.Dropdown(
                                        id="rival-code",
                                        options=RIVAL_OPTIONS,
                                        value=None,
                                        placeholder="select driver...",
                                        clearable=True,
                                        style={"color": "#000", "fontSize": "11px"}
                                    )
                                ]),
                                # Clean McLaren F1 Car Silhouette Cutout
                                html.Div(
                                    style={"marginTop": "10px", "paddingTop": "6px", "borderTop": "1px solid #141820", "textAlign": "center"},
                                    children=[
                                        html.Img(src=MCLAREN_CAR_URL, style={"width": "100%", "opacity": "0.85", "filter": "drop-shadow(0 2px 4px rgba(255, 164, 217, 0.2))"})
                                    ]
                                )
                            ]
                        )
                    ]
                ),

                # RIGHT DASHBOARD TABS
                html.Div(
                    style={"backgroundColor": "#0d1015", "border": "1px solid #1a202c", "borderRadius": "5px", "padding": "8px 12px"},
                    children=[
                        dcc.Tabs(
                            id="pitwall-tabs", value="tab-telemetry",
                            colors={"border": "#1a202c", "primary": "#ffa4d9", "background": "#07080a"},
                            children=[
                                dcc.Tab(label="telemetry + delta", value="tab-telemetry", style={"padding": "6px 12px", "fontSize": "11px"}, selected_style={"fontWeight": "bold", "color": "#ffa4d9", "padding": "6px 12px"}),
                                dcc.Tab(label="sector rankings overall", value="tab-rankings", style={"padding": "6px 12px", "fontSize": "11px"}, selected_style={"fontWeight": "bold", "color": "#ffa4d9", "padding": "6px 12px"}),
                                dcc.Tab(label="gps circuit", value="tab-gps", style={"padding": "6px 12px", "fontSize": "11px"}, selected_style={"fontWeight": "bold", "color": "#ffa4d9", "padding": "6px 12px"}),
                                dcc.Tab(label="pace monitor", value="tab-pace", style={"padding": "6px 12px", "fontSize": "11px"}, selected_style={"fontWeight": "bold", "color": "#ffa4d9", "padding": "6px 12px"}),
                                dcc.Tab(label="oscar's 2026 statistics!", value="tab-season", style={"padding": "6px 12px", "fontSize": "11px"}, selected_style={"fontWeight": "bold", "color": "#ffa4d9", "padding": "6px 12px"}),
                            ]
                        ),
                        html.Div(id="pitwall-tab-body", style={"marginTop": "8px"})
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    [
        Output("pitwall-tab-body", "children"),
        Output("weather-panel", "children"),
        Output("strategy-panel", "children"),
        Output("load-status", "children")
    ],
    [Input("load-btn", "n_clicks"), Input("pitwall-tabs", "value")],
    [State("gp-select", "value"), State("session-select", "value"), State("rival-code", "value")]
)
def render_pitwall_console(n_clicks, active_tab, gp, session_type, rival_code):
    rival_code = rival_code.strip().upper() if (rival_code and str(rival_code).strip()) else None

    # Standby UI if Grand Prix or Session is unselected
    if not gp or not session_type:
        standby_msg = "[ select a grand prix and session, then click load to ingest telemetry data! ]"
        empty_weather = [
            html.Div([html.Span("AIR: "), html.B("--", style={"color": "#fff"})]),
            html.Div([html.Span("TRACK: "), html.B("--", style={"color": "#ffa4d9"})]),
            html.Div([html.Span("PRESS: "), html.B("--", style={"color": "#fff"})]),
            html.Div([html.Span("HUMID: "), html.B("--", style={"color": "#e7f9ff"})]),
            html.Div([html.Span("WIND: "), html.B("--", style={"color": "#fff"})]),
            html.Div([html.Span("RAIN: "), html.B("--", style={"color": "#e7f9ff"})]),
        ]
        empty_strat = [
            html.Div("no track selected :(", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "bold"})
        ]

        if active_tab == "tab-season":
            pass
        else:
            placeholder_view = html.Div(
                standby_msg,
                style={
                    "display": "flex", "justifyContent": "center", "alignItems": "center",
                    "height": "650px", "color": "#6e798d", "fontSize": "12px",
                    "letterSpacing": "1px", "fontFamily": "JetBrains Mono, monospace"
                }
            )
            return placeholder_view, empty_weather, empty_strat, "waiting to load :)"

    session = load_past_session(2026, gp, session_type)

    # 1. DYNAMIC WEATHER EXTRACTION
    w = get_session_weather(session)
    weather_ui = [
        html.Div([html.Span("AIR: "), html.B(w.get("air_temp", "--"), style={"color": "#fff"})]),
        html.Div([html.Span("TRACK: "), html.B(w.get("track_temp", "--"), style={"color": "#ffa4d9"})]),
        html.Div([html.Span("PRESS: "), html.B(w.get("pressure", "--"), style={"color": "#fff"})]),
        html.Div([html.Span("HUMID: "), html.B(w.get("humidity", "--"), style={"color": "#e7f9ff"})]),
        html.Div([html.Span("WIND: "), html.B(f"{w.get('wind_speed', '--')} @ {w.get('wind_direction', '--')}", style={"color": "#fff"})]),
        html.Div([html.Span("RAIN: "), html.B(w.get("rainfall", "--"), style={"color": "#00e676" if w.get("rainfall") == "DRY" else "#e7f9ff"})]),
    ]

    # 2. DYNAMIC CIRCUIT-SPECIFIC STRATEGY WINDOW
    prof = CIRCUIT_STRATEGY_PROFILES.get(gp, {"green": "21.5s", "sc": "12.0s", "pit_limit": "80 km/h"})

    try:
        p_laps = session.laps.pick_drivers("PIA")
        if not p_laps.empty:
            stints = p_laps.dropna(subset=["Stint", "Compound"]).drop_duplicates(subset=["Stint"])
            stint_parts = []
            for _, s_row in stints.iterrows():
                comp_char = str(s_row["Compound"])[0].upper()
                stint_laps = len(p_laps[p_laps["Stint"] == s_row["Stint"]])
                stint_parts.append(f"{comp_char} ({stint_laps}L)")
            actual_strategy = " -> ".join(stint_parts) if stint_parts else "M -> H (EST)"
        else:
            actual_strategy = "NO STINT DATA"
    except Exception:
        actual_strategy = "M -> H (EST)"

    strategy_ui = [
        html.Div([html.Span("DELTA (GRN): "), html.B(prof["green"], style={"color": "#fff"})], style={"marginBottom": "3px"}),
        html.Div([html.Span("DELTA (SC): "), html.B(prof["sc"], style={"color": "#00e676"})], style={"marginBottom": "3px"}),
        html.Div([html.Span("PIT LIMIT: "), html.B(prof["pit_limit"], style={"color": "#00e5ff"})], style={"marginBottom": "6px"}),
        html.Div([html.Span("TYRE STINTS: "), html.B(actual_strategy, style={"color": "#ffa4d9", "fontSize": "10px"})])
    ]

    status_msg = f"✓ 2026 {gp} [{session_type}]"

    # TAB 1: TELEMETRY (OSCAR SOLO BY DEFAULT -> RIVAL ADDED ON SELECTION)
    if active_tab == "tab-telemetry":
        df_pia, t_pia, comp_pia = get_telemetry_trace(session, "PIA")

        df_riv, t_riv, comp_riv = (pd.DataFrame(), "--", "--")
        if rival_code:
            df_riv, t_riv, comp_riv = get_telemetry_trace(session, rival_code)

        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.38, 0.20, 0.26, 0.16]
        )

        # Oscar Piastri Traces
        if not df_pia.empty:
            x_pia = df_pia["distance"]
            fig.add_trace(go.Scatter(x=x_pia, y=df_pia["speed"], mode="lines", name=f"PIA Speed ({t_pia})", line=dict(color="#ffa4d9", width=2.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=x_pia, y=df_pia["throttle"], mode="lines", name="PIA Throttle", line=dict(color="#ffa4d9", width=1.5)), row=3, col=1)
            b_pia = df_pia["brake"] * 100 if df_pia["brake"].max() <= 1.0 else df_pia["brake"]
            fig.add_trace(go.Scatter(x=x_pia, y=b_pia, mode="lines", name="PIA Brake", line=dict(color="#ffa4d9", width=2.0, dash="dash")), row=3, col=1)
            fig.add_trace(go.Scatter(x=x_pia, y=df_pia["gear"], mode="lines", name="PIA Gear", line=dict(color="#ffa4d9", width=1.5)), row=4, col=1)

        # Rival Traces
        if rival_code and not df_riv.empty:
            riv_color = DRIVER_COLORS.get(rival_code, "#00e5ff")
            x_riv = df_riv["distance"]
            fig.add_trace(go.Scatter(x=x_riv, y=df_riv["speed"], mode="lines", name=f"{rival_code} Speed ({t_riv})", line=dict(color=riv_color, width=1.8)), row=1, col=1)
            fig.add_trace(go.Scatter(x=x_riv, y=df_riv["throttle"], mode="lines", name=f"{rival_code} Throttle", line=dict(color=riv_color, width=1.3)), row=3, col=1)
            b_riv = df_riv["brake"] * 100 if df_riv["brake"].max() <= 1.0 else df_riv["brake"]
            fig.add_trace(go.Scatter(x=x_riv, y=b_riv, mode="lines", name=f"{rival_code} Brake", line=dict(color=riv_color, width=1.6, dash="dot")), row=3, col=1)
            fig.add_trace(go.Scatter(x=x_riv, y=df_riv["gear"], mode="lines", name=f"{rival_code} Gear", line=dict(color=riv_color, width=1.3)), row=4, col=1)

            min_d = max(df_pia["distance"].min(), df_riv["distance"].min())
            max_d = min(df_pia["distance"].max(), df_riv["distance"].max())
            if max_d > min_d:
                grid = np.linspace(min_d, max_d, 1200)
                delta = np.interp(grid, df_pia["distance"], df_pia["speed"]) - np.interp(grid, df_riv["distance"], df_riv["speed"])
                delta_pos = np.where(delta >= 0, delta, 0)
                delta_neg = np.where(delta < 0, delta, 0)

                fig.add_trace(go.Scatter(
                    x=grid, y=delta_pos, mode="lines", name="PIA Faster (+km/h)",
                    line=dict(color="#00e676", width=1.2), fill="tozeroy", fillcolor="rgba(0, 230, 118, 0.28)"
                ), row=2, col=1)

                fig.add_trace(go.Scatter(
                    x=grid, y=delta_neg, mode="lines", name=f"{rival_code} Faster (+km/h)",
                    line=dict(color="#ff1744", width=1.2), fill="tozeroy", fillcolor="rgba(255, 23, 68, 0.28)"
                ), row=2, col=1)
        else:
            fig.add_annotation(
                text="   [ select a driver from the dropdown and press load to compare data from any session ! ]",
                xref="x2 domain", yref="y2 domain",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=11, color="#6e798d", family="JetBrains Mono, monospace")
            )

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="#08090b",
            paper_bgcolor="#08090b",
            height=860,
            margin=dict(l=65, r=20, t=55, b=30),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=11, family="JetBrains Mono, monospace")
            ),
            font=dict(family="JetBrains Mono, monospace", size=10, color="#8b949e")
        )

        for i in range(1, 5):
            fig.update_xaxes(row=i, col=1, gridcolor="#141820", zeroline=False)
            fig.update_yaxes(row=i, col=1, gridcolor="#141820", zeroline=False)

        fig.update_yaxes(title_text="SPEED (km/h)", range=[0, 360], row=1, col=1)
        fig.update_yaxes(title_text="Δ SPEED (km/h)", row=2, col=1)
        fig.update_yaxes(title_text="PEDALS (%)", range=[-5, 105], row=3, col=1)
        fig.update_yaxes(title_text="GEAR", range=[0, 9], tickmode="linear", tick0=1, dtick=1, row=4, col=1)
        fig.update_xaxes(title_text="Track Distance (m)", row=4, col=1)

        return dcc.Graph(figure=fig, config={"displayModeBar": False}), weather_ui, strategy_ui, status_msg

    # TAB 2: SECTOR RANKINGS
    elif active_tab == "tab-rankings":
        rank_tables, _ = get_performance_rankings(session)
        if not rank_tables:
            return html.Div("No lap times available for rankings.", style={"padding": "30px", "color": "#7e889b"}), weather_ui, strategy_ui, status_msg

        tables_ui = html.Div(
            style={"display": "flex", "flexWrap": "wrap", "gap": "10px", "marginTop": "6px"},
            children=[
                make_rank_table(rank_tables["s1"], "SECTOR 1 RANK", "TIME"),
                make_rank_table(rank_tables["s2"], "SECTOR 2 RANK", "TIME"),
                make_rank_table(rank_tables["s3"], "SECTOR 3 RANK", "TIME"),
                make_rank_table(rank_tables["fastest"], "FASTEST LAP", "TIME"),
                make_rank_table(rank_tables["theo"], "THEORETICAL BEST", "IDEAL"),
            ]
        )
        return tables_ui, weather_ui, strategy_ui, status_msg

    # TAB 3: CIRCUIT GPS TRACE
    elif active_tab == "tab-gps":
        coords = get_track_circuit_coords(session)
        fig_gps = go.Figure()
        if not coords.empty:
            fig_gps.add_trace(go.Scatter(
                x=coords["X"], y=coords["Y"], mode="lines",
                line=dict(color="#ffa4d9", width=3.5), name="Circuit Line"
            ))
        fig_gps.update_layout(
            template="plotly_dark", plot_bgcolor="#08090b", paper_bgcolor="#08090b",
            height=620, margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
            title=f"2D GPS TRACK LAYOUT // 2026 {gp}"
        )
        return dcc.Graph(figure=fig_gps, config={"displayModeBar": False}), weather_ui, strategy_ui, status_msg

    # TAB 4: OSCAR BROADCAST TIMING MATRIX
    elif active_tab == "tab-pace":
        laps = session.laps.pick_drivers("PIA").copy().sort_values("LapNumber")
        if laps.empty:
            return html.Div("No lap data for Oscar in this session.", style={"padding": "30px"}), weather_ui, strategy_ui, status_msg

        laps["Lap_s"] = laps["LapTime"].dt.total_seconds()
        laps["S1_s"] = laps["Sector1Time"].dt.total_seconds()
        laps["S2_s"] = laps["Sector2Time"].dt.total_seconds()
        laps["S3_s"] = laps["Sector3Time"].dt.total_seconds()

        overall_fastest_lap = laps["Lap_s"].min()
        overall_fastest_s1 = laps["S1_s"].min()
        overall_fastest_s2 = laps["S2_s"].min()
        overall_fastest_s3 = laps["S3_s"].min()

        valid_laps = laps.dropna(subset=["LapTime"]).copy()
        valid_laps["prev_best_lap"] = valid_laps["Lap_s"].shift(1).cummin()
        valid_laps["prev_best_s1"] = valid_laps["S1_s"].shift(1).cummin()
        valid_laps["prev_best_s2"] = valid_laps["S2_s"].shift(1).cummin()
        valid_laps["prev_best_s3"] = valid_laps["S3_s"].shift(1).cummin()

        pb_map_lap = dict(zip(valid_laps["LapNumber"], valid_laps["prev_best_lap"]))
        pb_map_s1 = dict(zip(valid_laps["LapNumber"], valid_laps["prev_best_s1"]))
        pb_map_s2 = dict(zip(valid_laps["LapNumber"], valid_laps["prev_best_s2"]))
        pb_map_s3 = dict(zip(valid_laps["LapNumber"], valid_laps["prev_best_s3"]))

        def resolve_sector_status(val, prev_pb, overall_best):
            if pd.isna(val): return "DEFAULT"
            if np.isclose(val, overall_best, atol=0.001): return "PURPLE"
            if pd.notnull(prev_pb) and val < (prev_pb - 0.001): return "GREEN"
            return "DEFAULT"

        def format_lap_row(row):
            num = row["LapNumber"]
            is_in = pd.notnull(row.get("PitInTime"))
            is_out = pd.notnull(row.get("PitOutTime"))

            if is_in: lap_str, lap_status = "IN LAP", "PIT"
            elif is_out: lap_str, lap_status = "OUT LAP", "PIT"
            elif pd.isna(row["LapTime"]): lap_str, lap_status = "NO TIME", "PIT"
            else:
                sec = row["Lap_s"]
                lap_str = f"{int(sec//60)}:{sec%60:06.3f}"
                if np.isclose(sec, overall_fastest_lap, atol=0.001): lap_status = "PURPLE"
                elif pd.notnull(pb_map_lap.get(num)) and sec < (pb_map_lap.get(num) - 0.001): lap_status = "GREEN"
                else: lap_status = "DEFAULT"

            s1_status = resolve_sector_status(row["S1_s"], pb_map_s1.get(num), overall_fastest_s1)
            s2_status = resolve_sector_status(row["S2_s"], pb_map_s2.get(num), overall_fastest_s2)
            s3_status = resolve_sector_status(row["S3_s"], pb_map_s3.get(num), overall_fastest_s3)

            return (
                lap_str, lap_status,
                f"{row['S1_s']:.3f}" if pd.notnull(row['S1_s']) else "--", s1_status,
                f"{row['S2_s']:.3f}" if pd.notnull(row['S2_s']) else "--", s2_status,
                f"{row['S3_s']:.3f}" if pd.notnull(row['S3_s']) else "--", s3_status,
            )

        processed_rows = [format_lap_row(row) for _, row in laps.iterrows()]

        summary = pd.DataFrame({
            "Lap": laps["LapNumber"].astype(int),
            "Compound": laps["Compound"].fillna("--"),
            "LapTime": [r[0] for r in processed_rows],
            "Lap_Status": [r[1] for r in processed_rows],
            "S1": [r[2] for r in processed_rows],
            "S1_Status": [r[3] for r in processed_rows],
            "S2": [r[4] for r in processed_rows],
            "S2_Status": [r[5] for r in processed_rows],
            "S3": [r[6] for r in processed_rows],
            "S3_Status": [r[7] for r in processed_rows],
            "TyreLife": laps["TyreLife"].fillna(0).astype(int)
        })

        pace_table = dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in ["Lap", "Compound", "LapTime", "S1", "S2", "S3", "TyreLife"]],
            data=summary.to_dict("records"),
            style_header={"backgroundColor": "#13171e", "color": "#ffa4d9", "fontWeight": "bold", "fontSize": "11px", "border": "1px solid #1a202c"},
            style_cell={"backgroundColor": "#090a0d", "color": "#d0d4dc", "fontSize": "11px", "padding": "5px", "textAlign": "center", "fontFamily": "JetBrains Mono, monospace", "border": "1px solid #141820"},
            style_data_conditional=[
                {"if": {"column_id": "LapTime", "filter_query": '{Lap_Status} eq "PIT"'}, "color": "#6e798d", "fontStyle": "italic"},
                {"if": {"column_id": "LapTime", "filter_query": '{Lap_Status} eq "GREEN"'}, "color": "#00e676", "fontWeight": "bold"},
                {"if": {"column_id": "LapTime", "filter_query": '{Lap_Status} eq "PURPLE"'}, "backgroundColor": "rgba(179, 136, 255, 0.22)", "color": "#d6a4ff", "fontWeight": "bold", "border": "1px solid #b388ff"},
                {"if": {"column_id": "S1", "filter_query": '{S1_Status} eq "GREEN"'}, "color": "#00e676", "fontWeight": "bold"},
                {"if": {"column_id": "S1", "filter_query": '{S1_Status} eq "PURPLE"'}, "color": "#d6a4ff", "fontWeight": "bold", "backgroundColor": "rgba(179, 136, 255, 0.15)"},
                {"if": {"column_id": "S2", "filter_query": '{S2_Status} eq "GREEN"'}, "color": "#00e676", "fontWeight": "bold"},
                {"if": {"column_id": "S2", "filter_query": '{S2_Status} eq "PURPLE"'}, "color": "#d6a4ff", "fontWeight": "bold", "backgroundColor": "rgba(179, 136, 255, 0.15)"},
                {"if": {"column_id": "S3", "filter_query": '{S3_Status} eq "GREEN"'}, "color": "#00e676", "fontWeight": "bold"},
                {"if": {"column_id": "S3", "filter_query": '{S3_Status} eq "PURPLE"'}, "color": "#d6a4ff", "fontWeight": "bold", "backgroundColor": "rgba(179, 136, 255, 0.15)"},
                {"if": {"column_id": "Compound", "filter_query": '{Compound} eq "SOFT"'}, "color": "#ff1744", "fontWeight": "bold"},
                {"if": {"column_id": "Compound", "filter_query": '{Compound} eq "MEDIUM"'}, "color": "#ffd600", "fontWeight": "bold"},
                {"if": {"column_id": "Compound", "filter_query": '{Compound} eq "HARD"'}, "color": "#ffffff", "fontWeight": "bold"},
                {"if": {"column_id": "Compound", "filter_query": '{Compound} eq "INTERMEDIATE"'}, "color": "#00e676", "fontWeight": "bold"},
                {"if": {"column_id": "Compound", "filter_query": '{Compound} eq "WET"'}, "color": "#00e5ff", "fontWeight": "bold"},
            ],
            page_size=20
        )
        return pace_table, weather_ui, strategy_ui, status_msg

    # TAB 5: OSCAR 2026 CAMPAIGN STATS (AUTO-SYNC READY + GUARANTEED DISPLAY)
    elif active_tab == "tab-season":
        # 1. Base verified records up to Round 16 (Sepang)
        baseline_records = [
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

        # 2. Try loading dynamic upcoming race results from local cache or FastF1
        campaign_2026 = baseline_records
        try:
            import os
            if os.path.exists("oscar_2026_stats.csv"):
                cached_df = pd.read_csv("oscar_2026_stats.csv")
                if not cached_df.empty:
                    campaign_2026 = cached_df.to_dict("records")
        except Exception:
            pass

        # 3. Dynamic metrics derived from actual rows
        total_pts = campaign_2026[-1]["CumPoints"] if campaign_2026 else 128
        gp_podiums = sum(1 for r in campaign_2026 if r["Session"] == "Grand Prix" and r["Finish"] in ["P1", "P2", "P3"])
        spr_podiums = sum(1 for r in campaign_2026 if r["Session"] == "Sprint Race" and r["Finish"] in ["P1", "P2", "P3"])

        hero_banner = html.Div(
            style={
                "display": "flex", "alignItems": "center", "justifyContent": "space-between",
                "backgroundColor": "#0d1015", "border": "1px solid #ffa4d9",
                "borderRadius": "5px", "padding": "10px 18px", "marginBottom": "12px",
                "background": "linear-gradient(90deg, #0d1015 65%, rgba(255, 164, 217, 0.15) 100%)"
            },
            children=[
                html.Div([
                    html.H3("OSCAR PIASTRI 2026 STATISTICS", style={"color": "#ffa4d9", "margin": "0 0 4px 0", "fontSize": "14px", "fontWeight": "800"}),
                    html.Div("MCLAREN FORMULA 1 TEAM • CAR #81", style={"color": "#8b949e", "fontSize": "10px", "letterSpacing": "0.5px"})
                ]),
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "14px"},
                    children=[
                        html.Img(src=MCLAREN_LOGO_URL, style={"height": "22px", "filter": "brightness(0) invert(1)"}),
                        html.Img(src=OSCAR_AVATAR_URL, style={"height": "46px", "borderRadius": "50%", "border": "1.5px solid #ffa4d9"})
                    ]
                )
            ]
        )

        stat_cards = html.Div(
            style={"display": "flex", "gap": "10px", "marginBottom": "12px"},
            children=[
                html.Div([
                    html.Div("CHAMPIONSHIP RANK", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "700"}),
                    html.Div("P7", style={"color": "#ffa4d9", "fontSize": "20px", "fontWeight": "800"})
                ], style={"backgroundColor": "#090a0d", "border": "1px solid #1a202c", "padding": "8px 14px", "borderRadius": "4px", "flex": "1"}),
                html.Div([
                    html.Div("TOTAL POINTS (WDC)", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "700"}),
                    html.Div(f"{total_pts} PTS", style={"color": "#00e676", "fontSize": "20px", "fontWeight": "800"})
                ], style={"backgroundColor": "#090a0d", "border": "1px solid #1a202c", "padding": "8px 14px", "borderRadius": "4px", "flex": "1"}),
                html.Div([
                    html.Div("PODIUMS (GP + SPRINT)", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "700"}),
                    html.Div(f"{gp_podiums + spr_podiums} ({gp_podiums} GP + {spr_podiums} SPR)", style={"color": "#00e5ff", "fontSize": "18px", "fontWeight": "800", "marginTop": "2px"})
                ], style={"backgroundColor": "#090a0d", "border": "1px solid #1a202c", "padding": "8px 14px", "borderRadius": "4px", "flex": "1"}),
                html.Div([
                    html.Div("CAR NUMBER", style={"color": "#6e798d", "fontSize": "10px", "fontWeight": "700"}),
                    html.Div("MCLAREN #81", style={"color": "#fff", "fontSize": "17px", "fontWeight": "800", "marginTop": "2px"})
                ], style={"backgroundColor": "#090a0d", "border": "1px solid #1a202c", "padding": "8px 14px", "borderRadius": "4px", "flex": "1"}),
            ]
        )

        pts_events = [r for r in campaign_2026 if r["Session"] in ["Grand Prix", "Sprint Race"]]
        fig_pts = go.Figure()
        fig_pts.add_trace(go.Scatter(
            x=[f"{r['Event'].split()[0]} {r['Session'][:3]}" for r in pts_events],
            y=[r["CumPoints"] for r in pts_events],
            mode="lines+markers",
            line=dict(color="#ffa4d9", width=2.2),
            marker=dict(size=6, color="#00e5ff"),
            name="Cumulative Points"
        ))
        fig_pts.update_layout(
            template="plotly_dark", plot_bgcolor="#08090b", paper_bgcolor="#08090b",
            height=230, margin=dict(l=35, r=15, t=25, b=25),
            title="2026 WDC POINTS PROGRESSION // GRAND PRIX & SPRINT COMBINED",
            font=dict(family="JetBrains Mono, monospace", size=9, color="#8b949e")
        )
        fig_pts.update_yaxes(gridcolor="#141820", zeroline=False)
        fig_pts.update_xaxes(gridcolor="#141820", zeroline=False)

        season_table = dash_table.DataTable(
            columns=[
                {"name": "EVENT", "id": "Event"},
                {"name": "SESSION", "id": "Session"},
                {"name": "GRID", "id": "Grid"},
                {"name": "FINISH", "id": "Finish"},
                {"name": "POINTS", "id": "Points"},
                {"name": "CUMULATIVE", "id": "CumPoints"},
                {"name": "NOTES", "id": "Note"},
            ],
            data=campaign_2026,
            style_header={"backgroundColor": "#13171e", "color": "#ffa4d9", "fontWeight": "bold", "fontSize": "11px", "border": "1px solid #1a202c"},
            style_cell={"backgroundColor": "#090a0d", "color": "#fff", "fontSize": "11px", "padding": "5px", "textAlign": "center", "fontFamily": "JetBrains Mono, monospace", "border": "1px solid #141820"},
            style_data_conditional=[
                {"if": {"column_id": "Finish", "filter_query": '{Finish} eq "P1"'}, "color": "#ffd600", "fontWeight": "bold"},
                {"if": {"column_id": "Finish", "filter_query": '{Finish} eq "P2" || {Finish} eq "P3"'}, "color": "#00e676", "fontWeight": "bold"},
                {"if": {"column_id": "Points", "filter_query": '{Points} contains "+"'}, "color": "#00e5ff", "fontWeight": "bold"},
                {"if": {"column_id": "Session", "filter_query": '{Session} contains "Sprint"'}, "backgroundColor": "rgba(0, 229, 255, 0.06)"},
            ],
            page_size=24
        )

        season_ui = html.Div([
            hero_banner,
            stat_cards,
            dcc.Graph(figure=fig_pts, config={"displayModeBar": False}),
            html.Div(style={"marginTop": "10px"}, children=[season_table])
        ])

        return season_ui, weather_ui, strategy_ui, status_msg


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8054))
    app.run(host="0.0.0.0", port=port, debug=False)
