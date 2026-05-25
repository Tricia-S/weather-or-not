# 🌤️ Weather or Not

*Should I go out now, or wait?*

A Streamlit app that answers one everyday Singapore question — is this a good
time to head outside? — by combining three live government data feeds into a
single **go / caution / stay-in** verdict for any area on the island.

🔗 **Live app:** _add your Streamlit Cloud link here after deploying_

## Why this exists

Two of the things Singaporeans most often weigh before stepping out are **heat**
and **haze**, and they don't always show up in a plain "is it raining?" check:

- Singapore is heating at about **twice the global average**, and recorded
  **29 high-heat-stress days in 2025** (up from 21 in 2024). A dry afternoon
  walk can still be miserable — or unsafe — because of heat, not rain.
- During haze episodes, a **PSI above 100 is "unhealthy,"** and NEA advises
  cutting back on outdoor activity.

So instead of just showing the weather, this app folds rain, heat and air
quality into one decision.

## What it shows

| Factor | Source | What it answers |
|--------|--------|-----------------|
| 🌧️ **Rain** | 2-hour weather forecast | Will I get wet if I leave now? |
| 🔥 **Heat** | Air temperature + humidity → feels-like heat index | Is it uncomfortably / dangerously hot? |
| 😷 **Haze** | Live 1-hour PM2.5 (24-hour PSI as next-day context) | Is the air safe right now? |

The worst of the three drives the headline verdict, with a live PM2.5 map of
the five regions and your selected area pinned.

## Design note: live data, no stored files

This app calls the [data.gov.sg](https://data.gov.sg) NEA APIs **directly on
each load** — there are no spreadsheets or scheduled pipelines, so the data is
always current rather than a snapshot. Responses are cached briefly
(`st.cache_data`) at intervals matching how often NEA refreshes each feed.

The APIs used are open and require **no API key**:

- `/v1/environment/2-hour-weather-forecast`
- `/v1/environment/air-temperature`
- `/v1/environment/relative-humidity`
- `/v1/environment/pm25`
- `/v1/environment/psi`

## Run it locally

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate        # Windows  (use: source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Roadmap

- [ ] **Walk window** — use the 24-hour forecast (morning/afternoon/evening) so
      the app can say *"wait till 5pm"*, not just judge *now*.
- [ ] **Geolocation** — replace the area dropdown with the browser's location.
- [ ] **Real WBGT** for heat, to match NEA's official Heat Stress Advisory.
- [ ] **Multi-language** (EN / 中文 / Tamil / Malay).
- [ ] **Auto-refresh** so the verdict updates itself.

## Data attribution

Data © [Data.gov.sg](https://data.gov.sg), Meteorological Service Singapore,
and the National Environment Agency.
