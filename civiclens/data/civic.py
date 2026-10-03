"""Google Civic Information API (elections, voter info) and official voting links."""
import requests
import streamlit as st

from civiclens.config import GOOGLE_KEY
from civiclens.states import DEFAULT_STATE, STATES

# Google only returns polling places for a tracked election, so find the current one
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
