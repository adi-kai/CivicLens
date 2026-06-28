# CivicLens 
 
**A nonpartisan civic education tool for North Carolina voters.**
 
CivicLens helps first-time and returning voters across NC find their representatives, track legislation, research candidates, and navigate the voting process — all in one place.
 
Built for the **NC-14 congressional district** and the 2026 election cycle.
 
---
 
## Features
 
| Tab | Description |
|---|---|
| 📍 **Polling Finder** | Look up your polling place by address via Google Civic API |
| 📅 **Deadlines** | Key NC 2026 voter registration and election deadlines |
| 🏛️ **My Representatives** | Every elected official who represents you — state and federal |
| 🗺️ **Rep Map** | Interactive NC district map colored by party, powered by U.S. Census TIGERweb |
| 📋 **Bill Tracker** | Browse and search active NC legislation via OpenStates |
| 🔍 **District Compare** | Compare representatives for two NC addresses side by side |
| 🗳️ **Candidates** | AI-powered candidate research with policy positions from official campaign sources |
 
---
 
## Tech Stack
 
- **Frontend:** [Streamlit](https://streamlit.io)
- **Maps:** [Folium](https://python-visualization.github.io/folium/) + [U.S. Census TIGERweb](https://tigerweb.geo.census.gov)
- **Representative data:** [OpenStates API v3](https://v3.openstates.org) + [unitedstates/congress-legislators](https://github.com/unitedstates/congress-legislators)
- **Geocoding:** [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org)
- **Election data:** [Google Civic Information API](https://developers.google.com/civic-information)
- **AI candidate research:** [Google Gemini 2.5 Flash](https://ai.google.dev) with Google Search grounding
- **AI fallback:** [Groq](https://groq.com) (Llama 3.3 70B) + [Tavily](https://tavily.com) search
- **Language:** Python 3.11
---
 
## Setup
 
### 1. Clone the repo
 
```bash
git clone https://github.com/YOUR_USERNAME/civiclens.git
cd civiclens
```
 
### 2. Install dependencies
 
```bash
pip install -r requirements.txt
```
 
### 3. Configure API keys
 
Create `.streamlit/secrets.toml` — **never commit this file**:
 
```toml
[google]
api_key = "YOUR_GOOGLE_API_KEY"
 
[openstates]
api_key = "YOUR_OPENSTATES_API_KEY"
 
[gemini]
api_key = "YOUR_GEMINI_API_KEY"
 
[groq]
api_key = "YOUR_GROQ_API_KEY"
 
[tavily]
api_key = "YOUR_TAVILY_API_KEY"
```
 
### 4. Run locally
 
```bash
streamlit run civiclens_app.py
```
 
---
 
## API Keys Required
 
| Service | Free Tier | Purpose |
|---|---|---|
| [Google Cloud](https://console.cloud.google.com) | Yes | Civic Information API + Geocoding |
| [OpenStates](https://openstates.org/accounts/login/) | Yes | State representative data |
| [Google AI Studio](https://aistudio.google.com) | Yes | Gemini candidate research |
| [Groq](https://console.groq.com) | Yes | Fallback AI (Llama 3.3 70B) |
| [Tavily](https://tavily.com) | Yes | Fallback web search |
 
All APIs used have free tiers sufficient for development and light production use.
 
---
 
## Architecture Notes
 
- **No data storage** — addresses entered by users are passed directly to geocoding and representative APIs and discarded. Nothing is written to a database or log.
- **Caching** — geocoding results are cached in memory for 24 hours (`st.cache_data`), API results for 1 hour, to reduce API calls and improve performance.
- **Rate limiting** — Gemini API calls are rate-limited per session (5 calls/minute) with automatic fallback to Groq + Tavily.
- **TIGERweb resilience** — district boundary fetching tries multiple field-name variants (`STATE='37'`, `STUSPS='NC'`) to handle Census API schema changes across years.
- **Federal rep data** — OpenStates covers state legislatures only. U.S. House members are sourced from the public-domain `unitedstates/congress-legislators` dataset.
---
 
## Privacy
 
CivicLens does not store, sell, or share any personal information. See [Privacy Policy](privacy-policy.html) for full details.
 
---
 
## Disclaimer
 
CivicLens is a nonpartisan tool and is not affiliated with any government agency, political party, or candidate. AI-generated candidate information is sourced from public web sources and should always be verified with official campaign sites and [ncsbe.gov](https://www.ncsbe.gov).
 
---
 
## License
 
MIT License — free to use, modify, and distribute with attribution.
 
