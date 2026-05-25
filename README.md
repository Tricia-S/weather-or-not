# 🌤️ Weather or Not

*Should I go out now, or wait?*

A Streamlit app that answers one everyday Singapore question — is this a good
time to head outside? — for any area on the island. It combines live government
data into a **go / caution / stay-in** verdict for *right now*, plus a **24-hour
timeline** that highlights the best upcoming window, so it can tell you *"not
now — this evening is clear and cooler"* instead of only judging the present
moment.

Available in English, 中文, Tamil and Bahasa Melayu, and built mobile-first so
it works on a phone or a laptop.

🔗 **Live app:** https://weather-or-not-csn4l5bvl6evcbpwemfkrf.streamlit.app/

## Why this exists

Two of the things Singaporeans most often weigh before stepping out are **heat**
and **haze**, and they don't always show up in a plain "is it raining?" check:

- Singapore is heating at about **twice the global average**, and recorded
  **29 high-heat-stress days in 2025** (up from 21 in 2024). A dry afternoon
  walk can still be miserable — or unsafe — because of heat, not rain.
- During haze episodes, a **PSI above 100 is "unhealthy,"** and NEA advises
  cutting back on outdoor activity.

So instead of just showing the weather, this app folds rain, temperature and air
quality into one decision, while also displaying humidity as additional comfort
context.

## What it shows

| Factor | Source | What it answers |
|--------|--------|-----------------|
| 🌧️ **Rain** | 2-hour weather forecast | Will I get wet if I leave now? |
| 🌡️ **Temperature** | Live air temperature | Is it unusually hot now? |
| 💧 **Humidity** | Live relative humidity | How humid or sticky will it feel outdoors? |
| 😷 **Haze** | Live 1-hour PM2.5 (24-hour PSI as next-day context) | Is the air safe right now? |

TThe headline verdict is driven by rain, temperature and air quality, while
humidity is displayed separately as additional context for outdoor comfort. 
Below it, a **24-hour timeline** lays out each upcoming forecast block 
(morning / afternoon / evening / night) colour-coded by rain risk, with 
the first clear block starred as the **best window** — that's what turns this 
from a dashboard into a decision. A live map then shows a dot for every NEA 
area across the island, each coloured by the same rain + temperature + haze verdict 
(so green means genuinely pleasant, not just dry), with your selected area ringed. 
The verdict auto-refreshes every few minutes.

## Design note: live data, no stored files

This app calls the [data.gov.sg](https://data.gov.sg) NEA APIs **directly on
each load** — there are no spreadsheets or scheduled pipelines, so the data is
always current rather than a snapshot. Responses are cached briefly
(`st.cache_data`) at intervals matching how often NEA refreshes each feed.

The APIs used are open and require **no API key**:

- `/v1/environment/2-hour-weather-forecast`
- `/v1/environment/24-hour-weather-forecast`
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

## Built so far

- [x] **Now verdict** — rain + temperature + haze rolled into one go / caution / stay-in call.
- [x] **24-hour walk-window timeline** — see when the better windows are, not just now.
- [x] **Multi-language** — English / 中文 / Tamil / Bahasa Melayu.
- [x] **Auto-refresh** — the verdict keeps itself current.
- [x] **Mobile-friendly layout** — adapts to phone or laptop.

## Ideas for later

- [ ] **Finer time granularity** — the timeline blocks are as coarse as NEA's
      24-hour forecast (morning / afternoon / evening / night); a smarter model
      could interpolate narrower windows.
- [ ] **Forecast-accuracy tracking** — log each forecast and compare it against
      what actually happened, to show how reliable the prediction was.
- [ ] **Saved areas & alerts** — remember frequent spots and notify when a good
      window opens.

## Data attribution

Data © [Data.gov.sg](https://data.gov.sg), Meteorological Service Singapore,
and the National Environment Agency.
