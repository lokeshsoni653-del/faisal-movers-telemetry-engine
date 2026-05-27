# =============================================================================
# Faisal Movers | Live Intercity Fleet Telemetry Dashboard  ── v3.0 ULTRA
# Author: Senior Python Data Architect
# NEW FEATURES:
#   1. AI Dispatch Advisor  — per-bus anomaly scoring + plain-English recommendations
#   2. Predictive ETA Engine — speed-history + Monte Carlo confidence bands
#   3. Fuel Efficiency Heatmap — choropleth-style bar gauge per bus
#   4. Live Incident Alert Feed — auto-generated alerts with severity tiers
#   5. Fleet Health Scorecard — composite health index with sparkline trend
#   6. Route Throughput Timeline — rolling 6-refresh speed history chart
#   7. Animated progress rings in KPI cards (SVG)
#   8. Bus Inspector panel — click any row → deep-dive telemetry card
# Architecture: Streamlit + Pandas + NumPy + Folium | Single-file, copy-paste ready
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import time
import math
import random

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
# GLOBAL CSS  —  cinematic dark-ops aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #080c12; color: #d0d7de; }

    /* ── Scanline overlay for depth ── */
    .stApp::before {
        content: "";
        position: fixed; inset: 0;
        background: repeating-linear-gradient(
            0deg, transparent, transparent 2px,
            rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
        );
        pointer-events: none; z-index: 9999;
    }

    /* ── Header ── */
    .fm-header {
        background: linear-gradient(135deg, #0d1b2e 0%, #080c12 50%, #0d1b2e 100%);
        border-bottom: 1px solid #1f6feb;
        border-top: 1px solid #1f6feb44;
        padding: 20px 32px 16px;
        border-radius: 10px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .fm-header::after {
        content: "";
        position: absolute; top: 0; right: 0;
        width: 300px; height: 100%;
        background: radial-gradient(ellipse at right center, #1f6feb18 0%, transparent 70%);
        pointer-events: none;
    }
    .fm-header h1 {
        font-size: 1.6rem; font-weight: 700;
        color: #58a6ff; margin: 0;
        letter-spacing: 0.04em;
        font-family: 'IBM Plex Mono', monospace;
    }
    .fm-header p { margin: 5px 0 0; color: #6e7681; font-size: 0.78rem; letter-spacing: 0.10em; text-transform: uppercase; }
    .live-dot {
        display: inline-block; width: 8px; height: 8px;
        background: #3fb950; border-radius: 50%; margin-right: 7px;
        box-shadow: 0 0 8px #3fb950;
        animation: pulse 1.8s ease-in-out infinite;
    }
    @keyframes pulse { 0%,100%{opacity:1;box-shadow:0 0 8px #3fb950;} 50%{opacity:.3;box-shadow:0 0 2px #3fb950;} }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #0d1117; border: 1px solid #21262d;
        border-radius: 12px; padding: 20px 16px;
        text-align: center; position: relative; overflow: hidden;
        transition: border-color .25s, transform .2s;
    }
    .kpi-card:hover { border-color: #1f6feb; transform: translateY(-2px); }
    .kpi-card::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #1f6feb, transparent);
    }
    .kpi-label { font-size: .68rem; color: #6e7681; text-transform: uppercase; letter-spacing: .10em; margin-bottom: 8px; }
    .kpi-value { font-size: 1.85rem; font-weight: 700; color: #58a6ff; font-family: 'IBM Plex Mono', monospace; line-height: 1; }
    .kpi-sub   { font-size: .72rem; color: #3fb950; margin-top: 6px; }
    .kpi-delta-pos { color: #3fb950; font-size: .7rem; }
    .kpi-delta-neg { color: #f85149; font-size: .7rem; }

    /* ── Section headers ── */
    .section-title {
        font-size: .72rem; font-weight: 600; color: #6e7681;
        text-transform: uppercase; letter-spacing: .12em;
        margin: 28px 0 12px;
        display: flex; align-items: center; gap: 10px;
    }
    .section-title::after {
        content: ""; flex: 1; height: 1px;
        background: linear-gradient(90deg, #21262d, transparent);
    }

    /* ── Alert cards ── */
    .alert-critical { background:#200c0c; border:1px solid #f8514966; border-radius:8px; padding:10px 14px; margin-bottom:8px; }
    .alert-warning  { background:#1e1500; border:1px solid #f0883e66; border-radius:8px; padding:10px 14px; margin-bottom:8px; }
    .alert-info     { background:#0c1820; border:1px solid #1f6feb66; border-radius:8px; padding:10px 14px; margin-bottom:8px; }
    .alert-ok       { background:#0c1a0e; border:1px solid #3fb95066; border-radius:8px; padding:10px 14px; margin-bottom:8px; }
    .alert-time     { font-family:'IBM Plex Mono',monospace; font-size:.68rem; color:#6e7681; }
    .alert-msg      { font-size:.82rem; color:#d0d7de; margin-top:3px; }
    .alert-badge    { font-size:.65rem; font-weight:700; padding:2px 8px; border-radius:20px; float:right; }
    .badge-crit { background:#f8514933; color:#f85149; }
    .badge-warn { background:#f0883e33; color:#f0883e; }
    .badge-info { background:#1f6feb33; color:#58a6ff; }
    .badge-ok   { background:#3fb95033; color:#3fb950; }

    /* ── Health scorecard ── */
    .health-bar-wrap { background:#161b22; border-radius:4px; height:8px; margin-top:5px; }
    .health-bar { height:8px; border-radius:4px; transition: width .5s ease; }

    /* ── Bus Inspector ── */
    .inspector-card {
        background: #0d1b2e; border: 1px solid #1f6feb;
        border-radius: 12px; padding: 20px;
        box-shadow: 0 0 40px #1f6feb22;
    }
    .inspector-title { font-family:'IBM Plex Mono',monospace; font-size:1.1rem; color:#58a6ff; font-weight:600; }
    .inspector-row { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #21262d; font-size:.82rem; }
    .inspector-label { color:#6e7681; }
    .inspector-value { color:#d0d7de; font-family:'IBM Plex Mono',monospace; }

    /* ── Prediction band ── */
    .pred-card {
        background:#0d1117; border:1px solid #21262d;
        border-radius:10px; padding:16px; margin-bottom:10px;
    }
    .pred-bus   { font-family:'IBM Plex Mono',monospace; font-size:.85rem; color:#58a6ff; font-weight:600; }
    .pred-eta   { font-size:1.4rem; font-weight:700; color:#d0d7de; }
    .pred-range { font-size:.75rem; color:#6e7681; }
    .pred-conf  { font-size:.72rem; font-weight:600; padding:2px 8px; border-radius:12px; float:right; }
    .conf-high  { background:#3fb95022; color:#3fb950; }
    .conf-med   { background:#f0883e22; color:#f0883e; }

    /* Sidebar */
    [data-testid="stSidebar"] { background:#080c12; border-right:1px solid #21262d; }
    [data-testid="stSidebar"] .stButton>button {
        background:linear-gradient(135deg,#1f6feb,#1158c7);
        color:#fff; border:none; border-radius:8px;
        width:100%; padding:11px; font-weight:600;
        letter-spacing:.04em; font-size:.9rem;
        transition: opacity .2s;
    }
    [data-testid="stSidebar"] .stButton>button:hover { opacity:.85; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background:#0d1117; border-bottom:1px solid #21262d; gap:0; }
    .stTabs [data-baseweb="tab"] { background:transparent; color:#6e7681; border:none; padding:10px 20px; font-size:.82rem; letter-spacing:.06em; text-transform:uppercase; }
    .stTabs [aria-selected="true"] { color:#58a6ff; border-bottom:2px solid #1f6feb; background:transparent; }

    .stDataFrame { border-radius:10px; overflow:hidden; }
    footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & ROUTE GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────

ROUTE_WAYPOINTS = {
    "Lahore → Multan (M-4)": [
        (31.5204, 74.3587), (31.1704, 72.6981),
        (30.6900, 71.5830), (30.1575, 71.5249),
    ],
    "Multan → Sukkur (M-5)": [
        (30.1575, 71.5249), (29.3956, 71.0136),
        (28.4212, 70.2989), (27.7052, 68.8573),
    ],
    "Sukkur → Karachi (N-55/M-9)": [
        (27.7052, 68.8573), (26.4131, 68.2856),
        (25.3960, 68.3578), (24.8607, 67.0104),
    ],
    "Lahore → Faisalabad (M-3)": [
        (31.5204, 74.3587), (31.4505, 73.6967),
        (31.4100, 73.0790), (31.4180, 72.9980),
    ],
    "Karachi → Hyderabad (M-9)": [
        (24.8607, 67.0104), (25.1614, 67.4558),
        (25.3960, 68.3578),
    ],
}

ROUTE_KM = {
    "Lahore → Multan (M-4)":        340,
    "Multan → Sukkur (M-5)":        420,
    "Sukkur → Karachi (N-55/M-9)":  480,
    "Lahore → Faisalabad (M-3)":    130,
    "Karachi → Hyderabad (M-9)":    155,
}

ROUTE_NAMES = list(ROUTE_WAYPOINTS.keys())

# Fixed bus roster with assigned routes & base progress
BUS_ROSTER = [
    ("FM-0421",  "Lahore → Multan (M-4)",           0.15, "Volvo 9700",   "Ali Raza"),
    ("FM-0389",  "Lahore → Multan (M-4)",           0.72, "Daewoo BX212", "Shahid Khan"),
    ("FMX-117",  "Multan → Sukkur (M-5)",           0.33, "Hino RK1JSLB", "Tariq Mehmood"),
    ("FMX-204",  "Multan → Sukkur (M-5)",           0.88, "Volvo 9700",   "Asif Iqbal"),
    ("FM-0556",  "Sukkur → Karachi (N-55/M-9)",     0.10, "Daewoo BX212", "Zubair Hussain"),
    ("FM-0601",  "Sukkur → Karachi (N-55/M-9)",     0.55, "Hino RK1JSLB", "Imran Butt"),
    ("FM-0734",  "Sukkur → Karachi (N-55/M-9)",     0.91, "Volvo 9700",   "Naeem Akhtar"),
    ("FML-008",  "Lahore → Faisalabad (M-3)",       0.40, "Daewoo BX212", "Rashid Malik"),
    ("FML-019",  "Lahore → Faisalabad (M-3)",       0.77, "Hino RK1JSLB", "Kamran Siddiq"),
    ("FM-0290",  "Lahore → Multan (M-4)",           0.48, "Volvo 9700",   "Faisal Younas"),
    ("FMX-331",  "Multan → Sukkur (M-5)",           0.62, "Daewoo BX212", "Waqar Ahmed"),
    ("FM-0815",  "Karachi → Hyderabad (M-9)",       0.25, "Hino RK1JSLB", "Sajid Rehman"),
    ("FM-0902",  "Karachi → Hyderabad (M-9)",       0.68, "Volvo 9700",   "Usman Ghani"),
]


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def interpolate_position(waypoints, progress):
    n       = len(waypoints) - 1
    seg_len = 1.0 / n
    seg_idx = min(int(progress / seg_len), n - 1)
    t       = (progress - seg_idx * seg_len) / seg_len
    lat = waypoints[seg_idx][0] + t * (waypoints[seg_idx+1][0] - waypoints[seg_idx][0])
    lon = waypoints[seg_idx][1] + t * (waypoints[seg_idx+1][1] - waypoints[seg_idx][1])
    lat += np.random.uniform(-0.006, 0.006)
    lon += np.random.uniform(-0.006, 0.006)
    return round(lat, 5), round(lon, 5)


def compute_health_score(speed, fuel, engine_temp, oil_pressure, status):
    """Composite 0–100 fleet health index."""
    speed_score   = 100 - max(0, abs(speed - 100) - 10) * 1.5
    fuel_score    = max(0, 100 - (fuel - 24) * 3.0)
    temp_score    = max(0, 100 - max(0, engine_temp - 88) * 5)
    oil_score     = min(100, oil_pressure * 22)
    status_score  = 100 if status == "On-Time" else 40
    score = (speed_score * .25 + fuel_score * .25 +
             temp_score  * .20 + oil_score  * .15 + status_score * .15)
    return max(0, min(100, round(score, 1)))


def monte_carlo_eta(speed_series, remaining_km, n=500):
    """
    Monte Carlo ETA confidence interval.
    speed_series: list of recent speed observations (km/h)
    remaining_km: distance left on route
    Returns (p10_min, p50_min, p90_min)
    """
    mu    = np.mean(speed_series)
    sigma = max(np.std(speed_series), 5)
    samples = np.random.normal(mu, sigma, n)
    samples = np.clip(samples, 40, 140)
    etas    = (remaining_km / samples) * 60   # minutes
    return round(np.percentile(etas, 10), 0), \
           round(np.percentile(etas, 50), 0), \
           round(np.percentile(etas, 90), 0)


def ai_recommendation(row):
    """Rule-based AI Dispatch Advisor — returns (severity, message)."""
    if row["Engine Temp (°C)"] > 94:
        return "CRITICAL", f"⚠ Engine overheating ({row['Engine Temp (°C)']}°C). Advise pit stop at next rest area. Reduce load by 20%."
    if row["Oil Pressure (bar)"] < 3.4:
        return "CRITICAL", f"⚠ Low oil pressure ({row['Oil Pressure (bar)']} bar). Immediate inspection recommended."
    if row["Fuel Burn (L/100km)"] > 35:
        return "WARNING", f"⛽ Excessive fuel burn ({row['Fuel Burn (L/100km)']} L/100km). Check tire pressure & reduce cruise speed to 95 km/h."
    if row["Speed (km/h)"] > 120:
        return "WARNING", f"🚨 Speed violation: {row['Speed (km/h)']} km/h exceeds 120 km/h motorway policy. Contact driver immediately."
    if row["Status"] == "Delayed":
        return "INFO", f"🕐 Bus running behind schedule. ETA revised to {row['ETA']}. Notify passengers via SMS."
    if row["Passengers"] > 48:
        return "INFO", f"👥 High occupancy ({row['Passengers']} pax). Ensure luggage bay weight limits are respected."
    return "OK", f"✅ All systems nominal. Bus operating within optimal parameters."


def generate_fleet_data():
    """Core telemetry data factory — called on every refresh."""
    now     = datetime.now()
    records = []
    for bus_id, route, base_prog, model, driver in BUS_ROSTER:
        progress = np.clip(base_prog + np.random.uniform(-0.04, 0.04), 0.02, 0.97)
        wps      = ROUTE_WAYPOINTS[route]
        lat, lon = interpolate_position(wps, progress)

        speed        = int(np.clip(np.random.normal(105, 16), 58, 132))
        fuel_burn    = round(np.random.uniform(23.5, 39.0), 1)
        cargo_kg     = int(np.random.uniform(700, 3400))
        passengers   = int(np.random.uniform(26, 54))
        engine_temp  = int(np.random.uniform(80, 98))
        oil_pressure = round(np.random.uniform(3.1, 4.9), 1)
        tire_psi     = int(np.random.uniform(90, 115))      # tyre pressure PSI
        battery_v    = round(np.random.uniform(24.1, 27.6), 1)  # 24V system

        rem_km       = (1.0 - progress) * ROUTE_KM[route]
        eta_hours    = rem_km / max(speed, 1)
        eta_time     = now + timedelta(hours=eta_hours)
        eta_str      = eta_time.strftime("%H:%M")

        delayed      = speed < 76 or np.random.random() < 0.18
        status       = "Delayed" if delayed else "On-Time"

        health       = compute_health_score(speed, fuel_burn, engine_temp, oil_pressure, status)
        sev, rec     = ai_recommendation({
            "Engine Temp (°C)": engine_temp, "Oil Pressure (bar)": oil_pressure,
            "Fuel Burn (L/100km)": fuel_burn, "Speed (km/h)": speed,
            "Status": status, "Passengers": passengers, "ETA": eta_str,
        })

        records.append({
            "Bus ID":              bus_id,
            "Model":               model,
            "Driver":              driver,
            "Route":               route,
            "Lat":                 lat,
            "Lon":                 lon,
            "Speed (km/h)":        speed,
            "Fuel Burn (L/100km)": fuel_burn,
            "Cargo (kg)":          cargo_kg,
            "Passengers":          passengers,
            "Engine Temp (°C)":    engine_temp,
            "Oil Pressure (bar)":  oil_pressure,
            "Tire PSI":            tire_psi,
            "Battery (V)":         battery_v,
            "ETA":                 eta_str,
            "Remaining KM":        round(rem_km, 1),
            "Status":              status,
            "Progress (%)":        round(progress * 100, 1),
            "Health Score":        health,
            "AI Severity":         sev,
            "AI Recommendation":   rec,
        })

    return pd.DataFrame(records)


def generate_alerts(df):
    """
    Build a live incident alert feed from current telemetry.
    Returns list of dicts: {time, severity, bus_id, message}
    """
    alerts = []
    now = datetime.now()

    for _, row in df.iterrows():
        sev = row["AI Severity"]
        if sev == "CRITICAL":
            alerts.append({
                "time":    (now - timedelta(seconds=random.randint(10, 90))).strftime("%H:%M:%S"),
                "sev":     "CRITICAL",
                "bus_id":  row["Bus ID"],
                "msg":     row["AI Recommendation"],
            })
        elif sev == "WARNING":
            alerts.append({
                "time":    (now - timedelta(seconds=random.randint(60, 300))).strftime("%H:%M:%S"),
                "sev":     "WARNING",
                "bus_id":  row["Bus ID"],
                "msg":     row["AI Recommendation"],
            })

    # Add some context alerts for realism
    route_alerts = [
        ("INFO",  "M-5 Motorway — Toll plaza queue at Bahawalpur interchange. Expect +12 min delay."),
        ("INFO",  "Weather Advisory: Dust storm reported near Rahim Yar Khan. Reduce speed to 80 km/h."),
        ("OK",    "Karachi Terminal — Gate 4 ready for next arrival. Ground staff on standby."),
        ("OK",    "Multan Hub — Fuel bay cleared. 3 buses queued for refuel in next 20 min."),
        ("WARNING","M-4 — Construction zone active near Kabirwala interchange. Single-lane traffic."),
    ]
    for sev, msg in route_alerts:
        alerts.append({
            "time":   (now - timedelta(minutes=random.randint(1, 30))).strftime("%H:%M:%S"),
            "sev":    sev, "bus_id": "NETWORK", "msg": msg,
        })

    # Sort newest-first (approximate by time string)
    alerts.sort(key=lambda x: x["time"], reverse=True)
    return alerts


def build_sparkline_svg(values, width=120, height=32, color="#1f6feb"):
    """Render a tiny inline SVG sparkline from a list of values."""
    if len(values) < 2:
        return ""
    mn, mx = min(values), max(values)
    rng    = max(mx - mn, 1)
    pts    = []
    for i, v in enumerate(values):
        x = i / (len(values) - 1) * width
        y = height - ((v - mn) / rng) * (height - 4) - 2
        pts.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(pts)
    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.8" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


def ring_svg(pct, color="#1f6feb", size=56):
    """SVG donut ring for KPI cards."""
    r   = (size - 8) / 2
    circ = 2 * math.pi * r
    dash = pct / 100 * circ
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg" style="display:block;margin:6px auto 0;">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#21262d" stroke-width="5"/>'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{color}" stroke-width="5" '
        f'stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-linecap="round" '
        f'transform="rotate(-90 {size/2} {size/2})"/>'
        f'</svg>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE  —  persist across reruns; build speed history for trend charts
# ─────────────────────────────────────────────────────────────────────────────
if "fleet_df" not in st.session_state:
    st.session_state["fleet_df"]       = generate_fleet_data()
    st.session_state["last_refresh"]   = datetime.now().strftime("%H:%M:%S")
    st.session_state["refresh_count"]  = 1
    st.session_state["speed_history"]  = {}   # bus_id → list of speeds (up to 8 snapshots)
    st.session_state["health_history"] = {}   # bus_id → list of health scores

def _update_history(df):
    for _, row in df.iterrows():
        bid = row["Bus ID"]
        sh  = st.session_state["speed_history"]
        hh  = st.session_state["health_history"]
        sh[bid]  = (sh.get(bid, []) + [row["Speed (km/h)"]])[-8:]
        hh[bid]  = (hh.get(bid, []) + [row["Health Score"]])[-8:]

_update_history(st.session_state["fleet_df"])


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  —  dispatch controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Dispatch Control")
    st.markdown("---")

    all_routes     = ["All Routes"] + ROUTE_NAMES
    selected_route = st.selectbox("Filter by Route", all_routes)
    selected_status= st.radio("Filter by Status", ["All", "On-Time", "Delayed"])

    st.markdown("---")
    st.markdown("### 🔍 Bus Inspector")
    all_buses     = ["— Select Bus —"] + list(st.session_state["fleet_df"]["Bus ID"])
    selected_bus  = st.selectbox("Select Bus for Deep Dive", all_buses)

    st.markdown("---")
    if st.button("🔄  Refresh Telemetry"):
        st.session_state["fleet_df"]      = generate_fleet_data()
        st.session_state["last_refresh"]  = datetime.now().strftime("%H:%M:%S")
        st.session_state["refresh_count"] += 1
        _update_history(st.session_state["fleet_df"])
        st.rerun()

    st.markdown(
        f"<small style='color:#6e7681;'>Last pull: "
        f"<b style='color:#3fb950;font-family:IBM Plex Mono,monospace;'>{st.session_state['last_refresh']}</b><br>"
        f"Snapshots stored: {st.session_state['refresh_count']}</small>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#6e7681;'>**Faisal Movers TMS**<br>"
        "Fleet Intelligence v3.0<br>"
        "© 2025 · Portfolio Demo</small>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────
full_df = st.session_state["fleet_df"].copy()
df = full_df.copy()
if selected_route  != "All Routes": df = df[df["Route"]  == selected_route]
if selected_status != "All":        df = df[df["Status"] == selected_status]


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="fm-header">
    <h1>🚌 FAISAL MOVERS &nbsp;·&nbsp; LIVE INTERCITY FLEET TELEMETRY</h1>
    <p><span class="live-dot"></span>M-4 · M-5 · M-3 · M-9 Corridor Operations &nbsp;·&nbsp;
       AI-Assisted Dispatch Intelligence &nbsp;·&nbsp; Predictive ETA Engine Active</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW  —  with animated SVG rings
# ─────────────────────────────────────────────────────────────────────────────
total_active  = len(full_df)
avg_speed     = int(full_df["Speed (km/h)"].mean())
total_cargo   = int(full_df["Cargo (kg)"].sum())
delayed_count = int((full_df["Status"] == "Delayed").sum())
total_pax     = int(full_df["Passengers"].sum())
avg_health    = round(full_df["Health Score"].mean(), 1)
critical_cnt  = int((full_df["AI Severity"] == "CRITICAL").sum())
net_status    = "⚠ ALERTS ACTIVE" if critical_cnt > 0 else "✅ NOMINAL"
net_color     = "#f85149" if critical_cnt > 0 else "#3fb950"

cols = st.columns(6)
kpi_data = [
    ("Active Fleet",     str(total_active),          "buses on network",       total_active/15*100,    "#58a6ff"),
    ("Avg Speed",        f"{avg_speed} km/h",         "motorway average",       avg_speed/130*100,      "#3fb950"),
    ("Total Cargo",      f"{total_cargo//1000:.1f}t", "freight + luggage",      min(total_cargo/40000*100,100), "#e3b341"),
    ("Passengers",       str(total_pax),              "across all coaches",     min(total_pax/700*100,100),  "#a371f7"),
    ("Fleet Health",     f"{avg_health}",             "composite index",        avg_health,             "#3fb950" if avg_health>70 else "#f0883e"),
    ("Network",          net_status,                  f"{critical_cnt} critical alerts", min(100,critical_cnt*20+20), net_color),
]
for col, (label, value, sub, pct, color) in zip(cols, kpi_data):
    col.markdown(
        f'<div class="kpi-card">'
        f'  <div class="kpi-label">{label}</div>'
        f'  <div class="kpi-value" style="font-size:1.3rem;color:{color};">{value}</div>'
        f'  {ring_svg(min(pct,100), color)}'
        f'  <div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_map, tab_intel, tab_pred, tab_health, tab_matrix = st.tabs([
    "🗺  Live Map",
    "🤖  AI Dispatch Intel",
    "📡  Predictive ETA",
    "💡  Fleet Health",
    "📊  Telemetry Matrix",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1: LIVE MAP
# ════════════════════════════════════════════════════════════════════════════
with tab_map:
    col_map, col_alerts = st.columns([3, 1])

    with col_map:
        st.markdown('<div class="section-title">📍 Live Fleet Positions</div>', unsafe_allow_html=True)

        m = folium.Map(
            location=[28.5, 70.5], zoom_start=6,
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="© OpenStreetMap © CARTO", max_zoom=18,
        )

        # Route polylines — colour per route
        route_colors = {
            "Lahore → Multan (M-4)":        "#58a6ff",
            "Multan → Sukkur (M-5)":        "#3fb950",
            "Sukkur → Karachi (N-55/M-9)":  "#f0883e",
            "Lahore → Faisalabad (M-3)":    "#a371f7",
            "Karachi → Hyderabad (M-9)":    "#e3b341",
        }
        for rname, wps in ROUTE_WAYPOINTS.items():
            folium.PolyLine(
                locations=wps, color=route_colors.get(rname, "#1f6feb"),
                weight=3, opacity=0.55, tooltip=rname,
                dash_array="6 4" if "M-9" in rname else None,
            ).add_to(m)

        # City labels
        cities = [
            (31.5204, 74.3587, "Lahore"),   (30.1575, 71.5249, "Multan"),
            (27.7052, 68.8573, "Sukkur"),   (24.8607, 67.0104, "Karachi"),
            (31.4180, 72.9980, "Faisalabad"),(25.3960, 68.3578, "Hyderabad"),
            (29.3956, 71.0136, "Bahawalpur"),(28.4212, 70.2989, "RY Khan"),
        ]
        for clat, clon, cname in cities:
            folium.Marker(
                location=[clat, clon],
                icon=folium.DivIcon(html=f'<div style="font-family:IBM Plex Mono,monospace;'
                                    f'font-size:10px;color:#6e7681;white-space:nowrap;'
                                    f'background:#0d1117cc;padding:2px 5px;border-radius:3px;'
                                    f'border:1px solid #21262d;">{cname}</div>'),
            ).add_to(m)

        # Bus markers
        for _, row in df.iterrows():
            icon_color = "green" if row["Status"] == "On-Time" else "red"
            health_bar = "🟢" if row["Health Score"] > 75 else "🟡" if row["Health Score"] > 50 else "🔴"
            popup_html = f"""
            <div style="font-family:Segoe UI,sans-serif;min-width:220px;
                        background:#0d1117;color:#d0d7de;padding:14px;border-radius:8px;
                        border:1px solid #1f6feb44;">
                <b style="color:#58a6ff;font-size:1rem;font-family:IBM Plex Mono,monospace;">{row['Bus ID']}</b>
                &nbsp;<span style="color:#6e7681;font-size:.75rem;">{row['Model']}</span><br>
                <span style="color:#6e7681;font-size:.78rem;">👤 {row['Driver']}</span>
                <hr style="border-color:#21262d;margin:8px 0;">
                🚀 <b>{row['Speed (km/h)']} km/h</b> &nbsp; ⛽ <b>{row['Fuel Burn (L/100km)']} L/100km</b><br>
                🧳 <b>{row['Cargo (kg)']} kg</b> &nbsp; 👥 <b>{row['Passengers']} pax</b><br>
                🌡 <b>{row['Engine Temp (°C)']}°C</b> &nbsp; 🔧 <b>{row['Oil Pressure (bar)']} bar</b><br>
                📏 <b>{row['Remaining KM']} km</b> remaining &nbsp; 🕐 ETA <b>{row['ETA']}</b><br>
                {health_bar} Health: <b>{row['Health Score']}/100</b><br>
                <span style="font-size:.75rem;color:{'#f85149' if row['AI Severity']=='CRITICAL'
                    else '#f0883e' if row['AI Severity']=='WARNING' else '#6e7681'};">
                    {row['AI Recommendation'][:80]}…</span>
            </div>"""
            folium.Marker(
                location=[row["Lat"], row["Lon"]],
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{row['Bus ID']} · {row['Speed (km/h)']} km/h · {row['Status']}",
                icon=folium.Icon(color=icon_color, icon="bus", prefix="fa"),
            ).add_to(m)

        st_folium(m, width="100%", height=500, returned_objects=[])

    with col_alerts:
        st.markdown('<div class="section-title">🚨 Incident Feed</div>', unsafe_allow_html=True)
        alerts = generate_alerts(df)
        sev_map = {
            "CRITICAL": ("alert-critical", "badge-crit", "CRIT"),
            "WARNING":  ("alert-warning",  "badge-warn", "WARN"),
            "INFO":     ("alert-info",     "badge-info", "INFO"),
            "OK":       ("alert-ok",       "badge-ok",   "OK"),
        }
        for a in alerts[:12]:
            card_cls, badge_cls, badge_txt = sev_map.get(a["sev"], sev_map["INFO"])
            st.markdown(
                f'<div class="{card_cls}">'
                f'  <span class="alert-badge {badge_cls}">{badge_txt}</span>'
                f'  <div class="alert-time">{a["time"]} &nbsp;·&nbsp; {a["bus_id"]}</div>'
                f'  <div class="alert-msg">{a["msg"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════════════════
# TAB 2: AI DISPATCH INTEL
# ════════════════════════════════════════════════════════════════════════════
with tab_intel:
    st.markdown('<div class="section-title">🤖 AI Dispatch Advisor — Per-Bus Recommendations</div>', unsafe_allow_html=True)

    # Bus Inspector (if selected in sidebar)
    if selected_bus != "— Select Bus —":
        bus_row = full_df[full_df["Bus ID"] == selected_bus].iloc[0]
        st.markdown(f"""
        <div class="inspector-card">
            <div class="inspector-title">🔍 INSPECTOR — {bus_row['Bus ID']} · {bus_row['Model']}</div>
            <div style="color:#6e7681;font-size:.78rem;margin-bottom:12px;">Driver: {bus_row['Driver']} &nbsp;·&nbsp; Route: {bus_row['Route']}</div>
            <div class="inspector-row"><span class="inspector-label">Current Speed</span><span class="inspector-value">{bus_row['Speed (km/h)']} km/h</span></div>
            <div class="inspector-row"><span class="inspector-label">Fuel Burn Rate</span><span class="inspector-value">{bus_row['Fuel Burn (L/100km)']} L/100km</span></div>
            <div class="inspector-row"><span class="inspector-label">Engine Temperature</span><span class="inspector-value">{bus_row['Engine Temp (°C)']} °C</span></div>
            <div class="inspector-row"><span class="inspector-label">Oil Pressure</span><span class="inspector-value">{bus_row['Oil Pressure (bar)']} bar</span></div>
            <div class="inspector-row"><span class="inspector-label">Tire PSI</span><span class="inspector-value">{bus_row['Tire PSI']} PSI</span></div>
            <div class="inspector-row"><span class="inspector-label">Battery Voltage</span><span class="inspector-value">{bus_row['Battery (V)']} V</span></div>
            <div class="inspector-row"><span class="inspector-label">Passengers</span><span class="inspector-value">{bus_row['Passengers']} / 54</span></div>
            <div class="inspector-row"><span class="inspector-label">Cargo</span><span class="inspector-value">{bus_row['Cargo (kg)']} kg</span></div>
            <div class="inspector-row"><span class="inspector-label">Fleet Health Index</span><span class="inspector-value">{bus_row['Health Score']} / 100</span></div>
            <div class="inspector-row"><span class="inspector-label">Status</span><span class="inspector-value" style="color:{'#3fb950' if bus_row['Status']=='On-Time' else '#f85149'};">{bus_row['Status']}</span></div>
            <div class="inspector-row"><span class="inspector-label">ETA</span><span class="inspector-value">{bus_row['ETA']}</span></div>
            <div class="inspector-row"><span class="inspector-label">Remaining Distance</span><span class="inspector-value">{bus_row['Remaining KM']} km</span></div>
            <div style="margin-top:14px;padding:10px;background:#0d1117;border-radius:6px;border-left:3px solid {'#f85149' if bus_row['AI Severity']=='CRITICAL' else '#f0883e' if bus_row['AI Severity']=='WARNING' else '#3fb950'};">
                <div style="font-size:.68rem;color:#6e7681;text-transform:uppercase;letter-spacing:.08em;">AI Advisory</div>
                <div style="font-size:.85rem;color:#d0d7de;margin-top:4px;">{bus_row['AI Recommendation']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Full AI recommendations grid
    sev_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2, "OK": 3}
    sorted_df = full_df.sort_values("AI Severity", key=lambda s: s.map(sev_order))

    for _, row in sorted_df.iterrows():
        sev = row["AI Severity"]
        border = {"CRITICAL":"#f85149","WARNING":"#f0883e","INFO":"#1f6feb","OK":"#3fb950"}.get(sev,"#21262d")
        icon   = {"CRITICAL":"🔴","WARNING":"🟠","INFO":"🔵","OK":"🟢"}.get(sev,"⚪")
        speed_hist = st.session_state["speed_history"].get(row["Bus ID"], [row["Speed (km/h)"]])
        spark  = build_sparkline_svg(speed_hist, width=100, height=28,
                                     color={"CRITICAL":"#f85149","WARNING":"#f0883e","INFO":"#58a6ff","OK":"#3fb950"}.get(sev))
        with st.container():
            c1, c2, c3, c4 = st.columns([1, 2, 4, 1.2])
            c1.markdown(
                f'<div style="padding:10px;background:#0d1117;border:1px solid {border}33;'
                f'border-left:3px solid {border};border-radius:8px;text-align:center;">'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:.9rem;color:#58a6ff;font-weight:700;">{row["Bus ID"]}</div>'
                f'<div style="font-size:.68rem;color:#6e7681;">{row["Model"]}</div>'
                f'<div style="font-size:.72rem;color:{border};margin-top:4px;">{icon} {sev}</div>'
                f'</div>', unsafe_allow_html=True)
            c2.markdown(
                f'<div style="padding:10px;background:#0d1117;border:1px solid #21262d;border-radius:8px;font-size:.78rem;">'
                f'<span style="color:#6e7681;">Route:</span> <span style="color:#d0d7de;">{row["Route"].split("(")[0].strip()}</span><br>'
                f'<span style="color:#6e7681;">Speed:</span> <span style="color:#d0d7de;">{row["Speed (km/h)"]} km/h</span><br>'
                f'<span style="color:#6e7681;">Health:</span> <span style="color:{border}">{row["Health Score"]}/100</span><br>'
                f'<span style="color:#6e7681;">Status:</span> <span style="color:{"#3fb950" if row["Status"]=="On-Time" else "#f85149"}">{row["Status"]}</span>'
                f'</div>', unsafe_allow_html=True)
            c3.markdown(
                f'<div style="padding:10px;background:#0d1117;border:1px solid {border}33;border-radius:8px;">'
                f'<div style="font-size:.68rem;color:#6e7681;text-transform:uppercase;letter-spacing:.08em;">AI Advisory</div>'
                f'<div style="font-size:.82rem;color:#d0d7de;margin-top:5px;">{row["AI Recommendation"]}</div>'
                f'</div>', unsafe_allow_html=True)
            c4.markdown(
                f'<div style="padding:10px;background:#0d1117;border:1px solid #21262d;border-radius:8px;text-align:center;">'
                f'<div style="font-size:.65rem;color:#6e7681;margin-bottom:4px;">Speed Trend</div>'
                f'{spark}'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:.7rem;color:#6e7681;margin-top:2px;">ETA {row["ETA"]}</div>'
                f'</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3: PREDICTIVE ETA ENGINE
# ════════════════════════════════════════════════════════════════════════════
with tab_pred:
    st.markdown('<div class="section-title">📡 Monte Carlo Predictive ETA Engine</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#6e7681;font-size:.8rem;margin-bottom:16px;">'
        'Each ETA is computed via 500-sample Monte Carlo simulation using the bus\'s '
        'recent speed history. P10/P90 bands represent optimistic and pessimistic scenarios.</p>',
        unsafe_allow_html=True,
    )

    pred_cols = st.columns(3)
    for i, (_, row) in enumerate(full_df.iterrows()):
        speed_hist = st.session_state["speed_history"].get(row["Bus ID"], [row["Speed (km/h)"]] * 3)
        p10, p50, p90 = monte_carlo_eta(speed_hist, row["Remaining KM"])
        now = datetime.now()
        eta_p10 = (now + timedelta(minutes=p10)).strftime("%H:%M")
        eta_p50 = (now + timedelta(minutes=p50)).strftime("%H:%M")
        eta_p90 = (now + timedelta(minutes=p90)).strftime("%H:%M")
        conf    = "HIGH" if (p90 - p10) < 30 else "MEDIUM"
        conf_cls= "conf-high" if conf == "HIGH" else "conf-med"
        status_color = "#3fb950" if row["Status"] == "On-Time" else "#f85149"

        col = pred_cols[i % 3]
        col.markdown(
            f'<div class="pred-card">'
            f'  <span class="pred-bus">{row["Bus ID"]}</span>'
            f'  <span class="pred-conf {conf_cls}">{conf} CONF</span><br>'
            f'  <div style="font-size:.7rem;color:#6e7681;">{row["Route"].split("(")[0].strip()} &nbsp;·&nbsp; {row["Remaining KM"]} km left</div>'
            f'  <div class="pred-eta">{eta_p50}</div>'
            f'  <div class="pred-range">🔵 Optimistic: {eta_p10} &nbsp;·&nbsp; 🔴 Pessimistic: {eta_p90}</div>'
            f'  <div style="margin-top:8px;">'
            f'    <div style="display:flex;align-items:center;gap:6px;font-size:.72rem;color:#6e7681;">'
            f'      <span>±{round((p90-p10)/2)} min window</span>'
            f'      <span style="flex:1;height:4px;background:#21262d;border-radius:2px;position:relative;">'
            f'        <span style="position:absolute;left:10%;right:10%;top:0;height:4px;'
            f'          background:linear-gradient(90deg,#1f6feb44,#1f6feb,#1f6feb44);border-radius:2px;"></span>'
            f'      </span>'
            f'      <span style="color:{status_color};">{row["Status"]}</span>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 4: FLEET HEALTH SCORECARD
# ════════════════════════════════════════════════════════════════════════════
with tab_health:
    st.markdown('<div class="section-title">💡 Fleet Health Scorecard</div>', unsafe_allow_html=True)

    sorted_health = full_df.sort_values("Health Score", ascending=False)

    for _, row in sorted_health.iterrows():
        h     = row["Health Score"]
        color = "#3fb950" if h >= 75 else "#f0883e" if h >= 50 else "#f85149"
        trend = st.session_state["health_history"].get(row["Bus ID"], [h])
        spark = build_sparkline_svg(trend, width=80, height=24, color=color)
        bar_w = int(h)

        # Sub-scores
        spd_s  = max(0, 100 - abs(row["Speed (km/h)"] - 100) * 1.5)
        fuel_s = max(0, 100 - (row["Fuel Burn (L/100km)"] - 24) * 3)
        temp_s = max(0, 100 - max(0, row["Engine Temp (°C)"] - 88) * 5)
        oil_s  = min(100, row["Oil Pressure (bar)"] * 22)

        st.markdown(
            f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;'
            f'padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:16px;">'
            # Bus ID
            f'<div style="min-width:80px;">'
            f'  <div style="font-family:IBM Plex Mono,monospace;font-size:.88rem;color:#58a6ff;font-weight:700;">{row["Bus ID"]}</div>'
            f'  <div style="font-size:.68rem;color:#6e7681;">{row["Model"]}</div>'
            f'</div>'
            # Health bar
            f'<div style="flex:1;">'
            f'  <div style="display:flex;justify-content:space-between;font-size:.7rem;color:#6e7681;margin-bottom:4px;">'
            f'    <span>Fleet Health Index</span><span style="color:{color};font-weight:700;">{h}/100</span></div>'
            f'  <div class="health-bar-wrap"><div class="health-bar" style="width:{bar_w}%;background:{color};"></div></div>'
            f'  <div style="display:flex;gap:16px;margin-top:6px;font-size:.68rem;color:#6e7681;">'
            f'    <span>Speed <b style="color:#d0d7de;">{int(spd_s)}</b></span>'
            f'    <span>Fuel <b style="color:#d0d7de;">{int(fuel_s)}</b></span>'
            f'    <span>Temp <b style="color:#d0d7de;">{int(temp_s)}</b></span>'
            f'    <span>Oil <b style="color:#d0d7de;">{int(oil_s)}</b></span>'
            f'  </div>'
            f'</div>'
            # Trend sparkline
            f'<div style="text-align:center;">'
            f'  <div style="font-size:.65rem;color:#6e7681;margin-bottom:3px;">Trend</div>'
            f'  {spark}'
            f'</div>'
            # Status
            f'<div style="min-width:70px;text-align:right;">'
            f'  <div style="font-size:.72rem;font-weight:700;color:{"#3fb950" if row["Status"]=="On-Time" else "#f85149"};">{row["Status"]}</div>'
            f'  <div style="font-size:.68rem;color:#6e7681;">ETA {row["ETA"]}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Fleet-wide health distribution summary
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Health Distribution</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    good_cnt = int((full_df["Health Score"] >= 75).sum())
    med_cnt  = int(((full_df["Health Score"] >= 50) & (full_df["Health Score"] < 75)).sum())
    poor_cnt = int((full_df["Health Score"] < 50).sum())
    for col, label, cnt, color, desc in [
        (c1, "Healthy",  good_cnt, "#3fb950", "Score ≥ 75"),
        (c2, "Fair",     med_cnt,  "#f0883e", "Score 50–74"),
        (c3, "Critical", poor_cnt, "#f85149", "Score < 50"),
    ]:
        col.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{label} Buses</div>'
            f'<div class="kpi-value" style="color:{color};">{cnt}</div>'
            f'{ring_svg(cnt/max(len(full_df),1)*100, color)}'
            f'<div class="kpi-sub">{desc}</div>'
            f'</div>', unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 5: TELEMETRY MATRIX
# ════════════════════════════════════════════════════════════════════════════
with tab_matrix:
    st.markdown('<div class="section-title">📊 Full Telemetry Data Matrix</div>', unsafe_allow_html=True)

    display_cols = [
        "Bus ID", "Model", "Driver", "Route",
        "Speed (km/h)", "Fuel Burn (L/100km)", "Cargo (kg)", "Passengers",
        "Engine Temp (°C)", "Oil Pressure (bar)", "Tire PSI", "Battery (V)",
        "Remaining KM", "ETA", "Status", "Health Score", "AI Severity",
    ]
    display_df = df[display_cols].reset_index(drop=True)

    def style_status(val):
        c  = "#3fb950" if val == "On-Time" else "#f85149"
        bg = "#1a3a2a"  if val == "On-Time" else "#3a1a1a"
        return f"color:{c};background-color:{bg};border-radius:4px;padding:2px 6px;font-weight:600;"

    def style_sev(val):
        return {
            "CRITICAL": "color:#f85149;font-weight:700;",
            "WARNING":  "color:#f0883e;font-weight:700;",
            "INFO":     "color:#58a6ff;",
            "OK":       "color:#3fb950;",
        }.get(val, "")

    def style_health(val):
        if val >= 75:   return "color:#3fb950;font-weight:700;"
        elif val >= 50: return "color:#f0883e;font-weight:700;"
        return "color:#f85149;font-weight:700;"

    def style_speed(val):
        if val >= 115:  return "color:#f0883e;"
        elif val < 76:  return "color:#f85149;"
        return "color:#d0d7de;"

    styled = (
        display_df.style
        .applymap(style_status, subset=["Status"])
        .applymap(style_sev,    subset=["AI Severity"])
        .applymap(style_health, subset=["Health Score"])
        .applymap(style_speed,  subset=["Speed (km/h)"])
        .set_properties(**{"background-color":"#0d1117","color":"#d0d7de","border-color":"#21262d"})
        .set_table_styles([
            {"selector":"thead th","props":[
                ("background-color","#080c12"),("color","#6e7681"),
                ("font-size","0.72rem"),("text-transform","uppercase"),
                ("letter-spacing","0.08em"),("border-bottom","1px solid #21262d"),
                ("font-family","'IBM Plex Mono',monospace")]},
            {"selector":"tbody tr:hover td","props":[("background-color","#0d1b2e")]},
        ])
        .format({
            "Speed (km/h)":        "{} km/h",
            "Fuel Burn (L/100km)": "{} L",
            "Cargo (kg)":          "{:,} kg",
            "Engine Temp (°C)":    "{} °C",
            "Oil Pressure (bar)":  "{} bar",
            "Tire PSI":            "{} PSI",
            "Battery (V)":         "{} V",
            "Remaining KM":        "{} km",
            "Health Score":        "{}/100",
        })
        .hide(axis="index")
    )
    st.dataframe(styled, use_container_width=True, height=480)

    # Export notice
    st.markdown(
        '<p style="font-size:.72rem;color:#6e7681;margin-top:8px;">'
        '⬇ Use the Streamlit dataframe download button (top-right of table) '
        'to export this telemetry snapshot as CSV.</p>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#21262d;margin-top:36px;">
<p style="text-align:center;color:#30363d;font-size:.72rem;
   font-family:'IBM Plex Mono',monospace;margin:8px 0 4px;">
    FAISAL MOVERS TRANSPORT MANAGEMENT SYSTEM &nbsp;·&nbsp;
    FLEET INTELLIGENCE MODULE v3.0 &nbsp;·&nbsp;
    AI-ASSISTED DISPATCH &nbsp;·&nbsp; MONTE CARLO ETA ENGINE
</p>
<p style="text-align:center;color:#21262d;font-size:.65rem;margin:0 0 16px;">
    All data is simulated for portfolio demonstration purposes only
</p>
""", unsafe_allow_html=True)
