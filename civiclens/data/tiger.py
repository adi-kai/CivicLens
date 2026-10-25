"""Census TIGERweb district boundaries."""
import requests
import streamlit as st

from civiclens.helpers import district_key

# TIGERweb's Legislative MapServer covers every state; you filter by FIPS code in the WHERE
# clause. Census adds new maps ahead of each election (the 120th Congress and 2026 legislative
# maps took over layers 0-2 in 2026), so the maps current members were elected on are found by
# name; these IDs are only the fallback if the layer list can't be read.
# Verify at: tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer
TIGER_BASE           = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
LAYER_US_HOUSE       = 4   # 119th Congressional Districts        (STATE field, district: CD119)
LAYER_STATE_SENATE   = 5   # 2024 State Legislative Upper/Senate  (STATE field, district: SLDU)
LAYER_STATE_HOUSE    = 6   # 2024 State Legislative Lower/House   (STATE field, district: SLDL)

CURRENT_LAYERS = {"us_house": ("119th Congressional Districts", LAYER_US_HOUSE),
                  "upper": ("2024 State Legislative Districts - Upper", LAYER_STATE_SENATE),
                  "lower": ("2024 State Legislative Districts - Lower", LAYER_STATE_HOUSE)}

# Stable GeoJSON with outlines for all 50 states + DC (avoids shifting TIGERweb State_County layer IDs)
US_STATES_GEOJSON_URL = (
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
)
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

@st.cache_data(ttl=86400, show_spinner=False)
def _current_layer_ids_cached() -> dict:
    layers = requests.get(TIGER_BASE, params={"f": "json"}, timeout=30).json().get("layers", [])
    # The first layer with each name; the MapServer repeats some names further down
    return {key: next(l["id"] for l in layers if l.get("name") == name)
            for key, (name, _) in CURRENT_LAYERS.items()}

def current_layer_ids() -> dict:
    """{"us_house": 4, "upper": 5, "lower": 6} — the layers for the maps current members were
    elected on; the fallback IDs if the layer list can't be read (not cached, so it's retried)."""
    try:
        return _current_layer_ids_cached()
    except Exception:
        return {key: layer_id for key, (_, layer_id) in CURRENT_LAYERS.items()}

@st.cache_data(ttl=86400, show_spinner=False)
def _districts_at_cached(lat: float, lng: float) -> dict:
    found = {}
    layer_ids = current_layer_ids()
    for chamber in ("upper", "lower"):
        layer_id = layer_ids[chamber]
        r = requests.get(f"{TIGER_BASE}/{layer_id}/query", params={
            "geometry": f"{lng},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "outFields": "BASENAME",
            "returnGeometry": "false", "f": "json"}, timeout=30)
        features = r.json().get("features", [])
        if features:
            found[chamber] = features[0]["attributes"].get("BASENAME", "")
    return found

def state_districts_at(lat: float, lng: float) -> dict:
    """{"upper": "38", "lower": "106"} — the state legislative districts (as Census names them)
    a point falls in on the maps current legislators were elected on; {} if TIGERweb fails."""
    try:
        return _districts_at_cached(lat, lng)
    except Exception:
        return {}

def extract_district_key(props: dict, district_field: str = "") -> str:
    """
    The feature's district as a district_key(), to match build_rep_lookup().
    BASENAME comes first: it's the district's name as the state writes it ("I", "Addison-1",
    "Hillsborough 10", "Third Middlesex"), which is how OpenStates spells it too. The code
    fields don't match for named districts (Alaska's SLDU is "00I", Vermont's "ADD",
    Massachusetts' "D15"), and CD119 has come back empty on the U.S. House layer.
    Pass district_field (CD119, SLDU, SLDL) as the next choice; legacy field names follow.
    """
    fields = ["BASENAME", district_field,
              "CD119", "CD119FP", "CD118", "CD118FP", "CDFP", "CD",
              "SLDU", "SLDUST", "SLDL", "SLDLST", "NAME"]
    for field in fields:
        key = district_key(props.get(field)) if field else ""
        if key:
            return key
    return ""

def is_undefined_area(props: dict) -> bool:
    """Census adds a shape for water that's in no district ("State House Districts not defined")."""
    return "NOT DEFINED" in str(props.get("BASENAME") or props.get("NAME") or "").upper()

def geojson_bounds(*geojsons) -> list:
    """[[south, west], [north, east]] around every feature, for folium's fit_bounds; [] if none.
    Alaska's western Aleutians cross the 180th meridian (positive longitudes), which would
    stretch the box around the whole world, so eastern-hemisphere points count as below -180."""
    lats, lngs = [], []

    def walk(coords):
        if coords and isinstance(coords[0], (int, float)):
            lng, lat = coords[0], coords[1]
            lngs.append(lng - 360 if lng > 0 else lng)
            lats.append(lat)
        else:
            for c in coords or []:
                walk(c)

    for geo in geojsons:
        for feature in (geo or {}).get("features", []):
            walk((feature.get("geometry") or {}).get("coordinates"))
    if not lats:
        return []
    return [[min(lats), min(lngs)], [max(lats), max(lngs)]]
