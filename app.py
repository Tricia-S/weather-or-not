"""
Weather or Not — "Should I go out now, or wait?"
=================================================
Answers one question for any area in Singapore by combining three free,
key-less NEA real-time feeds into a single go / caution / stay-in verdict:

  • Rain  -> 2-hour weather forecast (will I get wet if I leave now?)
  • Heat  -> air temperature + humidity -> feels-like heat index
  • Haze  -> live 1-hour PM2.5 (the reading NEA recommends for *immediate*
             outdoor decisions), with 24-hour PSI shown as next-day context

Data: data.gov.sg (NEA / Meteorological Service Singapore). No API key needed.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

BASE = "https://api.data.gov.sg/v1/environment"

st.set_page_config(page_title="Weather or Not", page_icon="🌤️",
                   layout="wide", initial_sidebar_state="expanded")

# --------------------------------------------------------------------------- #
# 1. API LAYER (cached; TTLs match how often NEA refreshes each feed)
# --------------------------------------------------------------------------- #
def _get(path):
    r = requests.get(f"{BASE}/{path}", timeout=10)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=300)
def get_forecast():    return _get("2-hour-weather-forecast")

@st.cache_data(ttl=300)
def get_temperature(): return _get("air-temperature")

@st.cache_data(ttl=300)
def get_humidity():    return _get("relative-humidity")

@st.cache_data(ttl=900)
def get_pm25():        return _get("pm25")

@st.cache_data(ttl=900)
def get_psi():         return _get("psi")

# --------------------------------------------------------------------------- #
# 2. PARSING HELPERS
# --------------------------------------------------------------------------- #
def forecast_areas(j):
    """{area_name: {forecast, lat, lon}} from the 2-hour forecast feed."""
    meta = {a["name"]: a["label_location"] for a in j["area_metadata"]}
    out = {}
    for f in j["items"][0]["forecasts"]:
        loc = meta.get(f["area"], {})
        out[f["area"]] = {"forecast": f["forecast"],
                          "lat": loc.get("latitude"),
                          "lon": loc.get("longitude")}
    return out

def nearest_value(j, lat, lon):
    """Nearest station reading (temp/humidity feeds share this shape)."""
    stations = {s["id"]: s["location"] for s in j["metadata"]["stations"]}
    best, best_d = None, 1e9
    for rd in j["items"][0]["readings"]:
        loc = stations.get(rd["station_id"])
        if not loc:
            continue
        d = (loc["latitude"] - lat) ** 2 + (loc["longitude"] - lon) ** 2
        if d < best_d:
            best, best_d = rd["value"], d
    return best

def area_to_region(lat, lon):
    """Crude area -> PSI/PM2.5 region. Improve with real polygons later."""
    if lat is None:               return "central"
    if lat > 1.38:                return "north"
    if lat < 1.29:                return "south"
    if lon > 103.87:              return "east"
    if lon < 103.75:              return "west"
    return "central"

def pm25_for_region(j, region):
    return j["items"][0]["readings"]["pm25_one_hourly"].get(region)

def psi_for_region(j, region):
    return j["items"][0]["readings"]["psi_twenty_four_hourly"].get(region)

# --------------------------------------------------------------------------- #
# 3. HEAT INDEX  (NWS Rothfusz regression; temp in °C, RH in %)
#    NOTE: This is "feels-like" air temperature, NOT NEA's official WBGT
#    heat-stress metric (which also needs sun + wind). Good enough for a
#    walk decision; swap in WBGT later if you want to match NEA exactly.
# --------------------------------------------------------------------------- #
def heat_index_c(temp_c, rh):
    if temp_c is None or rh is None:
        return temp_c
    t = temp_c * 9 / 5 + 32                     # to Fahrenheit
    if t < 80:                                  # formula only valid when hot
        return round(temp_c, 1)
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh
          - 0.22475541 * t * rh - 0.00683783 * t * t
          - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
          + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
    if rh < 13 and 80 <= t <= 112:
        hi -= ((13 - rh) / 4) * ((17 - abs(t - 95)) / 17) ** 0.5
    elif rh > 85 and 80 <= t <= 87:
        hi += ((rh - 85) / 10) * ((87 - t) / 5)
    return round((hi - 32) * 5 / 9, 1)          # back to Celsius

# --------------------------------------------------------------------------- #
# 4. CLASSIFICATION + VERDICT
# --------------------------------------------------------------------------- #
def rain_status(text):
    t = text.lower()
    if any(w in t for w in ["thundery", "heavy rain"]): return "bad", text
    if any(w in t for w in ["rain", "showers"]):        return "warn", text
    return "good", text

def heat_status(feels):
    if feels is None:   return "unknown", "No data"
    if feels < 32:      return "good", f"{feels}°C feels-like"
    if feels < 39:      return "warn", f"{feels}°C — Caution"
    return "bad", f"{feels}°C — Danger"

def haze_status(pm):                            # NEA 1-hour PM2.5 bands
    if pm is None:      return "unknown", "No data"
    if pm <= 55:        return "good", f"Normal ({pm} µg/m³)"
    if pm <= 150:       return "warn", f"Elevated ({pm} µg/m³)"
    return "bad", f"High ({pm} µg/m³)"

def overall_verdict(statuses):
    if "bad" in statuses:  return "🔴 Stay in", "#c0392b"
    if "warn" in statuses: return "🟠 Go with caution", "#e67e22"
    return "🟢 Good to go", "#27ae60"

COLORS = {"good": "#27ae60", "warn": "#e67e22",
          "bad": "#c0392b", "unknown": "#7f8c8d"}

# --------------------------------------------------------------------------- #
# 5. UI
# --------------------------------------------------------------------------- #
st.title("🌤️ Weather or Not")
st.caption("Rain, heat and haze — should you head out now, or wait?")

try:
    fc, temp, hum, pm, psi = (get_forecast(), get_temperature(),
                              get_humidity(), get_pm25(), get_psi())
except Exception as e:
    st.error(f"Couldn't reach NEA's API right now: {e}")
    st.stop()

areas = forecast_areas(fc)
names = sorted(areas)
default = "Woodlands" if "Woodlands" in names else names[0]
area = st.sidebar.selectbox("📍 Your area", names, index=names.index(default))

info = areas[area]
region = area_to_region(info["lat"], info["lon"])
feels = heat_index_c(nearest_value(temp, info["lat"], info["lon"]),
                     nearest_value(hum, info["lat"], info["lon"]))

r_stat, r_msg = rain_status(info["forecast"])
h_stat, h_msg = heat_status(feels)
z_stat, z_msg = haze_status(pm25_for_region(pm, region))
verdict, vcolor = overall_verdict([r_stat, h_stat, z_stat])

st.markdown(
    f"""<div style="background:{vcolor};color:white;padding:24px;
        border-radius:12px;text-align:center;margin-bottom:20px;">
        <div style="font-size:42px;font-weight:800;">{verdict}</div>
        <div style="font-size:18px;opacity:0.9;">in {area}</div></div>""",
    unsafe_allow_html=True)

def card(col, title, value, status):
    col.markdown(
        f"""<div style="border:2px solid {COLORS[status]};border-radius:10px;
            padding:16px;text-align:center;">
            <div style="font-size:15px;color:gray;">{title}</div>
            <div style="font-size:24px;font-weight:700;color:{COLORS[status]};">
            {value}</div></div>""",
        unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
card(c1, "🌧️ Rain (next 2h)", r_msg, r_stat)
card(c2, "🔥 Heat (feels-like)", h_msg, h_stat)
card(c3, f"😷 Haze — live PM2.5 ({region})", z_msg, z_stat)

# 24-hour PSI as next-day context (NEA's recommended use for PSI)
psi_val = psi_for_region(psi, region)
if psi_val is not None:
    st.caption(f"24-hour PSI for {region} (next-day guide): {psi_val}")

# --- Map: live PM2.5 by region + your area pin (light + fast) ---
st.subheader("🗺️ Air quality across Singapore (1-hour PM2.5)")
m = folium.Map(location=[1.3521, 103.8198], zoom_start=11, tiles="cartodbpositron")
if info["lat"]:
    folium.Marker([info["lat"], info["lon"]],
                  popup=f"{area}: {info['forecast']}, feels {feels}°C",
                  icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
for reg in pm["region_metadata"]:
    val = pm25_for_region(pm, reg["name"])
    loc = reg["label_location"]
    color = "green" if val <= 55 else "orange" if val <= 150 else "red"
    folium.CircleMarker([loc["latitude"], loc["longitude"]], radius=14,
                        color=color, fill=True, fill_opacity=0.6,
                        popup=f"{reg['name'].title()}: {val} µg/m³").add_to(m)
st_folium(m, width=900, height=450, returned_objects=[])

with st.expander("Show raw forecast data"):
    st.dataframe(pd.DataFrame(fc["items"][0]["forecasts"]))

st.caption("Data © Data.gov.sg, Meteorological Service Singapore, "
           "National Environment Agency")

# --------------------------------------------------------------------------- #
# NEXT IMPROVEMENTS
# --------------------------------------------------------------------------- #
# 1. The "walk window": pull the 24-hour forecast (morning/afternoon/evening
#    blocks) so the verdict can say "wait till 5pm" instead of only "now".
# 2. Geolocation: replace the area dropdown with browser GPS, snap to nearest
#    area by lat/lon.
# 3. Real WBGT for heat instead of feels-like, to match NEA's advisory exactly.
# 4. Multi-language (EN / 中文 / Tamil / Malay) via a translations dict.
# 5. Auto-refresh with streamlit-autorefresh.