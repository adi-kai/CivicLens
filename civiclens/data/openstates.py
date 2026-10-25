"""OpenStates API v3: reps by location, state legislator rosters, and bills."""
import requests
import streamlit as st

from civiclens.config import OPENSTATES_KEY
from civiclens.data.tiger import state_districts_at
from civiclens.helpers import district_key
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
            return correct_state_districts(r.json().get("results", []), state_districts_at(lat, lng))
    except Exception:
        pass
    return []

def correct_state_districts(reps: list, census_districts: dict) -> list:
    """people.geo can match an address against an old map (in 2026 it still used North
    Carolina's 2018 Senate districts). Where Census's current map puts the address in a
    different district, that chamber's members are replaced with the district's members
    from the OpenStates roster; if that lookup finds no one, people.geo's answer stays."""
    for chamber, census_district in census_districts.items():
        in_chamber = [p for p in reps
                      if (p.get("jurisdiction") or {}).get("classification") == "state"
                      and (p.get("current_role") or {}).get("org_classification") == chamber]
        if not in_chamber or not census_district:
            continue
        if any(district_key(p["current_role"].get("district")) == district_key(census_district)
               for p in in_chamber):
            continue
        members = _district_members(in_chamber[0]["jurisdiction"]["id"], chamber, census_district)
        if members:
            reps = [p for p in reps if p not in in_chamber] + members
    return reps

def _district_members(jurisdiction: str, chamber: str, district: str) -> list:
    try:
        r = requests.get(
            "https://v3.openstates.org/people",
            params={"jurisdiction": jurisdiction, "org_classification": chamber, "district": district},
            headers={"X-API-KEY": OPENSTATES_KEY},
            timeout=15,
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
    for page in range(1, 11):  # up to 500 reps; New Hampshire's House alone has 400
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
            data = r.json()
            batch = data.get("results", [])
            results.extend(batch)
            # Asking past the last page is a 404, so a chamber of exactly 50 (NC's Senate)
            # has to stop on max_page rather than wait for a short page
            if len(batch) < 50 or page >= (data.get("pagination") or {}).get("max_page", page + 1):
                break  # last page
        except Exception as e:
            return results, str(e)
    return results, ""

# ── Bill Tracker ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_state_bills(state_abbr: str, query: str = "", chamber: str = "All") -> tuple:
    """Returns (list_of_bills, error_message)"""
    jurisdiction = (state_abbr or DEFAULT_STATE).lower()
    # Sponsorships aren't returned unless requested; the sponsor's party and title live on sponsorship["person"].
    # Abstracts are the official bill summaries the AI summary is built from (some states, e.g. NC, publish none).
    params: dict = {"jurisdiction": jurisdiction, "per_page": 20, "sort": "updated_desc",
                    "include": ["sponsorships", "abstracts"]}
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
