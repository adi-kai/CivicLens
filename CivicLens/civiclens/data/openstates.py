"""OpenStates API v3: reps by location, state legislator rosters, and bills."""
import requests
import streamlit as st

from civiclens.config import OPENSTATES_KEY
from civiclens.states import DEFAULT_STATE

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

# ── Bill Tracker ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_state_bills(state_abbr: str, query: str = "", chamber: str = "All") -> tuple:
    """Returns (list_of_bills, error_message)"""
    jurisdiction = (state_abbr or DEFAULT_STATE).lower()
    # Sponsorships aren't returned unless requested; the sponsor's party and title live on sponsorship["person"]
    params: dict = {"jurisdiction": jurisdiction, "per_page": 20, "sort": "updated_desc", "include": "sponsorships"}
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
