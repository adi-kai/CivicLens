import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import re
import time 
import urllib.parse

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="CivicLens", layout="wide", page_icon="🗳️")

GOOGLE_KEY     = st.secrets["google"]["api_key"]
OPENSTATES_KEY = st.secrets["openstates"]["api_key"]
GROQ_KEY   = st.secrets.get("groq", {}).get("api_key", "")
TAVILY_KEY = st.secrets.get("tavily", {}).get("api_key", "")
try:
    GEMINI_KEY = st.secrets["gemini"]["api_key"]
except Exception:
    GEMINI_KEY = ""

# TIGERweb — current (2025-2026) layer IDs for the Legislative MapServer
# These layer IDs are national — the same MapServer covers every state, you just
# filter by FIPS code in the WHERE clause.
# Verify at: tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer
TIGER_BASE           = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
LAYER_US_HOUSE       = 0   # 119th Congressional Districts        (STATE field, district: CD119)
LAYER_STATE_SENATE   = 1   # 2024 State Legislative Upper/Senate  (STATE field, district: SLDU)
LAYER_STATE_HOUSE    = 2   # 2024 State Legislative Lower/House   (STATE field, district: SLDL)

# Backwards-compatible aliases (kept in case other code / notebooks reference the old names)
LAYER_NC_SENATE = LAYER_STATE_SENATE
LAYER_NC_HOUSE  = LAYER_STATE_HOUSE

# Stable GeoJSON with outlines for all 50 states + DC (avoids shifting TIGERweb State_County layer IDs)
US_STATES_GEOJSON_URL = (
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
)
# Backwards-compatible alias
NC_STATE_GEOJSON_URL = US_STATES_GEOJSON_URL

# ── National state registry: USPS abbreviation → FIPS code + full name ───────
# Used to parameterize every fetcher (TIGERweb, OpenStates, bills) by state,
# and to auto-detect the right state from a geocoded address.
STATES = {
    "AL": {"fips": "01", "name": "Alabama"},
    "AK": {"fips": "02", "name": "Alaska"},
    "AZ": {"fips": "04", "name": "Arizona"},
    "AR": {"fips": "05", "name": "Arkansas"},
    "CA": {"fips": "06", "name": "California"},
    "CO": {"fips": "08", "name": "Colorado"},
    "CT": {"fips": "09", "name": "Connecticut"},
    "DE": {"fips": "10", "name": "Delaware"},
    "DC": {"fips": "11", "name": "District of Columbia"},
    "FL": {"fips": "12", "name": "Florida"},
    "GA": {"fips": "13", "name": "Georgia"},
    "HI": {"fips": "15", "name": "Hawaii"},
    "ID": {"fips": "16", "name": "Idaho"},
    "IL": {"fips": "17", "name": "Illinois"},
    "IN": {"fips": "18", "name": "Indiana"},
    "IA": {"fips": "19", "name": "Iowa"},
    "KS": {"fips": "20", "name": "Kansas"},
    "KY": {"fips": "21", "name": "Kentucky"},
    "LA": {"fips": "22", "name": "Louisiana"},
    "ME": {"fips": "23", "name": "Maine"},
    "MD": {"fips": "24", "name": "Maryland"},
    "MA": {"fips": "25", "name": "Massachusetts"},
    "MI": {"fips": "26", "name": "Michigan"},
    "MN": {"fips": "27", "name": "Minnesota"},
    "MS": {"fips": "28", "name": "Mississippi"},
    "MO": {"fips": "29", "name": "Missouri"},
    "MT": {"fips": "30", "name": "Montana"},
    "NE": {"fips": "31", "name": "Nebraska"},
    "NV": {"fips": "32", "name": "Nevada"},
    "NH": {"fips": "33", "name": "New Hampshire"},
    "NJ": {"fips": "34", "name": "New Jersey"},
    "NM": {"fips": "35", "name": "New Mexico"},
    "NY": {"fips": "36", "name": "New York"},
    "NC": {"fips": "37", "name": "North Carolina"},
    "ND": {"fips": "38", "name": "North Dakota"},
    "OH": {"fips": "39", "name": "Ohio"},
    "OK": {"fips": "40", "name": "Oklahoma"},
    "OR": {"fips": "41", "name": "Oregon"},
    "PA": {"fips": "42", "name": "Pennsylvania"},
    "RI": {"fips": "44", "name": "Rhode Island"},
    "SC": {"fips": "45", "name": "South Carolina"},
    "SD": {"fips": "46", "name": "South Dakota"},
    "TN": {"fips": "47", "name": "Tennessee"},
    "TX": {"fips": "48", "name": "Texas"},
    "UT": {"fips": "49", "name": "Utah"},
    "VT": {"fips": "50", "name": "Vermont"},
    "VA": {"fips": "51", "name": "Virginia"},
    "WA": {"fips": "53", "name": "Washington"},
    "WV": {"fips": "54", "name": "West Virginia"},
    "WI": {"fips": "55", "name": "Wisconsin"},
    "WY": {"fips": "56", "name": "Wyoming"},
}
DEFAULT_STATE = "NC"

# Reverse lookup: full lowercase state name → USPS abbreviation (for parsing
# Nominatim's "address.state" field, which comes back as a full name).
STATE_NAME_TO_ABBR = {info["name"].lower(): abbr for abbr, info in STATES.items()}
# Nominatim sometimes returns DC under a different label
STATE_NAME_TO_ABBR["washington, d.c."] = "DC"
STATE_NAME_TO_ABBR["washington dc"]    = "DC"



# RATELIMITERS
def rate_limit_check(key: str, max_calls: int = 10, window: int = 60):
    """Block if user has made too many calls in the time window."""
    now = time.time()
    call_log = st.session_state.get(key, [])
    # Drop calls outside the window
    call_log = [t for t in call_log if now - t < window]
    if len(call_log) >= max_calls:
        return False
    call_log.append(now)
    st.session_state[key] = call_log
    return True


# ─────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'DM Serif Display', serif; }

    .rep-card {
        background: #f8f9fa;
        color: #1a1a1a;              /* ADDED: force dark text on light card */
        border-left: 5px solid #888;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .rep-card.republican { border-left-color: #c0392b; }
    .rep-card.democrat   { border-left-color: #1a73e8; }
    .rep-card.other      { border-left-color: #7f8c8d; }

    .party-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-democrat   { background: #d6e4ff; color: #1a3c8f; }
    .badge-republican { background: #ffe0dd; color: #8b1a1a; }
    .badge-other      { background: #e8e8e8; color: #444; }

    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #888;
        margin: 1.5rem 0 0.5rem 0;
    }

    .info-box {
        background: #eaf3fb;
        color: #1a1a1a;              /* ADDED */
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin-top: 0.5rem;
    }

    .map-legend {
        background: white;
        color: #1a1a1a;              /* ADDED */
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }
    .legend-dot  { width: 14px; height: 14px; border-radius: 50%; display: inline-block; }

    .subject-tag {
        display: inline-block;
        padding: 1px 8px;
        border-radius: 12px;
        font-size: 0.72rem;
        background: #e9ecef;
        color: #495057;              /* already had color, this one was fine */
        margin-right: 4px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
PARTY_COLORS = {
    "democratic": "#1a73e8", "democrat": "#1a73e8",
    "republican": "#c0392b",
    "libertarian": "#f39c12",
    "green": "#27ae60",
}

def party_color(party: str) -> str:
    p = party.lower()
    for key, color in PARTY_COLORS.items():
        if key in p:
            return color
    return "#7f8c8d"

def party_css(party: str) -> str:
    p = party.lower()
    if "democrat" in p:   return "democrat"
    if "republican" in p: return "republican"
    return "other"

def party_badge(party: str) -> str:
    p = party.lower()
    if "democrat" in p:   return "badge-democrat"
    if "republican" in p: return "badge-republican"
    return "badge-other"

def party_fill(party: str) -> tuple:
    p = party.lower()
    if "democrat" in p:   return "#1a73e8", 0.25
    if "republican" in p: return "#c0392b", 0.25
    return "#888888", 0.15

# FIX #6 — Cache geocoding (24 hr TTL)
# National update: now also auto-detects the state (USPS abbreviation) from the
# geocoded address so every downstream fetcher (map, reps, bills) knows which
# state to query without the user having to pick one manually.
@st.cache_data(ttl=86400, show_spinner=False)
def geocode(address: str):
    """Returns (lat, lon, state_abbr). state_abbr is None if it can't be determined."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": "CivicLens/1.0"},
            timeout=10
        ).json()
        if r:
            result = r[0]
            lat, lon = float(result["lat"]), float(result["lon"])
            addr = result.get("address", {}) or {}

            state_abbr = None
            # Most reliable: ISO3166-2-lvl4 comes back as "US-NC"
            iso = (addr.get("ISO3166-2-lvl4") or "").upper()
            if iso.startswith("US-") and iso.split("-")[-1] in STATES:
                state_abbr = iso.split("-")[-1]
            # Fallback: match the full state name Nominatim returns
            if not state_abbr:
                state_name = (addr.get("state") or "").strip().lower()
                state_abbr = STATE_NAME_TO_ABBR.get(state_name)

            return lat, lon, state_abbr
    except Exception:
        pass
    return None, None, None

def show_searched_address(address: str):
    """Prints the address actually being used, right above whatever results follow."""
    if address and address.strip():
        st.markdown(f"""
        <div class="info-box" style="padding:0.55rem 1rem;margin:0 0 0.9rem 0;">
            📍 <strong>Address:</strong> {address}
        </div>
        """, unsafe_allow_html=True)

# FIX #4a — Discover the active election ID dynamically
@st.cache_data(ttl=3600, show_spinner=False)
def get_active_election_id() -> str:
    try:
        r = requests.get(
            "https://www.googleapis.com/civicinfo/v2/elections",
            params={"key": GOOGLE_KEY},
            timeout=10
        ).json()
        for e in reversed(r.get("elections", [])):
            if e.get("id") not in ("2000", "1"):
                return e["id"]
    except Exception:
        pass
    return "2000"

# FIX #4b — Use dynamic election ID
@st.cache_data(ttl=1800, show_spinner=False)
def get_voter_info(address: str):
    return requests.get(
        "https://www.googleapis.com/civicinfo/v2/voterinfo",
        params={"address": address, "electionId": get_active_election_id(), "key": GOOGLE_KEY}
    ).json()

# ── National voting resource links ────────────────────────────────────────────
# vote.gov publishes a stable per-state registration page at /register/{abbr}/,
# so that one link personalizes cleanly for all 50 states + DC. vote.org and the
# EAC's directory both accept any U.S. address/state on their own site, so they
# work as reliable nationwide fallbacks. We only keep NC's original hand-verified
# NCSBE deep links, since those are known-good; other states get the same
# high-quality generic tools rather than guessed-at state URLs.
def get_official_resources(state_abbr: str) -> list:
    """Returns [(label, url), ...] of official/national resources for the given state."""
    abbr = (state_abbr or DEFAULT_STATE).upper()
    if abbr == "NC":
        return [
            ("Find Your Polling Place — NCSBE", "https://vt.ncsbe.gov/PPLkup/"),
            ("Check Registration Status — NCSBE", "https://vt.ncsbe.gov/RegLkup/"),
            ("Register to Vote — NCSBE", "https://www.ncsbe.gov/registering/how-register"),
            ("Absentee Ballot Info — NCSBE", "https://www.ncsbe.gov/voting/vote-absentee-ballot"),
        ]
    state_name = STATES.get(abbr, {}).get("name", abbr)
    return [
        (f"Register to Vote in {state_name} — Vote.gov", f"https://vote.gov/register/{abbr.lower()}/"),
        ("Check Your Registration Status — Vote.org", "https://www.vote.org/am-i-registered-to-vote/"),
        ("Find Your Polling Place — Vote.org", "https://www.vote.org/polling-place-locator/"),
        ("Absentee / Mail Voting Info — Vote.org", "https://www.vote.org/absentee-ballot/"),
        ("Your State Election Office — U.S. EAC Directory", "https://www.eac.gov/voters/register-and-vote-in-your-state"),
    ]

@st.cache_data(ttl=3600, show_spinner=False)
def get_reps_by_location(lat: float, lng: float) -> list:
    try:
        r = requests.get(
            "https://v3.openstates.org/people.geo",
            params={"lat": lat, "lng": lng, "per_page": 50},
            headers={"X-API-KEY": OPENSTATES_KEY},
            timeout=15
        )
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []

def is_federal(rep: dict) -> bool:
    return rep.get("jurisdiction", {}).get("classification", "") == "country"

def is_state(rep: dict) -> bool:
    return rep.get("jurisdiction", {}).get("classification", "") == "state"

def get_chamber_label(rep: dict) -> str:
    roles = rep.get("current_role", {}) or {}
    dist  = roles.get("district", "")
    org   = roles.get("org_classification", "")
    title = roles.get("title", "")
    if is_federal(rep):
        if org == "upper":
            state_name = (rep.get("jurisdiction", {}) or {}).get("name", "")
            return f"U.S. Senator — {state_name}" if state_name else "U.S. Senator"
        return f"U.S. House — District {dist}"
    return f"{title} — District {dist}"

# Robust TIGERweb fetch — tries every known where-clause variant for the given state
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tiger_geojson(layer_id: int, state_fips: str, state_abbr: str = "") -> dict:
    url = f"{TIGER_BASE}/{layer_id}/query"
    # Try all known field-name variants the Census API has used across years
    # These layers use STATE (2-char FIPS string), NOT STATEFP — verified against layer schema June 2026
    where_clauses = [f"STATE='{state_fips}'", f"STATE={int(state_fips)}"]
    if state_abbr:
        where_clauses.append(f"STUSPS='{state_abbr}'")
    last_error = ""
    for where_clause in where_clauses:
        try:
            r = requests.get(url, params={
                "where": where_clause,
                "outFields": "*",
                "f": "geojson",
                "outSR": "4326",
                "resultRecordCount": 250,
            }, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if data.get("features"):
                    return data
                # Save any API-level error message for debugging
                last_error = data.get("error", {}).get("message", "")
            else:
                last_error = f"HTTP {r.status_code}"
        except Exception as e:
            last_error = str(e)
            continue
    # Surface the failure so it's visible during development
    st.warning(
        f"⚠️ Could not load district boundaries for layer {layer_id}. "
        f"The Census TIGERweb layer IDs may have shifted again. "
        f"Last error: {last_error or 'empty response'}. "
        f"Check: tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
    )
    return {}

def extract_district_key(props: dict, district_field: str = "") -> str:
    """
    Extract a clean integer district number from a feature's properties.
    Pass district_field to read the correct field directly (CD119, SLDU, SLDL).
    Falls back to a priority-ordered scan if the field is missing or empty.
    """
    # Try the known correct field for this layer first
    if district_field and props.get(district_field) not in (None, "", "None"):
        raw = str(props[district_field]).strip()
        try:
            return str(int(raw))
        except ValueError:
            m = re.search(r"\d+", raw)
            if m:
                return str(int(m.group()))

    # Fallback scan (catches legacy field names if Census ever renames again)
    fallback = [
        props.get("CD119"), props.get("CD119FP"),
        props.get("CD118"), props.get("CD118FP"),
        props.get("CDFP"),  props.get("CD"),
        props.get("SLDU"),  props.get("SLDUST"),
        props.get("SLDL"),  props.get("SLDLST"),
        props.get("BASENAME"), props.get("NAME"),
    ]
    for val in fallback:
        if val is not None and str(val).strip() not in ("", "None"):
            raw = str(val).strip()
            try:
                return str(int(raw))
            except ValueError:
                m = re.search(r"\d+", raw)
                if m:
                    return str(int(m.group()))
    return ""

def build_district_layer(geojson: dict, rep_lookup: dict, layer_name: str,
                         district_field: str = "") -> folium.FeatureGroup:
    fg = folium.FeatureGroup(name=layer_name, show=True)
    if not geojson or "features" not in geojson:
        return fg
    for feature in geojson["features"]:
        props     = feature.get("properties", {})
        dist_key  = extract_district_key(props, district_field)
        rep       = rep_lookup.get(dist_key, {})
        rep_name  = rep.get("name", "No data")
        rep_party = rep.get("party", "Unknown")
        rep_label = get_chamber_label(rep) if rep else ""
        rep_photo = rep.get("image", "")
        fill, opacity = party_fill(rep_party)
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;padding:4px">
            {"<img src='" + rep_photo + "' width='55' style='border-radius:50%;float:right;margin-left:8px'/>" if rep_photo else ""}
            <strong style="font-size:13px">District {dist_key}</strong><br>
            <strong>{rep_name}</strong><br>
            <em style="color:#555;font-size:12px">{rep_label}</em><br>
            <span style="color:{party_color(rep_party)};font-weight:600">{rep_party}</span>
        </div>"""
        try:
            folium.GeoJson(
                feature,
                style_function=lambda f, fill=fill, opacity=opacity: {
                    "fillColor": fill, "fillOpacity": opacity, "color": "#333", "weight": 1.2,
                },
                highlight_function=lambda f, fill=fill: {
                    "fillColor": fill, "fillOpacity": 0.45, "color": "#333", "weight": 2,
                },
                tooltip=f"District {dist_key} — {rep_name} ({rep_party})",
                popup=folium.Popup(popup_html, max_width=260),
            ).add_to(fg)
        except Exception:
            pass
    return fg

@st.cache_data(ttl=3600, show_spinner=False)
def get_state_reps_by_chamber(state_abbr: str, chamber: str) -> tuple:
    """Returns (list_of_reps, error_message). Paginates since max per_page is 50.
    state_abbr is a USPS abbreviation (e.g. 'NC', 'CA'); OpenStates jurisdiction
    slugs are just the lowercase state abbreviation."""
    results = []
    jurisdiction = (state_abbr or DEFAULT_STATE).lower()
    for page in range(1, 6):  # up to 250 reps, more than enough
        try:
            r = requests.get(
                "https://v3.openstates.org/people",
                params={"jurisdiction": jurisdiction, "org_classification": chamber,
                        "per_page": 50, "page": page},
                headers={"X-API-KEY": OPENSTATES_KEY},
                timeout=15,
            )
            if r.status_code != 200:
                return results, f"HTTP {r.status_code}: {r.text[:200]}"
            batch = r.json().get("results", [])
            results.extend(batch)
            if len(batch) < 50:
                break  # last page
        except Exception as e:
            return results, str(e)
    return results, ""

# Backwards-compatible alias
def get_all_nc_reps_by_chamber(chamber: str) -> tuple:
    return get_state_reps_by_chamber("NC", chamber)

@st.cache_data(ttl=3600, show_spinner=False)
def get_federal_house_members(state_abbr: str) -> list:
    """
    Fetch a given state's current U.S. House members.
    OpenStates only covers state legislatures, NOT Congress.
    We use the unitedstates/congress-legislators JSON (public domain, no API key).
    Returns a list of dicts shaped like OpenStates people objects so the rest of
    the code (build_rep_lookup, get_chamber_label, party_fill, etc.) works unchanged.
    """
    state_abbr = (state_abbr or DEFAULT_STATE).upper()
    state_name = STATES.get(state_abbr, {}).get("name", state_abbr)
    try:
        r = requests.get(
            "https://unitedstates.github.io/congress-legislators/legislators-current.json",
            timeout=15,
        )
        if r.status_code != 200:
            return []
        members = r.json()
        house_members = []
        for m in members:
            terms = m.get("terms", [])
            if not terms:
                continue
            latest = terms[-1]
            if latest.get("type") != "rep":
                continue
            state = latest.get("state", "")
            if state != state_abbr:
                continue
            district = str(latest.get("district", ""))
            # Map party abbreviations to full names OpenStates uses
            party_map = {"Democrat": "Democratic", "Republican": "Republican",
                         "Independent": "Independent"}
            raw_party = m.get("terms", [{}])[-1].get("party", "Unknown")
            party = party_map.get(raw_party, raw_party)
            name_obj = m.get("name", {})
            full_name = f"{name_obj.get('first', '')} {name_obj.get('last', '')}".strip()
            # Build an OpenStates-shaped dict so downstream code needs no changes
            house_members.append({
                "name": full_name,
                "party": party,
                "image": f"https://unitedstates.github.io/images/congress/225x275/{m.get('id', {}).get('bioguide', '')}.jpg",
                "email": "",
                "current_role": {
                    "title": "U.S. Representative",
                    "org_classification": "lower",
                    "district": f"{state_abbr}-{district}",
                },
                "jurisdiction": {"classification": "country", "name": state_name},
            })
        return house_members
    except Exception:
        return []

# Backwards-compatible alias
def get_nc_federal_members() -> list:
    return get_federal_house_members("NC")

def build_rep_lookup(reps: list, federal: bool = False) -> dict:
    lookup = {}
    for rep in reps:
        roles = rep.get("current_role", {}) or {}
        dist  = str(roles.get("district", "")).strip()
        # Strip any state prefix (e.g. "NC-14" → "14", "NC-" → "")
        dist = re.sub(r"^[A-Z]{2}-", "", dist.upper()).strip()
        # Extract the numeric part and convert to int then str to drop leading zeros
        # e.g. "037" → "37", "014" → "14", "14" → "14"
        m = re.search(r"\d+", dist)
        key = str(int(m.group())) if m else dist
        if key:
            lookup[key] = rep
    return lookup

@st.cache_data(ttl=3600, show_spinner=False)
def get_bill_summary(bill_id: str, title: str, latest_action: str) -> str:
    if not GEMINI_KEY:
        return "⚠️ Gemini API key not set."
    prompt = f"""You are a nonpartisan civic education assistant for a voter app.

Summarize this North Carolina bill in 2-3 plain English sentences that a first-time voter can understand.
Be strictly factual and nonpartisan. Do not editorialize or take sides.

Bill: {title}
Latest action: {latest_action}

Respond with only the summary — no intro, no labels, no markdown."""
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": GEMINI_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 500},
            },
            timeout=20,
        )
        if r.status_code != 200:
            return f"⚠️ Gemini error {r.status_code}"
        parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# ── Bill Tracker ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_state_bills(state_abbr: str, query: str = "", chamber: str = "All") -> tuple:
    """Returns (list_of_bills, error_message)"""
    jurisdiction = (state_abbr or DEFAULT_STATE).lower()
    params: dict = {"jurisdiction": jurisdiction, "per_page": 20, "sort": "updated_desc"}
    if query.strip():
        params["q"] = query.strip()
    if chamber == "House":
        params["chamber"] = "lower"
    elif chamber == "Senate":
        params["chamber"] = "upper"
    try:
        r = requests.get(
            "https://v3.openstates.org/bills",
            params=params,
            headers={"X-API-KEY": OPENSTATES_KEY},
            timeout=15
        )
        if r.status_code == 200:
            return r.json().get("results", []), ""
        return [], f"HTTP {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return [], str(e)

# Backwards-compatible alias
def get_nc_bills(query: str = "", chamber: str = "All") -> tuple:
    return get_state_bills("NC", query, chamber)

# ── Candidates — powered by Gemini 1.5 Flash + Google Search (FREE) ──────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_candidate_info(race: str) -> str:
    if not GEMINI_KEY:
        return _candidate_info_fallback(race)

    prompt = f"""You are a nonpartisan civic information assistant for CivicLens, a voter education app.

Search and find all major candidates running in the 2026 North Carolina {race} election.

For each candidate provide:
1. Full name and party affiliation
2. Their main opponent(s) and those opponents' parties
3. Top 4-5 policy positions from their official campaign website
4. Official campaign website URL if available

Return your ENTIRE response as pure HTML — no markdown, no code fences, just raw HTML.
Use this card structure for each candidate:

<div style="border-left:5px solid BORDER_COLOR; background:#f8f9fa; border-radius:8px; padding:1rem 1.25rem; margin-bottom:1rem;">
  <h4 style="margin:0 0 2px 0; font-family:sans-serif;">NAME <span style="font-size:0.78rem; padding:2px 10px; border-radius:20px; background:BADGE_BG; color:BADGE_FG; font-weight:600; margin-left:6px;">PARTY</span></h4>
  <p style="color:#555; font-size:0.88rem; margin:0 0 8px 0; font-family:sans-serif;">ROLE — Running against: OPPONENT(S)</p>
  <strong style="font-family:sans-serif;">Key Positions:</strong>
  <ul style="margin:6px 0 10px 20px; font-family:sans-serif; color:#333;">
    <li>POSITION 1</li>
    <li>POSITION 2</li>
    <li>POSITION 3</li>
  </ul>
  <a href="WEBSITE" target="_blank" style="font-size:0.85rem; font-family:sans-serif; color:#1a73e8;">🌐 Campaign Website</a>
</div>

Color guide:
- Democrat:   BORDER_COLOR=#1a73e8  BADGE_BG=#d6e4ff  BADGE_FG=#1a3c8f
- Republican: BORDER_COLOR=#c0392b  BADGE_BG=#ffe0dd  BADGE_FG=#8b1a1a
- Other:      BORDER_COLOR=#7f8c8d  BADGE_BG=#e8e8e8  BADGE_FG=#444444

Be strictly factual and nonpartisan. List ALL major-party candidates."""

    try:
        for attempt in range(2):
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": GEMINI_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"google_search": {}}],
                    "generationConfig": {"temperature": 0.1}
                },
                timeout=45
            )
            if r.status_code == 503:
                if attempt == 0:
                    time.sleep(4)
                    continue
                raise Exception("Gemini 503")
            if r.status_code != 200:
                raise Exception(f"Gemini {r.status_code}: {r.text[:200]}")

            data  = r.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            html  = "".join(p.get("text", "") for p in parts if "text" in p)
            html  = re.sub(r"```html?\n?|```\n?", "", html).strip()
            if html:
                return html
            raise Exception("Gemini returned empty")

    except Exception:
        return None  #

def _candidate_info_fallback(race: str) -> str:
    """Groq (Llama 3.3 70B) + Tavily search — runs when Gemini is down."""
    if not GROQ_KEY or not TAVILY_KEY:
        return '<p style="color:#c0392b;">⚠️ Gemini is currently overloaded and no fallback keys are configured. Please try again in a minute.</p>'

    # Step 1 — Tavily search for live candidate data
    try:
        # First search: who's running
        search_r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": f"2026 North Carolina {race} election candidates",
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=20
        )
        search_data    = search_r.json()
        search_context = search_data.get("answer", "")
        for result in search_data.get("results", []):
            search_context += f"\n\nSource: {result.get('title')}\n{result.get('content', '')}"

        # Second search: policy positions and campaign websites
        policy_r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": f"2026 North Carolina {race} candidates policy positions issues campaign website",
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=20
        )
        policy_data = policy_r.json()
        search_context += "\n\n" + policy_data.get("answer", "")
        for result in policy_data.get("results", []):
            search_context += f"\n\nSource: {result.get('title')}\n{result.get('content', '')}"

    except Exception as e:
        return f'<p style="color:#c0392b;">⚠️ Search unavailable: {e}. Please try again.</p>'

    # Step 2 — Groq summarizes the search results
    prompt = f"""Based on the search results below, find all major candidates running in the 2026 North Carolina {race} election.

SEARCH RESULTS:
{search_context[:8000]}

For each candidate provide:
1. Full name and party affiliation
2. Their main opponent(s) and those opponents' parties
3. 6-8 detailed policy positions with 2-3 sentences of explanation for each — infer from their party platform and any available info if their site isn't in the results
4. A 3-4 sentence biography covering their background, career, and why they're running
5. Official campaign website URL if available — search for it in the results, otherwise omit the link entirely

Important: Never write "Not available" for positions. If you cannot find specific positions, write what this type of candidate typically supports based on their party and the race they're running in. Be specific — not just "supports lower taxes" but WHY and HOW they propose to do it.

Return your ENTIRE response as pure HTML using this card structure for each candidate:

<div style="border-left:5px solid BORDER_COLOR; background:#f8f9fa; border-radius:8px; padding:1rem 1.25rem; margin-bottom:1rem;">
  <h4 style="margin:0 0 2px 0; font-family:sans-serif;">NAME <span style="font-size:0.78rem; padding:2px 10px; border-radius:20px; background:BADGE_BG; color:BADGE_FG; font-weight:600; margin-left:6px;">PARTY</span></h4>
  <p style="color:#555; font-size:0.88rem; margin:0 0 8px 0; font-family:sans-serif;">ROLE — Running against: OPPONENT(S)</p>
  <p style="font-family:sans-serif; font-size:0.9rem; color:#333; margin:0 0 10px 0;">BIO HERE</p>
  <strong style="font-family:sans-serif;">Key Positions:</strong>
  <ul style="margin:6px 0 10px 20px; font-family:sans-serif; color:#333;">
    <li><strong>ISSUE 1:</strong> Detailed explanation here.</li>
    <li><strong>ISSUE 2:</strong> Detailed explanation here.</li>
    <li><strong>ISSUE 3:</strong> Detailed explanation here.</li>
    <li><strong>ISSUE 4:</strong> Detailed explanation here.</li>
    <li><strong>ISSUE 5:</strong> Detailed explanation here.</li>
    <li><strong>ISSUE 6:</strong> Detailed explanation here.</li>
  </ul>
  <a href="WEBSITE" target="_blank" style="font-size:0.85rem; font-family:sans-serif; color:#1a73e8;">🌐 Campaign Website</a>
</div>

Color guide:
- Democrat:   BORDER_COLOR=#1a73e8  BADGE_BG=#d6e4ff  BADGE_FG=#1a3c8f
- Republican: BORDER_COLOR=#c0392b  BADGE_BG=#ffe0dd  BADGE_FG=#8b1a1a
- Other:      BORDER_COLOR=#7f8c8d  BADGE_BG=#e8e8e8  BADGE_FG=#444444

Be strictly factual and nonpartisan."""
    try:
        groq_r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a nonpartisan civic information assistant. You output ONLY raw HTML — no greetings, no markdown, no explanations, no code fences. Your entire response must be HTML starting with a <div> tag."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            timeout=30
        )
        html = groq_r.json()["choices"][0]["message"]["content"]
        html = re.sub(r"```html?\n?|```\n?", "", html).strip()

        if not html:
            raw = groq_r.json()["choices"][0]["message"]["content"]
            return f'<pre style="font-size:0.75rem">{raw[:500]}</pre>'

        return html
    except Exception as e:
        return f'<p style="color:#c0392b;">⚠️ Backup also failed: {e}. Please try again in a minute.</p>'
# ─────────────────────────────────────────────
# SIDEBAR NAV
# ─────────────────────────────────────────────
menu = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "📍 Polling Finder",
        "📅 Deadlines",
        "🏛️ My Representatives",
        "🗺️ Rep Map",
        "📋 Bill Tracker",
        "🔍 District Compare",
        "🗳️ Candidates",
    ]
)

# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
if menu == "🏠 Home":
    st.title("🗳️ CivicLens")
    st.subheader("Your complete guide to voting and civic life in North Carolina")
    st.markdown("""
    Welcome! CivicLens helps **first-time and new voters** across North Carolina navigate every part of the civic process.

    | Tab | What it does |
    |---|---|
    | 📍 **Polling Finder** | Locate your polling place by address — any U.S. state |
    | 📅 **Deadlines** | Election Day + your state's registration & voting resources |
    | 🏛️ **My Representatives** | Every rep who represents you — state and federal |
    | 🗺️ **Rep Map** | Interactive NC district map colored by party |
    | 📋 **Bill Tracker** | Browse and search active NC legislation |
    | 🔍 **District Compare** | Compare reps for two addresses side by side |
    | 🗳️ **Candidates** | Live candidate research with policy positions |

    **Get started →** pick any section on the left and enter your NC address.
    """)
    st.caption("Data: OpenStates · U.S. Census TIGERweb · Google Civic API · Google Gemini AI")

# ─────────────────────────────────────────────
# POLLING FINDER
# ─────────────────────────────────────────────
elif menu == "📍 Polling Finder":
    st.header("📍 Find Your Polling Place")
    st.caption("Works for any U.S. address — powered by the Google Civic Information API.")
    address = st.text_input("Enter your full address (e.g. 123 Main St, Charlotte, NC 28201)")

    if st.button("Search", type="primary"):
        if not address.strip():
            st.error("Please enter an address.")
        else:
            with st.spinner("Looking up your polling place…"):
                data = get_voter_info(address)
                _, _, detected_state = geocode(address)

            state_info = STATES.get(detected_state, {})
            state_name = state_info.get("name", "")

            show_searched_address(address)

            if "pollingLocations" in data and data["pollingLocations"]:
                loc  = data["pollingLocations"][0]
                addr = loc.get("address", {})
                st.success("✅ Polling location found!")
                st.markdown(f"""
                <div class="info-box">
                    <strong>{addr.get('locationName', 'Polling Location')}</strong><br>
                    {addr.get('line1', '')}<br>
                    {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}
                </div>
                """, unsafe_allow_html=True)
                hours = loc.get("pollingHours", "")
                if hours:
                    st.caption(f"🕐 Hours: {hours}")
            else:
                st.warning("Polling location not available right now — no active election. Use these resources:")

            # Prefer any official links Google's Civic API returns for this
            # address's state administration body; fall back to our curated list.
            admin_bodies = (data.get("state") or [{}])[0].get("electionAdministrationBody", {}) if data.get("state") else {}
            civic_links = [
                ("Voting Location Finder", admin_bodies.get("votingLocationFinderUrl")),
                ("Register to Vote", admin_bodies.get("electionRegistrationUrl")),
                ("Absentee / Mail Voting Info", admin_bodies.get("absenteeVotingInfoUrl")),
                ("Ballot Information", admin_bodies.get("ballotInfoUrl")),
            ]
            civic_links = [(label, url) for label, url in civic_links if url]

            st.subheader(f"🗳️ {state_name + ' ' if state_name else ''}Voting Resources")
            links_to_show = civic_links if civic_links else get_official_resources(detected_state)
            for label, url in links_to_show:
                st.markdown(f"- [{label}]({url})")

# ─────────────────────────────────────────────
# DEADLINES
# ─────────────────────────────────────────────
elif menu == "📅 Deadlines":
    st.header("📅 Key Voting Deadlines — 2026")
    st.caption("Election Day itself is set federally — the same date nationwide. "
               "Registration and early-voting windows are set by each state, so enter your address below to see yours.")

    dl_address = st.text_input("Enter your address", key="dl_address")

    dl_state = None
    if dl_address.strip():
        with st.spinner("Locating address…"):
            _, _, dl_state = geocode(dl_address)
        if not dl_state:
            st.warning("Could not determine the state for that address — try adding your city and zip code.")

    dl_state_name = STATES.get(dl_state, {}).get("name", "")

    show_searched_address(dl_address)

    st.markdown(f"""
    <div class="rep-card other">
        <strong>Election Day</strong><br>
        📅 <em>November 3, 2026</em><br>
        <span style="color:#555;font-size:0.9rem">Polls open per your state and county's posted hours. Set by federal law — the same date nationwide.</span>
    </div>
    """, unsafe_allow_html=True)

    if not dl_state:
        st.info("Enter your address above to see registration and early-voting resources for your state.")
    elif dl_state == "NC":
        st.markdown(f'<p class="section-label">🏛️ {dl_state_name} 2026 Deadlines</p>', unsafe_allow_html=True)
        deadlines = [
            ("Voter Registration Deadline",          "October 11, 2026",    "Register online, by mail, or in person."),
            ("Same-Day Registration (Early Voting)",  "During early voting", "Register and vote at your early voting site."),
            ("Early Voting Begins",                   "October 15, 2026",   "No excuse needed in NC."),
            ("Early Voting Ends",                     "November 1, 2026",   "Last day to vote early."),
            ("Absentee Ballot Request Deadline",      "October 29, 2026",   "Request must be received by this date."),
        ]
        for name, date, note in deadlines:
            st.markdown(f"""
            <div class="rep-card other">
                <strong>{name}</strong><br>
                📅 <em>{date}</em><br>
                <span style="color:#555;font-size:0.9rem">{note}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('<p class="section-label">🗳️ Official Resources</p>', unsafe_allow_html=True)
        for label, url in get_official_resources(dl_state):
            st.markdown(f"- [{label}]({url})")
        st.caption(f"Always verify deadlines directly with {dl_state_name}'s official election authority — rules can change.")
    else:
        st.info(
            f"Registration cutoffs, early-voting windows, and absentee deadlines for **{dl_state_name}** "
            f"vary and can change year to year, so we don't guess at exact dates here — use the official "
            f"links below to get {dl_state_name}'s current 2026 deadlines."
        )
        st.markdown('<p class="section-label">🗳️ Official Resources</p>', unsafe_allow_html=True)
        for label, url in get_official_resources(dl_state):
            st.markdown(f"- [{label}]({url})")
        st.caption(f"Always verify deadlines directly with {dl_state_name}'s official election authority — rules can change.")

# ─────────────────────────────────────────────
# MY REPRESENTATIVES
# ─────────────────────────────────────────────
elif menu == "🏛️ My Representatives":
    st.header("🏛️ Who Represents You?")
    st.caption("Shows your state legislators AND your federal representatives in Congress — for any U.S. address.")
    address = st.text_input("Enter your address", placeholder="123 Main St, Charlotte, NC 28201")

    if st.button("Find My Reps", type="primary"):
        if not address.strip():
            st.error("Please enter an address.")
        else:
            with st.spinner("Locating address…"):
                lat, lng, detected_state = geocode(address)

            if lat is None:
                st.error("Could not locate that address. Try adding your city and zip code.")
            else:
                state_name = STATES.get(detected_state, {}).get("name", "")
                show_searched_address(address)
                if state_name:
                    st.caption(f"Detected state: **{state_name}**")

                with st.spinner("Loading your representatives…"):
                    all_reps = get_reps_by_location(lat, lng)

                if not all_reps:
                    st.warning("Could not load representatives for this address.")
                else:
                    federal_reps = [r for r in all_reps if is_federal(r)]
                    state_reps   = [r for r in all_reps if is_state(r)]

                    # Governor card is currently only populated for North Carolina.
                    # For other states we skip it rather than show incorrect info —
                    # a live per-state governor lookup is a follow-up step.
                    if detected_state == "NC":
                        st.markdown('<p class="section-label">🏛️ Governor of North Carolina</p>', unsafe_allow_html=True)
                        st.markdown("""
                        <div class="rep-card democrat">
                            <strong style="font-size:1.05rem">Josh Stein</strong>
                            <span class="party-badge badge-democrat">Democrat</span><br>
                            <span style="color:#555;font-size:0.88rem">Governor — North Carolina</span><br>
                            🌐 <a href="https://governor.nc.gov" target="_blank">governor.nc.gov</a>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f'<p class="section-label">🇺🇸 U.S. Senate{" — " + state_name if state_name else ""}</p>', unsafe_allow_html=True)
                    us_senators = [r for r in federal_reps if (r.get("current_role") or {}).get("org_classification") == "upper"]
                    for rep in us_senators:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:#555;font-size:0.88rem">U.S. Senator{" — " + state_name if state_name else ""}</span><br>
                                {"📧 <a href='" + email + "' target='_blank'>Contact</a>" if email else ""}
                            </div>""", unsafe_allow_html=True)

                    st.markdown('<p class="section-label">🇺🇸 U.S. House of Representatives</p>', unsafe_allow_html=True)
                    us_house = [r for r in federal_reps if (r.get("current_role") or {}).get("org_classification") == "lower"]
                    for rep in us_house:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        label = get_chamber_label(rep)
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:#555;font-size:0.88rem">{label}</span><br>
                                {"📧 <a href='" + email + "' target='_blank'>Contact</a>" if email else ""}
                            </div>""", unsafe_allow_html=True)

                    st.markdown(f'<p class="section-label">🏛️ {state_name or "State"} Senate</p>', unsafe_allow_html=True)
                    nc_senate = [r for r in state_reps if (r.get("current_role") or {}).get("org_classification") == "upper"]
                    for rep in nc_senate:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        label = get_chamber_label(rep)
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:#555;font-size:0.88rem">{label}</span><br>
                                {"📧 <a href='mailto:" + email + "'>" + email + "</a>" if email and not email.startswith("http") else ""}
                            </div>""", unsafe_allow_html=True)

                    st.markdown(f'<p class="section-label">🏛️ {state_name or "State"} House of Representatives</p>', unsafe_allow_html=True)
                    nc_house = [r for r in state_reps if (r.get("current_role") or {}).get("org_classification") == "lower"]
                    for rep in nc_house:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        label = get_chamber_label(rep)
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:#555;font-size:0.88rem">{label}</span><br>
                                {"📧 <a href='mailto:" + email + "'>" + email + "</a>" if email and not email.startswith("http") else ""}
                            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# REP MAP — FIX #5: st.status loading
# ─────────────────────────────────────────────
elif menu == "🗺️ Rep Map":
    st.header("🗺️ District Map")
    st.caption("Real district boundaries from the U.S. Census Bureau, colored by party. Click any district for rep details.")

    if st.button("🔄 Clear map cache", help="Force re-fetch boundaries from Census — use if districts look wrong"):
        st.cache_data.clear()
        st.success("Cache cleared — click Show Map to reload.")

    col_addr, col_state = st.columns([3, 1])
    with col_addr:
        address = st.text_input("Enter your address (optional — pins your location and auto-selects the state below)")
    with col_state:
        state_abbrs = sorted(STATES.keys())
        manual_state = st.selectbox(
            "State", state_abbrs,
            index=state_abbrs.index(DEFAULT_STATE),
            help="Auto-overridden if your address above resolves to a different state.",
        )

    st.markdown("**Show district layer:**")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: show_gov      = st.checkbox("Governor",    value=True)
    with col2: show_us_sen   = st.checkbox("U.S. Senate", value=False)
    with col3: show_us_house = st.checkbox("U.S. House",  value=False)
    with col4: show_nc_sen   = st.checkbox("NC Senate",   value=False)
    with col5: show_nc_house = st.checkbox("NC House",    value=False)

    if st.button("Show Map", type="primary"):
        with st.status("Loading district data…", expanded=True) as load_status:
            st.write("📡 Geocoding address…")
            lat, lng, detected_state = None, None, None
            if address.strip():
                lat, lng, detected_state = geocode(address)

            # Address-detected state wins; otherwise fall back to the manual picker.
            state_abbr = detected_state or manual_state
            state_info = STATES.get(state_abbr, STATES[DEFAULT_STATE])
            state_fips = state_info["fips"]
            state_name = state_info["name"]
            if detected_state and detected_state != manual_state:
                st.write(f"📍 Address resolved to **{state_name}** — using that state.")

            st.write(f"🗺️ Fetching Census district boundaries for {state_name}…")
            geojson_us_house  = fetch_tiger_geojson(LAYER_US_HOUSE, state_fips, state_abbr)     if show_us_house else {}
            geojson_nc_senate = fetch_tiger_geojson(LAYER_STATE_SENATE, state_fips, state_abbr) if show_nc_sen   else {}
            geojson_nc_house  = fetch_tiger_geojson(LAYER_STATE_HOUSE, state_fips, state_abbr)  if show_nc_house else {}

            st.write("👥 Loading representative data…")
            nc_senate_reps, nc_senate_err = get_state_reps_by_chamber(state_abbr, "upper") if show_nc_sen   else ([], "")
            nc_house_reps,  nc_house_err  = get_state_reps_by_chamber(state_abbr, "lower") if show_nc_house else ([], "")
            us_house_reps  = get_federal_house_members(state_abbr)                        if show_us_house else []

            lookup_nc_senate = build_rep_lookup(nc_senate_reps)
            lookup_nc_house  = build_rep_lookup(nc_house_reps)
            lookup_us_house  = build_rep_lookup(us_house_reps, federal=True)
            load_status.update(label="✅ Map data loaded!", state="complete", expanded=False)

        # Surface rep-load failures (st.warning not allowed inside cached functions)
        if show_nc_sen and not nc_senate_reps:
            st.warning(f"⚠️ Could not load {state_name} Senate representatives. Boundaries will show without rep names.")
        if show_nc_house and not nc_house_reps:
            st.warning(f"⚠️ Could not load {state_name} House representatives. Boundaries will show without rep names.")
        if show_us_house and not us_house_reps:
            st.warning("⚠️ Could not load U.S. House representatives. Boundaries will show without rep names.")

        show_searched_address(address)

        if lat:
            center, zoom = [lat, lng], 11
        else:
            # No address given — center on the selected state instead of always NC.
            fallback_lat, fallback_lng, _ = geocode(f"{state_name}, USA")
            center = [fallback_lat, fallback_lng] if fallback_lat else [35.5, -79.5]
            zoom = 7
        m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

        # Fetch the selected state's outline once and reuse for both Governor and US Senate overlays.
        # Using a stable GitHub-hosted GeoJSON instead of the shifting TIGERweb State_County layer.
        state_outline_geo = None
        if show_gov or show_us_sen:
            try:
                all_states_geo = requests.get(US_STATES_GEOJSON_URL, timeout=15).json()
                state_feature = next(
                    (f for f in all_states_geo.get("features", [])
                     if f.get("properties", {}).get("name") == state_name),
                    None
                )
                if state_feature:
                    state_outline_geo = {"type": "FeatureCollection", "features": [state_feature]}
            except Exception:
                pass

        # NOTE: Governor and U.S. Senate names/parties below are only populated for
        # North Carolina. For other states we still draw the outline layer but skip
        # the name/party popup rather than show incorrect information — live
        # per-state governor/senator lookups are a follow-up step.
        if show_gov:
            try:
                gov_fg = folium.FeatureGroup(name="Governor", show=True)
                if state_abbr == "NC":
                    popup_html = """
                    <div style="font-family:sans-serif;min-width:200px">
                        <strong>Josh Stein</strong><br>
                        <em style="color:#555">Governor of North Carolina</em><br>
                        <span style="color:#1a73e8;font-weight:600">Democrat</span><br>
                        <a href="https://governor.nc.gov" target="_blank">governor.nc.gov</a>
                    </div>"""
                    tooltip = "Governor: Josh Stein (Democrat)"
                else:
                    popup_html = f"""
                    <div style="font-family:sans-serif;min-width:200px">
                        <strong>Governor of {state_name}</strong><br>
                        <span style="color:#888;font-size:0.85rem">Name/party lookup for this state coming soon.</span>
                    </div>"""
                    tooltip = f"Governor of {state_name}"
                for feature in (state_outline_geo or {}).get("features", []):
                    folium.GeoJson(
                        feature,
                        style_function=lambda f: {"fillColor": "#1a73e8", "fillOpacity": 0.08, "color": "#1a73e8", "weight": 2, "dashArray": "6 4"},
                        highlight_function=lambda f: {"fillColor": "#1a73e8", "fillOpacity": 0.20, "color": "#1a73e8", "weight": 2, "dashArray": "6 4"},
                        tooltip=tooltip,
                        popup=folium.Popup(popup_html, max_width=260),
                    ).add_to(gov_fg)
                gov_fg.add_to(m)
            except Exception:
                pass

        if show_us_sen:
            try:
                sen_fg = folium.FeatureGroup(name="U.S. Senate", show=True)
                if state_abbr == "NC":
                    popup_html = """
                    <div style="font-family:sans-serif;min-width:210px">
                        <strong>NC U.S. Senators</strong><br><br>
                        <img src='https://unitedstates.github.io/images/congress/450x550/T000476.jpg' width='45' style='border-radius:50%;margin-right:6px'/>
                        <strong>Thom Tillis</strong> <span style="color:#c0392b">Republican</span><br>
                        <a href="https://www.tillis.senate.gov" target="_blank">tillis.senate.gov</a><br><br>
                        <img src='https://unitedstates.github.io/images/congress/450x550/B001305.jpg' width='45' style='border-radius:50%;margin-right:6px'/>
                        <strong>Ted Budd</strong> <span style="color:#c0392b">Republican</span><br>
                        <a href="https://www.budd.senate.gov" target="_blank">budd.senate.gov</a>
                    </div>"""
                    tooltip = "U.S. Senators: Tillis & Budd (Republican)"
                else:
                    popup_html = f"""
                    <div style="font-family:sans-serif;min-width:210px">
                        <strong>{state_name} U.S. Senators</strong><br>
                        <span style="color:#888;font-size:0.85rem">Name/party lookup for this state coming soon.</span>
                    </div>"""
                    tooltip = f"U.S. Senators for {state_name}"
                for feature in (state_outline_geo or {}).get("features", []):
                    folium.GeoJson(
                        feature,
                        style_function=lambda f: {"fillColor": "#c0392b", "fillOpacity": 0.08, "color": "#c0392b", "weight": 2, "dashArray": "6 4"},
                        highlight_function=lambda f: {"fillColor": "#c0392b", "fillOpacity": 0.20, "color": "#c0392b", "weight": 2, "dashArray": "6 4"},
                        tooltip=tooltip,
                        popup=folium.Popup(popup_html, max_width=260),
                    ).add_to(sen_fg)
                sen_fg.add_to(m)
            except Exception:
                pass

        if show_us_house and geojson_us_house:
            build_district_layer(geojson_us_house, lookup_us_house, "U.S. House",  district_field="CD119").add_to(m)
        if show_nc_sen and geojson_nc_senate:
            build_district_layer(geojson_nc_senate, lookup_nc_senate, "NC Senate", district_field="SLDU").add_to(m)
        if show_nc_house and geojson_nc_house:
            build_district_layer(geojson_nc_house, lookup_nc_house, "NC House",    district_field="SLDL").add_to(m)

        if lat:
            folium.Marker(
                location=[lat, lng], popup="📍 Your Address", tooltip="You are here",
                icon=folium.Icon(color="black", icon="home", prefix="fa"),
            ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        st.markdown("""
        <div class="map-legend">
            <strong style="font-size:0.85rem">Party Key:</strong>
            <div class="legend-item"><span class="legend-dot" style="background:#1a73e8"></span> Democrat</div>
            <div class="legend-item"><span class="legend-dot" style="background:#c0392b"></span> Republican</div>
            <div class="legend-item"><span class="legend-dot" style="background:#888"></span> Other / Unknown</div>
            <span style="font-size:0.78rem;color:#888;margin-left:auto">Click any district for rep details</span>
        </div>
        """, unsafe_allow_html=True)
        st_folium(m, width=950, height=580, returned_objects=[])
        st.caption("District boundaries: U.S. Census Bureau TIGERweb · Rep data: OpenStates API")

# ─────────────────────────────────────────────
# BILL TRACKER
# ─────────────────────────────────────────────
elif menu == "📋 Bill Tracker":
    st.header("📋 State Bill Tracker")
    st.caption("Browse and search active state legislation for any state · Via OpenStates · Updated every 30 min")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input("Search by keyword", placeholder="e.g. school funding, gun safety, Medicaid")
    with col2:
        chamber = st.selectbox("Chamber", ["All", "House", "Senate"])
    with col3:
        bill_state_abbrs = sorted(STATES.keys())
        bill_state = st.selectbox("State", bill_state_abbrs, index=bill_state_abbrs.index(DEFAULT_STATE), key="bill_state")

    search_clicked = st.button("Search Bills", type="primary")

    if "bills" not in st.session_state or search_clicked:
        load_query   = query      if search_clicked else ""
        load_chamber = chamber    if search_clicked else "All"
        load_state   = bill_state if search_clicked else DEFAULT_STATE
        with st.spinner("Loading bills…"):
            bills_result, bills_err = get_state_bills(load_state, query=load_query, chamber=load_chamber)
            st.session_state.bills     = bills_result
            st.session_state.bills_err = bills_err

    bills     = st.session_state.get("bills", [])
    bills_err = st.session_state.get("bills_err", "")

    if bills_err:
        st.error(f"Could not load bills — {bills_err}")
    elif not bills:
        st.info("No bills found. Try a different keyword or chamber.")
    else:
        st.caption(f"Showing {len(bills)} bills — sorted by most recent activity")
        for bill in bills:
            identifier  = bill.get("identifier", "—")
            title       = bill.get("title", "No title")
            latest_act  = bill.get("latest_action_description", "No recent action")
            latest_date = (bill.get("latest_action_date") or "")[:10]
            url         = bill.get("openstates_url", "#")
            bill_id     = bill.get("id", identifier)
            subjects    = (bill.get("subject") or [])[:3]
            sponsors    = bill.get("sponsorships", [])
            primary     = next((s for s in sponsors if s.get("primary")), None)
            sponsor_name  = (primary or {}).get("name", "Unknown")
            sponsor_party = (primary or {}).get("party", "")
            css           = party_css(sponsor_party)
            tags_html     = "".join(f'<span class="subject-tag">{s}</span>' for s in subjects)
            st.markdown(f"""
            <div class="rep-card {css}" style="padding:0.85rem 1.1rem">
                <strong>{identifier}</strong>
                <span style="color:#222;font-size:0.97rem"> — {title}</span><br>
                <span style="color:#555;font-size:0.83rem">
                    👤 {sponsor_name}{' (' + sponsor_party + ')' if sponsor_party else ''}
                    &nbsp;·&nbsp; 📅 {latest_date}
                    &nbsp;·&nbsp; {latest_act}
                </span>
                {"<br>" + tags_html if tags_html else ""}
                <br><a href="{url}" target="_blank" style="font-size:0.8rem;color:#1a73e8;">View full bill on OpenStates →</a>
            </div>
            """, unsafe_allow_html=True)

            summary_key = f"summary_{bill_id}"
            if st.button("✨ Plain-English Summary", key=f"btn_{bill_id}"):
                with st.spinner("Summarizing…"):
                    st.session_state[summary_key] = get_bill_summary(bill_id, title, latest_act)
            if summary_key in st.session_state:
                st.info(f"💡 {st.session_state[summary_key]}")

# ─────────────────────────────────────────────
# DISTRICT COMPARE
# ─────────────────────────────────────────────
elif menu == "🔍 District Compare":
    st.header("🔍 District Comparison")
    st.caption("Enter two NC addresses to compare their representatives side by side. Shared reps are highlighted in green.")

    col1, col2 = st.columns(2)
    with col1:
        addr1 = st.text_input("📍 Address 1", placeholder="123 Main St, Charlotte, NC 28201", key="dc_addr1")
    with col2:
        addr2 = st.text_input("📍 Address 2", placeholder="456 Oak Ave, Raleigh, NC 27601",   key="dc_addr2")

    if st.button("Compare Districts", type="primary"):
        if not addr1.strip() or not addr2.strip():
            st.error("Please enter both addresses.")
        else:
            with st.spinner("Looking up representatives for both addresses…"):
                lat1, lng1, state1 = geocode(addr1)
                lat2, lng2, state2 = geocode(addr2)
                reps1 = get_reps_by_location(lat1, lng1) if lat1 else []
                reps2 = get_reps_by_location(lat2, lng2) if lat2 else []

            if not lat1: st.error(f"Could not locate: **{addr1}**")
            if not lat2: st.error(f"Could not locate: **{addr2}**")

            if reps1 or reps2:
                ids1, ids2     = {r.get("id") for r in reps1}, {r.get("id") for r in reps2}
                shared_ids     = ids1 & ids2

                def rep_card_compare(rep: dict, shared: bool) -> str:
                    name  = rep.get("name", "Unknown")
                    party = rep.get("party", "Unknown")
                    label = get_chamber_label(rep)
                    photo = rep.get("image", "")
                    css, badge = party_css(party), party_badge(party)
                    shared_html = (
                        ' <span style="background:#d4edda;color:#155724;padding:1px 8px;'
                        'border-radius:10px;font-size:0.72rem;font-weight:600;">Shared</span>'
                    ) if shared else ""
                    img_html = f"<img src='{photo}' width='45' style='border-radius:50%;float:right;margin-left:8px'/>" if photo else ""
                    return f"""
                    <div class="rep-card {css}">
                        {img_html}
                        <strong>{name}</strong>{shared_html}
                        <span class="party-badge {badge}">{party}</span><br>
                        <span style="color:#555;font-size:0.85rem">{label}</span>
                    </div>"""

                def sort_reps(reps):
                    return sorted(reps, key=lambda r: (0 if is_federal(r) else 1, r.get("name", "")))

                left_col, right_col = st.columns(2)
                with left_col:
                    st.subheader(f"📍 {addr1[:45]}{'…' if len(addr1) > 45 else ''}")
                    if state1 and state1 in STATES:
                        st.caption(STATES[state1]["name"])
                    if reps1:
                        for rep in sort_reps(reps1):
                            st.markdown(rep_card_compare(rep, rep.get("id") in shared_ids), unsafe_allow_html=True)
                    else:
                        st.warning("No representatives found.")
                with right_col:
                    st.subheader(f"📍 {addr2[:45]}{'…' if len(addr2) > 45 else ''}")
                    if state2 and state2 in STATES:
                        st.caption(STATES[state2]["name"])
                    if reps2:
                        for rep in sort_reps(reps2):
                            st.markdown(rep_card_compare(rep, rep.get("id") in shared_ids), unsafe_allow_html=True)
                    else:
                        st.warning("No representatives found.")

                if shared_ids:
                    st.success(f"✅ These addresses share **{len(shared_ids)}** representative(s) — marked in green above.")
                elif reps1 and reps2:
                    st.info("These addresses have entirely separate sets of representatives.")

# ─────────────────────────────────────────────
# CANDIDATES
# ─────────────────────────────────────────────
elif menu == "🗳️ Candidates":
    st.header("🗳️ 2026 NC Candidates")
    st.caption("Powered by Google Gemini 2.5 Flash + Groq + Tavily + Google Search — free, nonpartisan, live from official campaign websites")

    race_options = {
        "Governor":                           "Governor",
        "U.S. Senate":                        "U.S. Senate",
        "U.S. House (enter district below)":  "U.S. House",
        "NC Senate (enter district below)":   "NC Senate",
        "NC House (enter district below)":    "NC House",
    }
    race_label = st.selectbox("Select Race", list(race_options.keys()))
    race_type  = race_options[race_label]
    needs_district = "enter district" in race_label

    district = ""
    if needs_district:
        district = st.text_input("District Number", placeholder="e.g. 14 for NC-14")

    if st.button("Find Candidates & Positions", type="primary", key="candidates_btn"):
        clean_race = race_type
        if district.strip():
            clean_race = f"{race_type} District {district.strip()}"

        if needs_district and not district.strip():
            st.error("Please enter a district number for this race type.")
        else:
            with st.spinner(f"Searching for 2026 {clean_race} candidates — may take 15–30 seconds…"):
                if not rate_limit_check("gemini_calls", max_calls=5, window=60):
                    st.toast("⚡ Gemini limit reached, switching to backup…", icon="🔄")
                    html_output = _candidate_info_fallback(clean_race)
                else:
                    html_output = get_candidate_info(clean_race)
                    if html_output is None:
                        st.toast("⚡ Gemini unavailable, switching to backup…", icon="🔄")
                        html_output = _candidate_info_fallback(clean_race)

            st.markdown(html_output, unsafe_allow_html=True)
            st.caption(
                "⚠️ AI-assisted research from public web sources. "
                "Always verify with official campaign sites and [ncsbe.gov](https://www.ncsbe.gov). "
                "Results cached for 1 hour."
            )
# Privacy Policy and Terms of Use
with open("privacy-policy.html", "r") as f:
    privacy_html = f.read()
with open("terms-of-service.html", "r") as f:
    tos_html = f.read()

privacy_encoded = urllib.parse.quote(privacy_html)
tos_encoded = urllib.parse.quote(tos_html)

st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center;font-size:0.8rem;color:#888;padding:0.5rem 0 1rem">
    <a href="data:text/html,{privacy_encoded}" target="_blank" style="color:#1a73e8;text-decoration:none">Privacy Policy</a>
    &nbsp;·&nbsp;
    <a href="data:text/html,{tos_encoded}" target="_blank" style="color:#1a73e8;text-decoration:none">Terms of Service</a>
    &nbsp;·&nbsp; CivicLens is nonpartisan and not affiliated with any government agency.
    </div>
    """,
    unsafe_allow_html=True
)
