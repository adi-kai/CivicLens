"""Nominatim geocoding with state detection."""
import requests
import streamlit as st

from civiclens.states import STATES, STATE_NAME_TO_ABBR

# Cached for 24 hours. Also detects the state (USPS abbreviation) from the geocoded
# address so every downstream fetcher (map, reps, bills) knows which state to query
# without the user having to pick one manually.
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
