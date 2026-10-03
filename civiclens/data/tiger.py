"""Census TIGERweb district boundaries."""
import re

import requests
import streamlit as st

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

class TigerFetchError(Exception):
    pass

# Robust TIGERweb fetch — tries every known where-clause variant for the given state.
# Raises on failure instead of returning {} so a failed load is never cached.
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_tiger_geojson_cached(layer_id: int, state_fips: str, state_abbr: str = "") -> dict:
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
    raise TigerFetchError(last_error or "empty response")

def fetch_tiger_geojson(layer_id: int, state_fips: str, state_abbr: str = "") -> tuple:
    """Returns (geojson, error_message). Uncached wrapper so failures are retried on the
    next click and the warning can be shown by the tab code (st.warning not allowed
    inside cached functions)."""
    try:
        return _fetch_tiger_geojson_cached(layer_id, state_fips, state_abbr), ""
    except TigerFetchError as e:
        return {}, str(e)

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
