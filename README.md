# CivicLens

**A nonpartisan civic education tool for voters in all 50 states and D.C.**

CivicLens helps first-time and returning voters find their representatives, track legislation, research candidates, and navigate the voting process — all in one place. Enter an address and the app detects your state automatically.

Built for the 2026 election cycle.

---

## Features

| Section | Description |
|---|---|
| 📍 **Polling Finder** | Look up your polling place by address via the Google Civic API, plus your state's official voting links |
| 📅 **Deadlines** | Election Day for everyone; hand-verified 2026 registration, early-voting, and absentee dates for North Carolina; official deadline resources for every other state |
| 🏛️ **My Representatives** | Your governor (or D.C.'s mayor), U.S. Senators, U.S. Representative, and state legislators |
| 🗺️ **Rep Map** | Interactive district map for any state, colored by party — U.S. House, State Senate, and State House boundaries plus governor and senator overlays |
| 📋 **Bill Tracker** | Browse and search active legislation in any state, with optional plain-English AI summaries |
| 🔍 **District Compare** | Compare representatives for two addresses side by side — same state or different states |
| 🗳️ **Candidates** | AI-assisted research on 2026 races in any state, with policy positions from public sources |

The sidebar also has a **color theme** picker (six light themes and a dark one). Your choice is remembered in the page URL — no cookies or accounts.

---

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io)
- **Maps:** [Folium](https://python-visualization.github.io/folium/) + [U.S. Census TIGERweb](https://tigerweb.geo.census.gov)
- **Representative data:** [OpenStates API v3](https://v3.openstates.org) + [unitedstates/congress-legislators](https://github.com/unitedstates/congress-legislators)
- **Governors:** [Wikidata](https://www.wikidata.org) (no free government API covers current governors)
- **Geocoding:** [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org)
- **Election data:** [Google Civic Information API](https://developers.google.com/civic-information)
- **AI bill summaries and candidate research:** [Google Gemini 2.5 Flash](https://ai.google.dev), with Google Search grounding for candidates
- **AI fallback:** [Groq](https://groq.com) (GPT-OSS 120B) + [Tavily](https://tavily.com) search
- **Language:** Python 3.11

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/adi-kai/CivicLens.git
cd CivicLens
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Create `.streamlit/secrets.toml` — **never commit this file** (it's already in `.gitignore`):

```toml
[google]
api_key = "YOUR_GOOGLE_API_KEY"         # required

[openstates]
api_key = "YOUR_OPENSTATES_API_KEY"     # required

[gemini]
api_key = "YOUR_GEMINI_API_KEY"         # optional — bill summaries + candidate research

[groq]
api_key = "YOUR_GROQ_API_KEY"           # optional — candidate research fallback

[tavily]
api_key = "YOUR_TAVILY_API_KEY"         # optional — candidate research fallback
```

The app runs without the optional keys; the AI features are just disabled or limited.

### 4. Run locally

Run from the project folder — Streamlit reads `secrets.toml` and the theme config from the folder it's started in:

```bash
streamlit run civiclens_app.py
```

### 5. Run the render check

```bash
python tests/smoke_test.py
```

This opens every section with all network calls replaced by canned data, so it needs no API keys or internet, and fails if anything crashes or is missing.

---

## API Keys

| Service | Free Tier | Purpose |
|---|---|---|
| [Google Cloud](https://console.cloud.google.com) | Yes | Civic Information API (polling places) |
| [OpenStates](https://openstates.org/accounts/login/) | Yes | Representatives and bills |
| [Google AI Studio](https://aistudio.google.com) | Yes | Gemini bill summaries and candidate research |
| [Groq](https://console.groq.com) | Yes | Fallback AI (GPT-OSS 120B) |
| [Tavily](https://tavily.com) | Yes | Fallback web search |

Nominatim, TIGERweb, congress-legislators, and Wikidata need no key. All APIs used have free tiers sufficient for development and light production use.

---

## Project Structure

```
civiclens_app.py        # entry point: page setup, sidebar, theme picker, policy footer
civiclens/
  config.py             # API keys from secrets.toml
  states.py             # all 50 states + D.C., per-state race lists
  helpers.py            # shared helpers (party styling, rep labels, rate limiting)
  theme.py              # fonts, card styles, color themes
  data/                 # one module per outside service, all cached
    geocode.py  civic.py  openstates.py  congress.py  governors.py  tiger.py  ai.py
  tabs/                 # one module per sidebar section, each with render()
tests/smoke_test.py     # render check for every section
privacy-policy.html
terms-of-service.html
```

---

## Architecture Notes

- **No data storage** — addresses entered by users are passed directly to geocoding and representative APIs and discarded. Nothing is written to a database or log.
- **Caching** — results are cached in memory with `st.cache_data`: geocoding for 24 hours, governors for 6 hours, representatives and district boundaries for 1 hour, bills for 30 minutes. Failed map-boundary loads aren't cached, so the next click retries.
- **Rate limiting** — Gemini candidate research is rate-limited per session (5 calls/minute) with automatic fallback to Groq + Tavily.
- **No invented candidates** — both AI prompts tell the model to report that no 2026 election was found rather than make up candidates, and the fallback may only use facts from its search results.
- **TIGERweb resilience** — district boundary fetching tries multiple field-name variants (`STATE='37'`, `STUSPS='NC'`) to handle Census API schema changes across years.
- **Federal rep data** — OpenStates' per-state rosters list state legislators only, so the Rep Map's U.S. House and Senate data come from the public-domain `unitedstates/congress-legislators` dataset.
- **Deadlines** — exact dates are shown only where they've been verified against the official source (currently North Carolina). Other states get links to official resources rather than guessed dates.

---

## Privacy

CivicLens does not store, sell, or share any personal information. See the [Privacy Policy](privacy-policy.html) for full details.

---

## Disclaimer

CivicLens is a nonpartisan tool and is not affiliated with any government agency, political party, or candidate. Governor data comes from Wikidata, which is community-edited; each card links the official `.gov` site to verify. AI-generated candidate information is sourced from public web sources and should always be verified with official campaign sites and your [state election office](https://www.eac.gov/voters/register-and-vote-in-your-state).

---

## License

MIT License — free to use, modify, and distribute with attribution.
