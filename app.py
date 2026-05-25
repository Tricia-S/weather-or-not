from datetime import datetime, timezone, timedelta

import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

BASE = "https://api.data.gov.sg/v1/environment"
SGT = timezone(timedelta(hours=8))

st.set_page_config(page_title="Weather or Not", page_icon="🌤️",
                   layout="wide", initial_sidebar_state="expanded")

# Re-run every 5 minutes so the verdict stays current (cache prevents real
# API hammering within each feed's TTL).
st_autorefresh(interval=5 * 60 * 1000, key="auto")

# --------------------------------------------------------------------------- #
# 1. TRANSLATIONS
# --------------------------------------------------------------------------- #
TR = {
    "en": {
        "tagline": "Should you head out now, or wait?",
        "your_area": "Your area", "now_in": "Right now in {area}",
        "good": "🟢 Good to go", "caution": "🟠 Go with caution",
        "stay": "🔴 Stay in",
        "rain": "🌧️ Rain (next 2h)", "heat": "🔥 Feels-like",
        "humidity": "💧 Humidity", "actual": "actual",
        "haze": "😷 Haze — live PM2.5 ({region})",
        "timeline": "📅 Next 24 hours", "best": "Best window",
        "today": "Today", "tomorrow": "Tomorrow", "now": "Now", "later": "Later",
        "morning": "morning", "afternoon": "afternoon",
        "evening": "evening", "night": "night",
        "feels_like": "feels-like", "warn_heat": "Caution",
        "danger_heat": "Danger", "normal": "Normal",
        "elevated": "Elevated", "high": "High", "no_data": "No data",
        "psi_context": "24-hour PSI for {region} (next-day guide): {val}",
        "air_map": "🗺️ Air quality across Singapore (1-hour PM2.5)",
        "cond_map": "🗺️ Where's good to go right now",
        "raw": "Show raw forecast data",
    },
    "zh": {
        "tagline": "现在适合出门吗，还是再等等？",
        "your_area": "你的地区", "now_in": "{area} 现在情况",
        "good": "🟢 适合出门", "caution": "🟠 谨慎出门",
        "stay": "🔴 留在室内",
        "rain": "🌧️ 降雨（未来2小时）", "heat": "🔥 体感温度",
        "humidity": "💧 湿度", "actual": "实际",
        "haze": "😷 烟霾 — 实时 PM2.5（{region}）",
        "timeline": "📅 未来24小时", "best": "最佳时段",
        "today": "今天", "tomorrow": "明天", "now": "现在", "later": "稍后",
        "morning": "早上", "afternoon": "下午",
        "evening": "傍晚", "night": "夜间",
        "feels_like": "体感", "warn_heat": "注意",
        "danger_heat": "危险", "normal": "正常",
        "elevated": "偏高", "high": "高", "no_data": "暂无数据",
        "psi_context": "{region} 24小时 PSI（次日参考）：{val}",
        "air_map": "🗺️ 全岛空气质量（1小时 PM2.5）",
        "cond_map": "🗺️ 现在哪里适合出门",
        "raw": "显示原始预报数据",
    },
    "ta": {
        "tagline": "இப்போது வெளியே செல்லலாமா, அல்லது காத்திருக்கவா?",
        "your_area": "உங்கள் பகுதி", "now_in": "{area} — இப்போது",
        "good": "🟢 செல்லலாம்", "caution": "🟠 கவனமாக செல்லவும்",
        "stay": "🔴 உள்ளே இருங்கள்",
        "rain": "🌧️ மழை (அடுத்த 2 மணி)", "heat": "🔥 உணரும் வெப்பம்",
        "humidity": "💧 ஈரப்பதம்", "actual": "உண்மை",
        "haze": "😷 புகைமூட்டம் — PM2.5 ({region})",
        "timeline": "📅 அடுத்த 24 மணி", "best": "சிறந்த நேரம்",
        "today": "இன்று", "tomorrow": "நாளை", "now": "இப்போது", "later": "பின்னர்",
        "morning": "காலை", "afternoon": "மதியம்",
        "evening": "மாலை", "night": "இரவு",
        "feels_like": "உணரும்", "warn_heat": "கவனம்",
        "danger_heat": "ஆபத்து", "normal": "சாதாரண",
        "elevated": "உயர்ந்த", "high": "அதிக", "no_data": "தரவு இல்லை",
        "psi_context": "{region} 24-மணி PSI (மறுநாள் வழிகாட்டி): {val}",
        "air_map": "🗺️ காற்று தரம் (1-மணி PM2.5)",
        "cond_map": "🗺️ இப்போது எங்கு செல்வது நல்லது",
        "raw": "மூல முன்னறிவிப்பு தரவு",
    },
    "ms": {
        "tagline": "Patut keluar sekarang, atau tunggu dulu?",
        "your_area": "Kawasan anda", "now_in": "Sekarang di {area}",
        "good": "🟢 Boleh keluar", "caution": "🟠 Keluar dengan berhati-hati",
        "stay": "🔴 Duduk di dalam",
        "rain": "🌧️ Hujan (2 jam akan datang)", "heat": "🔥 Suhu terasa",
        "humidity": "💧 Kelembapan", "actual": "sebenar",
        "haze": "😷 Jerebu — PM2.5 langsung ({region})",
        "timeline": "📅 24 jam akan datang", "best": "Masa terbaik",
        "today": "Hari ini", "tomorrow": "Esok", "now": "Sekarang", "later": "Kemudian",
        "morning": "pagi", "afternoon": "tengah hari",
        "evening": "petang", "night": "malam",
        "feels_like": "terasa", "warn_heat": "Berhati-hati",
        "danger_heat": "Bahaya", "normal": "Normal",
        "elevated": "Tinggi sedikit", "high": "Tinggi", "no_data": "Tiada data",
        "psi_context": "PSI 24-jam {region} (panduan esok): {val}",
        "air_map": "🗺️ Kualiti udara seluruh Singapura (PM2.5 1-jam)",
        "cond_map": "🗺️ Di mana sesuai untuk keluar sekarang",
        "raw": "Tunjuk data ramalan mentah",
    },
}

def T(lang, key, **kw):
    s = TR.get(lang, TR["en"]).get(key, TR["en"].get(key, key))
    return s.format(**kw) if kw else s

# --------------------------------------------------------------------------- #
# 2. API LAYER (cached; TTLs match NEA refresh rates)
# --------------------------------------------------------------------------- #
def _get(path):
    r = requests.get(f"{BASE}/{path}", timeout=10)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=300)
def get_forecast2():   return _get("2-hour-weather-forecast")

@st.cache_data(ttl=900)
def get_forecast24():  return _get("24-hour-weather-forecast")

@st.cache_data(ttl=300)
def get_temperature(): return _get("air-temperature")

@st.cache_data(ttl=300)
def get_humidity():    return _get("relative-humidity")

@st.cache_data(ttl=900)
def get_pm25():        return _get("pm25")

@st.cache_data(ttl=900)
def get_psi():         return _get("psi")

# --------------------------------------------------------------------------- #
# 3. PARSING HELPERS
# --------------------------------------------------------------------------- #
def forecast_areas(j):
    meta = {a["name"]: a["label_location"] for a in j["area_metadata"]}
    out = {}
    for f in j["items"][0]["forecasts"]:
        loc = meta.get(f["area"], {})
        out[f["area"]] = {"forecast": f["forecast"],
                          "lat": loc.get("latitude"),
                          "lon": loc.get("longitude")}
    return out

def nearest_value(j, lat, lon):
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
    if lat is None:    return "central"
    if lat > 1.38:     return "north"
    if lat < 1.29:     return "south"
    if lon > 103.87:   return "east"
    if lon < 103.75:   return "west"
    return "central"

def pm25_for_region(j, region):
    return j["items"][0]["readings"]["pm25_one_hourly"].get(region)

def psi_for_region(j, region):
    return j["items"][0]["readings"]["psi_twenty_four_hourly"].get(region)

def fmt_time(dt):
    """12-hour time, cross-platform (no %-I, which breaks on Windows)."""
    h = dt.hour % 12 or 12
    ap = "am" if dt.hour < 12 else "pm"
    return f"{h}:{dt.minute:02d}{ap}" if dt.minute else f"{h}{ap}"


def forecast24_blocks(j, region, lang, now):
    """Parse 24h periods into [{label, text, status}] for the timeline.

    NEA's 24-hour feed sometimes returns 'Invalid date' for a single chunk's
    timestamp. Since the chunks are contiguous, we reconstruct a missing time
    from its neighbours (start = previous chunk's end, end = next chunk's
    start), so a block almost never loses its label.
    """
    try:
        periods = j["items"][0].get("periods", [])
    except (KeyError, IndexError, TypeError):
        return []

    def parse(t, key):
        try:
            return datetime.fromisoformat(t[key]).astimezone(SGT)
        except (ValueError, KeyError, TypeError):
            return None

    # Pass 1: pull each chunk's time + forecast text
    raw = []
    for p in periods:
        regions = p.get("regions", {})
        t = p.get("time", {}) or {}
        raw.append({"start": parse(t, "start"), "end": parse(t, "end"),
                    "text": regions.get(region) or regions.get("central") or ""})

    # Pass 2: fill any gaps from neighbouring chunks
    for i, r in enumerate(raw):
        if r["start"] is None and i > 0:
            r["start"] = raw[i - 1]["end"]
        if r["end"] is None and i + 1 < len(raw):
            r["end"] = raw[i + 1]["start"]

    # Pass 3: build labels with time ranges
    blocks = []
    for r in raw:
        start, end, text = r["start"], r["end"], r["text"]
        if not text:
            continue
        if start and end and end < now:           # already passed
            continue
        if start and end and start <= now < end:
            name = T(lang, "now")
        elif start:
            day = "today" if start.date() == now.date() else "tomorrow"
            h = start.hour
            tod = ("morning" if 5 <= h < 12 else "afternoon" if 12 <= h < 17
                   else "evening" if 17 <= h < 21 else "night")
            name = f"{T(lang, day)} {T(lang, tod)}"
        else:
            name = T(lang, "later")
        rng = f" · {fmt_time(start)}–{fmt_time(end)}" if start and end else ""
        blocks.append({"label": name + rng, "text": text,
                       "status": rain_status(text)[0]})
    return blocks

# --------------------------------------------------------------------------- #
# 4. HEAT INDEX (feels-like; NWS Rothfusz, temp °C + RH %)
# --------------------------------------------------------------------------- #
def heat_index_c(temp_c, rh):
    if temp_c is None or rh is None:
        return temp_c
    t = temp_c * 9 / 5 + 32
    if t < 80:
        return round(temp_c, 1)
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh
          - 0.22475541 * t * rh - 0.00683783 * t * t
          - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
          + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
    if rh < 13 and 80 <= t <= 112:
        hi -= ((13 - rh) / 4) * ((17 - abs(t - 95)) / 17) ** 0.5
    elif rh > 85 and 80 <= t <= 87:
        hi += ((rh - 85) / 10) * ((87 - t) / 5)
    return round((hi - 32) * 5 / 9, 1)

# --------------------------------------------------------------------------- #
# 5. CLASSIFICATION + VERDICT
# --------------------------------------------------------------------------- #
def rain_status(text):
    t = text.lower()
    if any(w in t for w in ["thundery", "heavy rain"]): return "bad", text
    if any(w in t for w in ["rain", "showers"]):        return "warn", text
    return "good", text

def heat_status(feels, lang):
    if feels is None:  return "unknown", T(lang, "no_data")
    if feels < 32:     return "good", f"{feels}°C {T(lang,'feels_like')}"
    if feels < 39:     return "warn", f"{feels}°C — {T(lang,'warn_heat')}"
    return "bad", f"{feels}°C — {T(lang,'danger_heat')}"

def humidity_status(rh):
    """Display-only band for the humidity card (not part of the verdict —
    its effect is already captured in the feels-like temperature)."""
    if rh is None:  return "unknown"
    if rh < 70:     return "good"
    if rh <= 85:    return "warn"
    return "bad"

def haze_status(pm, lang):
    if pm is None:     return "unknown", T(lang, "no_data")
    if pm <= 55:       return "good", f"{T(lang,'normal')} ({pm} µg/m³)"
    if pm <= 150:      return "warn", f"{T(lang,'elevated')} ({pm} µg/m³)"
    return "bad", f"{T(lang,'high')} ({pm} µg/m³)"

def overall_verdict(statuses, lang):
    if "bad" in statuses:  return T(lang, "stay"), "#c0392b"
    if "warn" in statuses: return T(lang, "caution"), "#e67e22"
    return T(lang, "good"), "#27ae60"

COLORS = {"good": "#27ae60", "warn": "#e67e22",
          "bad": "#c0392b", "unknown": "#7f8c8d"}
ICON = {"good": "☀️", "warn": "🌦️", "bad": "🌧️", "unknown": "❔"}

# --------------------------------------------------------------------------- #
# 6. UI
# --------------------------------------------------------------------------- #
LANGS = {"English": "en", "中文": "zh", "தமிழ்": "ta", "Bahasa Melayu": "ms"}
lang_name = st.sidebar.selectbox("🌐 Language", list(LANGS))
lang = LANGS[lang_name]

st.title("🌤️ Weather or Not")
st.caption(T(lang, "tagline"))

try:
    fc2, fc24 = get_forecast2(), get_forecast24()
    temp, hum = get_temperature(), get_humidity()
    pm, psi = get_pm25(), get_psi()
except Exception as e:
    st.error(f"Couldn't reach NEA's API right now: {e}")
    st.stop()

areas = forecast_areas(fc2)
names = sorted(areas)
default = "Woodlands" if "Woodlands" in names else names[0]
if "area" not in st.session_state:
    st.session_state.area = default
area = st.sidebar.selectbox(T(lang, "your_area"), names, key="area")

info = areas[area]
region = area_to_region(info["lat"], info["lon"])
temp_c = nearest_value(temp, info["lat"], info["lon"])
rh = nearest_value(hum, info["lat"], info["lon"])
feels = heat_index_c(temp_c, rh)
now = datetime.now(SGT)

r_stat, r_msg = rain_status(info["forecast"])
h_stat = heat_status(feels, lang)[0]
z_stat, z_msg = haze_status(pm25_for_region(pm, region), lang)
# Humidity is shown but NOT in the verdict — feels-like already accounts for it.
verdict, vcolor = overall_verdict([r_stat, h_stat, z_stat], lang)

# --- NOW verdict ---
st.markdown(
    f"""<div style="background:{vcolor};color:white;padding:22px;
        border-radius:12px;text-align:center;margin-bottom:6px;">
        <div style="font-size:38px;font-weight:800;">{verdict}</div>
        <div style="font-size:17px;opacity:0.9;">
        {T(lang,'now_in',area=area)}</div></div>""",
    unsafe_allow_html=True)

def card(col, title, value, status, sub=""):
    sub_html = (f'<div style="font-size:13px;color:gray;margin-top:3px;">{sub}</div>'
                if sub else "")
    col.markdown(
        f"""<div style="border:2px solid {COLORS[status]};border-radius:10px;
            padding:14px;text-align:center;min-height:104px;">
            <div style="font-size:14px;color:gray;">{title}</div>
            <div style="font-size:22px;font-weight:700;color:{COLORS[status]};">
            {value}</div>{sub_html}</div>""",
        unsafe_allow_html=True)

# Feels-like card: feels-like temp big, actual temp small underneath
if feels is None:
    feels_val, feels_sub = T(lang, "no_data"), ""
else:
    word = {"warn": T(lang, "warn_heat"),
            "bad": T(lang, "danger_heat")}.get(h_stat, "")
    feels_val = f"{feels}°C" + (f" — {word}" if word else "")
    feels_sub = (f"{T(lang,'actual')} {round(temp_c, 1)}°C"
                 if temp_c is not None else "")

# Humidity card
hum_stat = humidity_status(rh)
hum_val = f"{round(rh)}%" if rh is not None else T(lang, "no_data")

c1, c2, c3, c4 = st.columns(4)
card(c1, T(lang, "rain"), r_msg, r_stat)
card(c2, T(lang, "heat"), feels_val, h_stat, sub=feels_sub)
card(c3, T(lang, "humidity"), hum_val, hum_stat)
card(c4, T(lang, "haze", region=region), z_msg, z_stat)

psi_val = psi_for_region(psi, region)
if psi_val is not None:
    st.caption(T(lang, "psi_context", region=region, val=psi_val))

# --- WALK-WINDOW TIMELINE (the centerpiece) ---
st.subheader(T(lang, "timeline"))
blocks = forecast24_blocks(fc24, region, lang, now)
best_marked = False
if not blocks:
    st.info(T(lang, "no_data"))
for b in blocks:
    star = ""
    if not best_marked and b["status"] == "good" and b["label"] != T(lang, "now"):
        star = f"⭐ {T(lang,'best')} · "
        best_marked = True
    color = COLORS[b["status"]]
    st.markdown(
        f"""<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;
            border-left:6px solid {color};background:rgba(127,127,127,0.08);
            padding:10px 14px;border-radius:6px;margin-bottom:6px;">
            <div style="font-weight:700;min-width:120px;">{b['label']}</div>
            <div style="color:inherit;">{ICON[b['status']]} {star}{b['text']}</div>
            </div>""",
        unsafe_allow_html=True)

# --- Conditions map: a dot for every NEA area (rain + heat + haze combined) ---
st.subheader(T(lang, "cond_map"))
m = folium.Map(location=[1.3521, 103.8198], zoom_start=11, tiles="cartodbpositron")
order = {"unknown": -1, "good": 0, "warn": 1, "bad": 2}
for aname, ainfo in areas.items():
    if ainfo["lat"] is None:
        continue
    a_rain = rain_status(ainfo["forecast"])[0]
    a_feels = heat_index_c(nearest_value(temp, ainfo["lat"], ainfo["lon"]),
                           nearest_value(hum, ainfo["lat"], ainfo["lon"]))
    a_heat = heat_status(a_feels, lang)[0]
    a_haze = haze_status(
        pm25_for_region(pm, area_to_region(ainfo["lat"], ainfo["lon"])), lang)[0]
    worst = max((a_rain, a_heat, a_haze), key=lambda s: order[s])
    color = {"good": "green", "warn": "orange", "bad": "red"}.get(worst, "gray")
    is_me = (aname == area)
    folium.CircleMarker(
        [ainfo["lat"], ainfo["lon"]],
        radius=10 if is_me else 6,
        color="#1f6fd6" if is_me else color,      # blue ring on your area
        weight=4 if is_me else 1,
        fill=True, fill_color=color, fill_opacity=0.85,
        popup=f"{aname}: {ainfo['forecast']}, {a_feels}°C",
    ).add_to(m)
st_folium(m, height=420, use_container_width=True, returned_objects=[])

with st.expander(T(lang, "raw")):
    st.dataframe(pd.DataFrame(fc2["items"][0]["forecasts"]))

st.caption("Data © Data.gov.sg, Meteorological Service Singapore, "
           "National Environment Agency")