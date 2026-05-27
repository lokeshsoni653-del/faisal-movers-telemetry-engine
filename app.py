# =============================================================================
# Faisal Movers | Live Intercity Fleet Telemetry Dashboard
# Author: Senior Python Data Architect
# Architecture: Streamlit + Pandas + Folium | Single-file, self-contained app
# Routes: M-4 (Lahore–Multan) | M-5 (Multan–Sukkur–Karachi)
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import time

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  —  must be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Faisal Movers | Fleet Telemetry",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  —  dark-mode professional aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ── */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }
    .stApp { background-color: #0d1117; color: #e6edf3; }

    /* ── Header Banner ── */
    .fm-header {
        background: linear-gradient(135deg, #1a2332 0%, #0d1117 60%, #162032 100%);
        border-bottom: 2px solid #1f6feb;
        padding: 18px 28px 14px;
        border-radius: 8px;
        margin-bottom: 22px;
    }
    .fm-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        color: #58a6ff;
        margin: 0;
        letter-spacing: 0.04em;
    }
    .fm-header p {
        margin: 4px 0 0;
        color: #8b949e;
        font-size: 0.85rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .live-dot {
        display: inline-block;
        width: 9px; height: 9px;
        background: #3fb950;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 1.6s infinite;
    }
    @keyframes pulse {
        0%,100% { opacity: 1; }
        50%      { opacity: 0.3; }
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #1f6feb; }
    .kpi-label {
        font-size: 0.72rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #58a6ff;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #3fb950;
        margin-top: 4px;
    }

    /* ── Section headings ── */
    .section-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        margin: 20px 0 10px;
        border-left: 3px solid #1f6feb;
        padding-left: 10px;
    }

    /* ── Dataframe overrides ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] .stButton>button {
        background: #1f6feb;
        color: #fff;
        border: none;
        border-radius: 6px;
        width: 100%;
        padding: 10px;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: #388bfd;
    }

    /* ── Status badges ── */
    .badge-green {
        background: #1a3a2a; color: #3fb950;
        padding: 2px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-red {
        background: #3a1a1a; color: #f85149;
        padding: 2px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }
    /* hide default Streamlit footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER  —  realistic mock telemetry for Pakistani motorway network
# ─────────────────────────────────────────────────────────────────────────────

# Waypoint anchors along M-4 & M-5 corridors (lat, lon)
ROUTE_WAYPOINTS = {
    "Lahore → Multan (M-4)": [
        (31.5204, 74.3587),   # Lahore Thokar Niaz Baig interchange
        (31.1704, 72.6981),   # Faisalabad vicinity
        (30.6900, 71.5830),   # Kabirwala
        (30.1575, 71.5249),   # Multan
    ],
    "Multan → Sukkur (M-5)": [
        (30.1575, 71.5249),   # Multan
        (29.3956, 71.0136),   # Bahawalpur
        (28.4212, 70.2989),   # Rahim Yar Khan
        (27.7052, 68.8573),   # Sukkur
    ],
    "Sukkur → Karachi (N-55/M-9)": [
        (27.7052, 68.8573),   # Sukkur
        (26.4131, 68.2856),   # Nawabshah
        (25.3960, 68.3578),   # Hyderabad
        (24.8607, 67.0104),   # Karachi
    ],
    "Lahore → Faisalabad (M-3)": [
        (31.5204, 74.3587),   # Lahore
        (31.4505, 73.6967),   # Sheikhupura
        (31.4100, 73.0790),   # Sangla Hill
        (31.4180, 72.9980),   # Faisalabad
    ],
    "Karachi → Hyderabad (M-9)": [
        (24.8607, 67.0104),   # Karachi
        (25.1614, 67.4558),   # Deh Hub
        (25.3960, 68.3578),   # Hyderabad
    ],
}

ROUTE_NAMES  = list(ROUTE_WAYPOINTS.keys())
BUS_PREFIXES = ["FM", "FMX", "FML"]   # Faisal Movers fleet codes


def interpolate_position(waypoints: list, progress: float) -> tuple:
    """
    Given a list of (lat, lon) waypoints and a progress ratio [0, 1],
    return the interpolated (lat, lon) along the route polyline.
    """
    n = len(waypoints) - 1
    seg_len = 1.0 / n
    seg_idx = min(int(progress / seg_len), n - 1)
    local_t  = (progress - seg_idx * seg_len) / seg_len
    lat = waypoints[seg_idx][0] + local_t * (waypoints[seg_idx + 1][0] - waypoints[seg_idx][0])
    lon = waypoints[seg_idx][1] + local_t * (waypoints[seg_idx + 1][1] - waypoints[seg_idx][1])
    # Add tiny GPS jitter to simulate real telemetry noise
    lat += np.random.uniform(-0.008, 0.008)
    lon += np.random.uniform(-0.008, 0.008)
    return round(lat, 5), round(lon, 5)


def generate_fleet_data(seed: int = None) -> pd.DataFrame:
    """
    Core data factory.  Called on every 'Refresh Telemetry' press.
    seed=None means true random (live simulation); pass an int for repeatable tests.
    """
    if seed is not None:
        np.random.seed(seed)

    now = datetime.now()
    records = []

    # 13 buses  —  mix of routes, stages, and conditions
    bus_configs = [
        ("FM-0421", "Lahore → Multan (M-4)",          0.15),
        ("FM-0389", "Lahore → Multan (M-4)",          0.72),
        ("FMX-117", "Multan → Sukkur (M-5)",          0.33),
        ("FMX-204", "Multan → Sukkur (M-5)",          0.88),
        ("FM-0556", "Sukkur → Karachi (N-55/M-9)",    0.10),
        ("FM-0601", "Sukkur → Karachi (N-55/M-9)",    0.55),
        ("FM-0734", "Sukkur → Karachi (N-55/M-9)",    0.91),
        ("FML-008", "Lahore → Faisalabad (M-3)",      0.40),
        ("FML-019", "Lahore → Faisalabad (M-3)",      0.77),
        ("FM-0290", "Lahore → Multan (M-4)",          0.48),
        ("FMX-331", "Multan → Sukkur (M-5)",          0.62),
        ("FM-0815", "Karachi → Hyderabad (M-9)",      0.25),
        ("FM-0902", "Karachi → Hyderabad (M-9)",      0.68),
    ]

    for bus_id, route, base_progress in bus_configs:
        # Jitter progress slightly to simulate movement between refreshes
        progress = np.clip(base_progress + np.random.uniform(-0.05, 0.05), 0.02, 0.97)
        waypoints = ROUTE_WAYPOINTS[route]
        lat, lon  = interpolate_position(waypoints, progress)

        speed      = int(np.random.normal(loc=105, scale=18))   # km/h  (motorway realistic)
        speed      = max(60, min(130, speed))
        fuel_burn  = round(np.random.uniform(24.0, 38.5), 1)    # L/100 km (coach diesel)
        cargo_kg   = int(np.random.uniform(800, 3200))          # luggage + freight
        passengers = int(np.random.uniform(28, 52))

        # ETA: rough remaining distance / average speed
        remaining  = 1.0 - progress
        route_km   = {"Lahore → Multan (M-4)": 340,
                      "Multan → Sukkur (M-5)": 420,
                      "Sukkur → Karachi (N-55/M-9)": 480,
                      "Lahore → Faisalabad (M-3)": 130,
                      "Karachi → Hyderabad (M-9)": 155}.get(route, 300)
        eta_hours  = (remaining * route_km) / max(speed, 1)
        eta_time   = now + timedelta(hours=eta_hours)
        eta_str    = eta_time.strftime("%H:%M")

        # Status logic: delayed if speed < 75 or random event
        delayed    = speed < 75 or np.random.random() < 0.18
        status     = "Delayed" if delayed else "On-Time"

        # Driver & engine telemetry
        engine_temp  = int(np.random.uniform(82, 97))           # °C
        oil_pressure = round(np.random.uniform(3.2, 4.8), 1)   # bar

        records.append({
            "Bus ID":           bus_id,
            "Route":            route,
            "Lat":              lat,
            "Lon":              lon,
            "Speed (km/h)":     speed,
            "Fuel Burn (L/100km)": fuel_burn,
            "Cargo (kg)":       cargo_kg,
            "Passengers":       passengers,
            "Engine Temp (°C)": engine_temp,
            "Oil Pressure (bar)": oil_pressure,
            "ETA":              eta_str,
            "Status":           status,
            "Progress (%)":     round(progress * 100, 1),
        })

    df = pd.DataFrame(records)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE  —  persist telemetry across Streamlit reruns
# ─────────────────────────────────────────────────────────────────────────────
if "fleet_df" not in st.session_state:
    st.session_state["fleet_df"]      = generate_fleet_data()
    st.session_state["last_refresh"]  = datetime.now().strftime("%H:%M:%S")
    st.session_state["refresh_count"] = 1


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  —  dispatch controls & filters
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Dispatch Control")
    st.markdown("---")

    # Route filter
    all_routes = ["All Routes"] + ROUTE_NAMES
    selected_route = st.selectbox("Filter by Route", all_routes)

    # Status filter
    selected_status = st.radio(
        "Filter by Status",
        ["All", "On-Time", "Delayed"],
        horizontal=False,
    )

    st.markdown("---")

    # Live refresh button
    if st.button("🔄  Refresh Telemetry"):
        st.session_state["fleet_df"]      = generate_fleet_data()
        st.session_state["last_refresh"]  = datetime.now().strftime("%H:%M:%S")
        st.session_state["refresh_count"] += 1
        st.rerun()

    st.markdown(
        f"<small style='color:#8b949e;'>Last pull: "
        f"<b style='color:#3fb950;'>{st.session_state['last_refresh']}</b><br>"
        f"Total refreshes: {st.session_state['refresh_count']}</small>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "<small style='color:#8b949e;'>**Faisal Movers TMS**<br>"
        "Fleet Telemetry v2.4.1<br>"
        "Data cadence: ~30 s real-world</small>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────
df: pd.DataFrame = st.session_state["fleet_df"].copy()

if selected_route != "All Routes":
    df = df[df["Route"] == selected_route]

if selected_status != "All":
    df = df[df["Status"] == selected_status]


# ─────────────────────────────────────────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="fm-header">
    <h1>🚌 Faisal Movers &nbsp;|&nbsp; Live Intercity Fleet Telemetry</h1>
    <p><span class="live-dot"></span>M-4 · M-5 · M-3 · M-9 Corridor Operations &nbsp;•&nbsp; Real-Time Dispatch Intelligence</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI METRICS ROW
# ─────────────────────────────────────────────────────────────────────────────
full_df = st.session_state["fleet_df"]   # always from unfiltered fleet for fleet-wide KPIs

total_active   = len(full_df)
avg_speed      = int(full_df["Speed (km/h)"].mean())
total_cargo    = int(full_df["Cargo (kg)"].sum())
delayed_count  = int((full_df["Status"] == "Delayed").sum())
net_status     = "⚠ High Traffic" if delayed_count >= 3 else "✅ Optimal"
net_color      = "#f0883e" if delayed_count >= 3 else "#3fb950"
total_pax      = int(full_df["Passengers"].sum())

col1, col2, col3, col4, col5 = st.columns(5)

def kpi(col, label, value, sub):
    col.markdown(
        f'<div class="kpi-card">'
        f'  <div class="kpi-label">{label}</div>'
        f'  <div class="kpi-value">{value}</div>'
        f'  <div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

kpi(col1, "Active Fleet",       total_active,         "buses on network")
kpi(col2, "Avg Fleet Speed",    f"{avg_speed} km/h",  "motorway average")
kpi(col3, "Total Cargo",        f"{total_cargo:,} kg", "freight + luggage")
kpi(col4, "Total Passengers",   total_pax,             "across all coaches")
col5.markdown(
    f'<div class="kpi-card">'
    f'  <div class="kpi-label">Network Status</div>'
    f'  <div class="kpi-value" style="font-size:1.1rem;color:{net_color};">{net_status}</div>'
    f'  <div class="kpi-sub">{delayed_count} delayed of {total_active}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FOLIUM MAP  —  central Pakistan, M-4/M-5 corridor
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📍 Live Fleet Position Map</div>', unsafe_allow_html=True)

# Dark-tile basemap for the professional aesthetic
m = folium.Map(
    location=[28.5, 70.5],      # Center ~between Multan and Sukkur
    zoom_start=6,
    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attr="© OpenStreetMap contributors © CARTO",
    max_zoom=18,
)

# Draw route polylines for context
for route_name, wps in ROUTE_WAYPOINTS.items():
    folium.PolyLine(
        locations=wps,
        color="#1f6feb",
        weight=2.5,
        opacity=0.55,
        tooltip=route_name,
    ).add_to(m)

# Plot each bus in the filtered view
for _, row in df.iterrows():
    color      = "#3fb950" if row["Status"] == "On-Time" else "#f85149"
    icon_color = "green"   if row["Status"] == "On-Time" else "red"

    popup_html = f"""
    <div style="font-family:Segoe UI,sans-serif;min-width:200px;background:#161b22;
                color:#e6edf3;padding:10px;border-radius:6px;">
        <b style="color:#58a6ff;font-size:1rem;">{row['Bus ID']}</b><br>
        <span style="color:#8b949e;font-size:0.8rem;">{row['Route']}</span><hr style="border-color:#30363d;margin:6px 0;">
        🚀 Speed: <b>{row['Speed (km/h)']} km/h</b><br>
        ⛽ Burn:  <b>{row['Fuel Burn (L/100km)']} L/100 km</b><br>
        🧳 Cargo: <b>{row['Cargo (kg)']} kg</b><br>
        👥 Pax:   <b>{row['Passengers']}</b><br>
        🌡 Engine: <b>{row['Engine Temp (°C)']} °C</b><br>
        🕐 ETA:   <b>{row['ETA']}</b><br>
        📶 Status: <b style="color:{'#3fb950' if row['Status']=='On-Time' else '#f85149'};">{row['Status']}</b>
    </div>
    """

    folium.Marker(
        location=[row["Lat"], row["Lon"]],
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"{row['Bus ID']} — {row['Speed (km/h)']} km/h",
        icon=folium.Icon(color=icon_color, icon="bus", prefix="fa"),
    ).add_to(m)

# Render the Folium map inside Streamlit
st_folium(m, width="100%", height=480, returned_objects=[])


# ─────────────────────────────────────────────────────────────────────────────
# TELEMETRY DATA MATRIX
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Telemetry Data Matrix</div>', unsafe_allow_html=True)

# Select display columns only (hide raw lat/lon from the table)
display_cols = [
    "Bus ID", "Route", "Speed (km/h)", "Fuel Burn (L/100km)",
    "Cargo (kg)", "Passengers", "Engine Temp (°C)",
    "Oil Pressure (bar)", "ETA", "Status", "Progress (%)",
]
display_df = df[display_cols].reset_index(drop=True)

# Apply colour coding to the Status column via a Pandas Styler
def style_status(val):
    color = "#3fb950" if val == "On-Time" else "#f85149"
    bg    = "#1a3a2a" if val == "On-Time" else "#3a1a1a"
    return f"color:{color};background-color:{bg};border-radius:4px;padding:2px 6px;font-weight:600;"

def style_speed(val):
    if val >= 110:
        return "color:#f0883e;"     # fast  — amber
    elif val < 75:
        return "color:#f85149;"     # slow  — red (likely delayed)
    return "color:#e6edf3;"

styled = (
    display_df.style
    .map(style_status, subset=["Status"])
    .map(style_speed,  subset=["Speed (km/h)"])
    .set_properties(**{
        "background-color": "#161b22",
        "color":            "#e6edf3",
        "border-color":     "#30363d",
    })
    .set_table_styles([
        {"selector": "thead th",
         "props": [("background-color", "#0d1117"),
                   ("color", "#8b949e"),
                   ("font-size", "0.78rem"),
                   ("text-transform", "uppercase"),
                   ("letter-spacing", "0.06em"),
                   ("border-bottom", "2px solid #30363d")]},
        {"selector": "tbody tr:hover td",
         "props": [("background-color", "#1c2128")]},
    ])
    .format({
        "Speed (km/h)":        "{} km/h",
        "Fuel Burn (L/100km)": "{} L",
        "Cargo (kg)":          "{:,} kg",
        "Engine Temp (°C)":    "{} °C",
        "Oil Pressure (bar)":  "{} bar",
        "Progress (%)":        "{}%",
    })
    .hide(axis="index")
)

st.dataframe(styled, use_container_width=True, height=420)


# ─────────────────────────────────────────────────────────────────────────────
# SECONDARY ANALYTICS ROW
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Route Analytics Snapshot</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**Buses per Route**")
    route_counts = (
        full_df.groupby("Route")
               .size()
               .reset_index(name="Buses")
               .sort_values("Buses", ascending=False)
    )
    st.dataframe(
        route_counts.style
            .set_properties(**{"background-color": "#161b22", "color": "#e6edf3"})
            .hide(axis="index"),
        use_container_width=True,
        height=220,
    )

with col_b:
    st.markdown("**Average Speed per Route**")
    route_speed = (
        full_df.groupby("Route")["Speed (km/h)"]
               .mean()
               .round(1)
               .reset_index()
               .sort_values("Speed (km/h)", ascending=False)
    )
    route_speed.columns = ["Route", "Avg Speed (km/h)"]
    st.dataframe(
        route_speed.style
            .set_properties(**{"background-color": "#161b22", "color": "#e6edf3"})
            .hide(axis="index"),
        use_container_width=True,
        height=220,
    )

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#30363d;margin-top:30px;">
<p style="text-align:center;color:#484f58;font-size:0.75rem;margin:0;">
    Faisal Movers Transport Management System &nbsp;·&nbsp; Fleet Telemetry Module v2.4.1 &nbsp;·&nbsp;
    Data is simulated for portfolio demonstration purposes only
</p>
""", unsafe_allow_html=True)
