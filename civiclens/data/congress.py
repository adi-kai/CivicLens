"""U.S. House and Senate rosters from the unitedstates/congress-legislators JSON."""
import requests
import streamlit as st

from civiclens.states import DEFAULT_STATE, STATES

CONGRESS_LEGISLATORS_URL = (
    "https://unitedstates.github.io/congress-legislators/legislators-current.json"
)
CONGRESS_PHOTO_URL = "https://unitedstates.github.io/images/congress/225x275/{bioguide}.jpg"

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_congress_legislators() -> list:
    """Every current member of Congress, straight from the source JSON. Cached on its own
    so the House and Senate lookups share a single download of this fairly large file."""
    try:
        r = requests.get(CONGRESS_LEGISLATORS_URL, timeout=15)
        if r.status_code != 200:
            return []
        return r.json()
    except Exception:
        return []

def latest_term(member: dict) -> dict:
    terms = member.get("terms", [])
    return terms[-1] if terms else {}

# Map party names congress-legislators uses to the ones OpenStates returns
CONGRESS_PARTY_MAP = {"Democrat": "Democratic", "Republican": "Republican",
                      "Independent": "Independent"}

@st.cache_data(ttl=3600, show_spinner=False)
def get_federal_house_members(state_abbr: str) -> list:
    """
    Fetch a given state's current U.S. House members.
    OpenStates' per-state roster endpoint (/people?jurisdiction=<state>) only lists
    state legislators, so a full state roster of House members can't come from there.
    (people.geo does include Congress, but only for a single point, not a whole state.)
    We use the unitedstates/congress-legislators JSON (public domain, no API key).
    Returns a list of dicts shaped like OpenStates people objects so the rest of
    the code (build_rep_lookup, get_chamber_label, party_fill, etc.) works unchanged.
    """
    state_abbr = (state_abbr or DEFAULT_STATE).upper()
    state_name = STATES.get(state_abbr, {}).get("name", state_abbr)
    try:
        members = _fetch_congress_legislators()
        if not members:
            return []
        house_members = []
        for m in members:
            latest = latest_term(m)
            if latest.get("type") != "rep":
                continue
            state = latest.get("state", "")
            if state != state_abbr:
                continue
            district = str(latest.get("district", ""))
            raw_party = latest.get("party", "Unknown")
            party = CONGRESS_PARTY_MAP.get(raw_party, raw_party)
            name_obj = m.get("name", {})
            full_name = f"{name_obj.get('first', '')} {name_obj.get('last', '')}".strip()
            # Build an OpenStates-shaped dict so downstream code needs no changes
            house_members.append({
                "name": full_name,
                "party": party,
                "image": CONGRESS_PHOTO_URL.format(bioguide=m.get("id", {}).get("bioguide", "")),
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

@st.cache_data(ttl=3600, show_spinner=False)
def get_federal_senators(state_abbr: str) -> list:
    """
    A state's two current U.S. Senators, senior senator first, from the same
    congress-legislators JSON the House roster uses. Shaped like OpenStates people
    objects (plus "url" and "phone") so card rendering and get_chamber_label work
    unchanged. DC has no senators, so this returns [] there.
    """
    state_abbr = (state_abbr or DEFAULT_STATE).upper()
    state_name = STATES.get(state_abbr, {}).get("name", state_abbr)
    senators = []
    for m in _fetch_congress_legislators():
        latest = latest_term(m)
        if latest.get("type") != "sen" or latest.get("state", "") != state_abbr:
            continue
        raw_party = latest.get("party", "Unknown")
        name_obj = m.get("name", {})
        full_name = (name_obj.get("official_full")
                     or f"{name_obj.get('first', '')} {name_obj.get('last', '')}").strip()
        senators.append({
            "name": full_name,
            "party": CONGRESS_PARTY_MAP.get(raw_party, raw_party),
            "image": CONGRESS_PHOTO_URL.format(bioguide=m.get("id", {}).get("bioguide", "")),
            "email": latest.get("contact_form", ""),
            "url": latest.get("url", ""),
            "phone": latest.get("phone", ""),
            "current_role": {
                "title": "U.S. Senator",
                "org_classification": "upper",
                # Senators have no district; get_chamber_label reads the state name from here
                "district": state_name,
            },
            "jurisdiction": {"classification": "country", "name": "United States"},
            "_rank": 0 if latest.get("state_rank") == "senior" else 1,
        })
    return sorted(senators, key=lambda s: (s["_rank"], s["name"]))
