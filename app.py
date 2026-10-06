import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from engine import start_f1_listener, get_processed_trace

start_f1_listener()

DEFAULT_PRIMARY_COLOR = "#ff8700"   # Fallback Car 1 color
DEFAULT_COMPARE_COLOR = "#00e5ff"   # Fallback Car 2 color

app = dash.Dash(__name__)
app.title = "live telemetry!"

# Grid Livery Color Palette :)
DRIVER_COLORS = {
    # McLaren
    "81": "#ff8700",  # Piastri
    "4":  "#e07700",  # Norris
    "1":  "#e07700",  # Norris (if running champion #1)

    # Ferrari
    "16": "#e8002d",  # Leclerc
    "44": "#b40023",  # Hamilton

    # Mercedes 
    "63": "#00d2be",  # Russell
    "12": "#22ada0",  # Antonelli

    # Red Bull Racing 
    "3":  "#1e41ff",  # Verstappen
    "6":  "#4e62cd",  # hadjar

    # Aston Martin 
    "14": "#229971",  # Alonso
    "18": "#006945",  # Stroll

    # Williams 
    "23": "#006cbd",  # Albon
    "55": "#008af2",  # Sainz

    # Alpine
    "10": "#00a0de",  # Gasly
    "43": "#4790ac",  # colapinto

    # Racing Bulls
    "22": "#6692ff",  # Tsunoda
    "30": "#4178ff",  # Lawson
    "41": "#6692ff",  # Lindblad

    # Haas 
    "87": "#b6babd",  # Bearman
    "31": "#e10600",  # Ocon

    # Audi
    "27": "#999999",  # Hulkenberg
    "5":  "#5b5b5b",  # Bortoleto

    # Cadillac
    "77": "#e2aa00",  # Bottas
    "11": "#c09d32",  # perez
}

STATUS_STYLES = {
    "1": {"text": "ALL CLEAR", "color": "#00e676", "bg": "rgba(0, 230, 118, 0.15)"},
    "2": {"text": "YELLOW FLAG", "color": "#ffd600", "bg": "rgba(255, 214, 0, 0.2)"},
    "4": {"text": "SAFETY CAR (SC)", "color": "#ff9100", "bg": "rgba(255, 145, 0, 0.25)"},
    "5": {"text": "RED FLAG - STOPPED", "color": "#ff1744", "bg": "rgba(255, 23, 68, 0.25)"},
    "6": {"text": "VIRTUAL SC (VSC)", "color": "#ff9100", "bg": "rgba(255, 145, 0, 0.25)"},
    "7": {"text": "VSC ENDING", "color": "#ffd600", "bg": "rgba(255, 214, 0, 0.2)"},
}

app.layout = html.Div(
    style={
        "backgroundColor": "#08090b",
        "color": "#e1e4ea",
        "fontFamily": "'JetBrains Mono', 'SF Mono', Consolas, monospace",
        "padding": "12px 18px",
        "minHeight": "100vh",
        "boxSizing": "border-box"
    },
    children=[
        # TOP STATUS & WEATHER BAR
        html.Div(
            style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "backgroundColor": "#0f1217", "border": "1px solid #1e2430", "borderRadius": "4px",
                "padding": "8px 16px", "marginBottom": "12px"
            },
            children=[
                # Dynamic Track Status Badge
                html.Div([
                    html.Span("TRACK STATUS: ", style={"color": "#6e798d", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span(id="track-status-badge", children="connecting...")
                ]),
                # Dynamic Weather Readout
                html.Div([
                    html.Span("air: ", style={"color": "#6e798d", "fontSize": "11px"}),
                    html.Span(id="air-temp-val", children="--", style={"color": "#fff", "fontSize": "12px"}),
                    html.Span("  |  track: ", style={"color": "#6e798d", "fontSize": "11px"}),
                    html.Span(id="track-temp-val", children="--", style={"color": "#ff8700", "fontSize": "12px"}),
                    html.Span("  |  rain: ", style={"color": "#6e798d", "fontSize": "11px"}),
                    html.Span(id="rain-val", children="--", style={"color": "#00e5ff", "fontSize": "12px"}),
                ]),
                html.Div([
                    html.Span("pitwall telemetry console", style={"color": "#ffe7fb", "fontSize": "11px"}),
                ])
            ]
        ),

        # DRIVER SELECTORS & LIVE HUD
        html.Div(
            style={"display": "flex", "gap": "16px", "alignItems": "center", "marginBottom": "12px", "fontSize": "12px"},
            children=[
                html.Div([
                    html.Label("primary car: ", style={"color": "#ffe7fb", "fontWeight": "700"}),
                    dcc.Input(id="driver-1", type="text", value="81", style={"backgroundColor": "#13171e", "color": "#fff", "border": "1px solid #2b3545", "width": "45px", "textAlign": "center", "padding": "4px"})
                ]),
                html.Div([
                    html.Label("comparison car: ", style={"color": "#e7f9ff", "fontWeight": "700"}),
                    dcc.Input(id="driver-2", type="text", value="4", style={"backgroundColor": "#13171e", "color": "#fff", "border": "1px solid #2b3545", "width": "45px", "textAlign": "center", "padding": "4px"})
                ]),
                html.Div(id="live-hud-readout", style={"display": "flex", "gap": "20px", "marginLeft": "auto"})
            ]
        ),

        # MULTI-PLOT TELEMETRY CONTAINER
        html.Div(
            style={"border": "1px solid #1a202c", "borderRadius": "4px", "backgroundColor": "#0c0e12", "padding": "6px"},
            children=[
                dcc.Graph(id="pitwall-traces", config={"displayModeBar": False}, style={"height": "76vh"})
            ]
        ),

        dcc.Interval(id="pitwall-clock", interval=250, n_intervals=0)
    ]
)

@app.callback(
    [
        Output("pitwall-traces", "figure"),
        Output("live-hud-readout", "children"),
        Output("track-status-badge", "children"),
        Output("track-status-badge", "style"),
        Output("air-temp-val", "children"),
        Output("track-temp-val", "children"),
        Output("rain-val", "children")
    ],
    [Input("pitwall-clock", "n_intervals"), Input("driver-1", "value"), Input("driver-2", "value")]
)
def render_pitwall(n, d1_num, d2_num):
    d1_str, d2_str = str(d1_num).strip(), str(d2_num).strip()
    df1 = get_processed_trace(d1_str)
    df2 = get_processed_trace(d2_str)

    # 1. Update Track Status Badge
    status_info = get_track_status()
    code = status_info.get("status", "1")
    style_spec = STATUS_STYLES.get(code, STATUS_STYLES["1"])
    badge_label = style_spec["text"]
    badge_style = {
        "color": style_spec["color"],
        "backgroundColor": style_spec["bg"],
        "fontWeight": "800",
        "fontSize": "12px",
        "padding": "3px 8px",
        "borderRadius": "3px",
        "letterSpacing": "0.5px"
    }

    # 2. Update Weather Information
    weather = get_live_weather()
    air_display = f"{weather['air_temp']}°C" if weather['air_temp'] != "--" else "--°C"
    track_display = f"{weather['track_temp']}°C" if weather['track_temp'] != "--" else "--°C"
    rain_display = "YES" if str(weather['rainfall']).strip() in ["1", "true", "True"] else "0.0%"

    # 3. Build Telemetry Subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=(
            "speed delta (kph)",
            "throttle (solid) & brake (dashed) [%]",
            "gear",
            "engine rpm"
        ),
        row_heights=[0.42, 0.26, 0.16, 0.16]
    )

    c1_color = DRIVER_COLORS.get(d1_str, "#ffe7fb")
    c2_color = DRIVER_COLORS.get(d2_str, "#e7f9ff")
    if c1_color == c2_color:
        c2_color = "#00e5ff"

    def add_driver_traces(df, color, name):
        if df.empty:
            return
        x = df["distance"]
        fig.add_trace(go.Scatter(x=x, y=df["speed"], mode="lines", name=f"#{name} Speed", line=dict(color=color, width=2.0)), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["throttle"], mode="lines", name=f"#{name} Throttle", line=dict(color=color, width=1.4)), row=2, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["brake"], mode="lines", name=f"#{name} Brake", line=dict(color=color, width=1.2, dash="dot")), row=2, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["gear"], mode="lines", name=f"#{name} Gear", line=dict(color=color, width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["rpm"], mode="lines", name=f"#{name} RPM", line=dict(color=color, width=1.2)), row=4, col=1)

    add_driver_traces(df1, c1_color, d1_str)
    add_driver_traces(df2, c2_color, d2_str)

    # 4. Update HUD Items
    hud_items = []
    if not df1.empty:
        latest = df1.iloc[-1]
        hud_items = [
            html.Span([html.B(f"#{d1_str} SPEED: "), f"{int(latest['speed'])} KM/H"], style={"color": c1_color}),
            html.Span([html.B("GEAR: "), f"{int(latest['gear'])}"], style={"color": "#fff"}),
            html.Span([html.B("RPM: "), f"{int(latest['rpm'])}"], style={"color": "#fff"}),
            html.Span([html.B("DRS: "), "ACTIVE" if latest['drs'] == 1 else "OFF"], style={"color": "#00e676" if latest['drs'] == 1 else "#555"}),
        ]

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0c0e12",
        paper_bgcolor="#0c0e12",
        margin=dict(l=45, r=25, t=25, b=25),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=10)),
        font=dict(family="JetBrains Mono, monospace", size=10, color="#8b949e")
    )

    for i in range(1, 5):
        fig.update_xaxes(row=i, col=1, gridcolor="#161b22", zeroline=False)
        fig.update_yaxes(row=i, col=1, gridcolor="#161b22", zeroline=False)

    fig.update_yaxes(range=[0, 360], row=1, col=1)
    fig.update_yaxes(range=[-5, 105], row=2, col=1)
    fig.update_yaxes(range=[0, 9], row=3, col=1)
    fig.update_xaxes(title_text="Cumulative Track Distance (m)", row=4, col=1)

    return fig, hud_items, badge_label, badge_style, air_display, track_display, rain_display

if __name__ == "__main__":
    app.run(debug=False, port=8050)
