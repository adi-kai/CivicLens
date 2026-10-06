"""Google Civic Information API (elections, voter info) and official voting links."""
import requests
import streamlit as st

from civiclens.config import GOOGLE_KEY
from civiclens.i18n import t
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
def get_voter_info(address: str) -> dict:
    """Google's voterinfo response, or {"error": {"message": ...}} — the same shape Google
    uses for its own errors (e.g. "Election unknown" for a state whose data isn't loaded)."""
    try:
        return requests.get(
            "https://www.googleapis.com/civicinfo/v2/voterinfo",
            params={"address": address, "electionId": get_active_election_id(), "key": GOOGLE_KEY},
            timeout=20,
        ).json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def parse_ballot(data: dict) -> dict:
    """Pulls the ballot out of a voterinfo response:
    {"election": name, "day": ISO date, "races": [...], "measures": [...]}, both lists in
    ballot order. Google fills in contests state by state as election offices publish
    them through the Voting Information Project, so an empty result is normal early on."""
    def placement(contest):
        try:
            return int(contest.get("ballotPlacement", ""))
        except (TypeError, ValueError):
            return 10_000

    races, measures = [], []
    for c in sorted(data.get("contests") or [], key=placement):
        district = (c.get("district") or {}).get("name", "")
        if c.get("type") == "ballot-measure" or c.get("referendumTitle"):
            measures.append({
                "title": c.get("referendumTitle") or c.get("ballotTitle") or "",
                "subtitle": c.get("referendumSubtitle", ""),
                "text": c.get("referendumText", ""),
                "responses": c.get("referendumBallotResponses") or [],
                "url": c.get("referendumUrl", ""),
                "district": district,
            })
        else:
            races.append({
                "office": c.get("office") or c.get("ballotTitle") or "",
                "district": district,
                "vote_for": c.get("numberVotingFor"),
                "candidates": [{"name": x.get("name", ""), "party": x.get("party") or "",
                                "url": x.get("candidateUrl", "")}
                               for x in c.get("candidates") or []],
            })
    election = data.get("election") or {}
    return {"election": election.get("name", ""), "day": election.get("electionDay", ""),
            "races": races, "measures": measures}

# ── National voting resource links ────────────────────────────────────────────
# vote.gov publishes a stable per-state registration page at /register/{abbr}/,
# so that one link personalizes cleanly for all 50 states + DC. vote.org and the
# EAC's directory both accept any U.S. address/state on their own site, so they
# work as reliable nationwide fallbacks. States in STATE_OFFICIAL_LINKS get their own
# election office's tools instead — each URL there was checked against the state's
# official site, so add a state only after doing the same; never guess at a URL.
STATE_OFFICIAL_LINKS = {
    "NC": ("NCSBE", [
        ("Find Your Polling Place", "https://vt.ncsbe.gov/PPLkup/"),
        ("Check Registration Status", "https://vt.ncsbe.gov/RegLkup/"),
        ("Register to Vote", "https://www.ncsbe.gov/registering/how-register"),
        ("Absentee Ballot Info", "https://www.ncsbe.gov/voting/vote-absentee-ballot"),
    ]),
    "SC": ("SC Election Commission", [
        ("Find Your Polling Place", "https://vrems.scvotes.sc.gov/Voter/Login?PageMode=PollingPlace"),
        ("Check Registration Status", "https://vrems.scvotes.sc.gov/Voter/Login?PageMode=VoterInformation"),
        ("Register to Vote", "https://scvotes.gov/voters/register-to-vote/"),
        ("Absentee Ballot Info", "https://scvotes.gov/voters/absentee-voting/"),
    ]),
    "VA": ("VA Department of Elections", [
        ("Check Registration Status", "https://vote.elections.virginia.gov/VoterInformation?lang=en"),
        ("Register to Vote", "https://www.elections.virginia.gov/citizen-portal/"),
        ("Absentee Ballot Info", "https://www.elections.virginia.gov/casting-a-ballot/early-absentee/"),
    ]),
    "TN": ("TN Secretary of State", [
        ("Check Registration & Find Your Polling Place", "https://tnmap.tn.gov/voterlookup/"),
        ("Register to Vote", "https://ovr.govote.tn.gov/"),
        ("Absentee Ballot Info", "https://sos.tn.gov/elections/guides/guide-to-absentee-voting"),
    ]),
    "GA": ("GA Secretary of State", [
        ("Check Registration & Find Your Polling Place", "https://mvp.sos.ga.gov/s/"),
        ("Register to Vote", "https://mvp.sos.ga.gov/s/voter-registration?IsRegisterNow=true"),
        ("Request an Absentee Ballot", "https://securemyabsenteeballot.sos.ga.gov/s/"),
    ]),
}

def get_official_resources(state_abbr: str) -> list:
    """Returns [(label, url), ...] of official/national resources for the given state."""
    abbr = (state_abbr or DEFAULT_STATE).upper()
    if abbr in STATE_OFFICIAL_LINKS:
        office, links = STATE_OFFICIAL_LINKS[abbr]
        return [(f"{t(label)} — {office}", url) for label, url in links]
    state_name = t(STATES.get(abbr, {}).get("name", abbr))
    return [
        (t("Register to Vote in {state} — Vote.gov", state=state_name), f"https://vote.gov/register/{abbr.lower()}/"),
        (t("Check Your Registration Status — Vote.org"), "https://www.vote.org/am-i-registered-to-vote/"),
        (t("Find Your Polling Place — Vote.org"), "https://www.vote.org/polling-place-locator/"),
        (t("Absentee / Mail Voting Info — Vote.org"), "https://www.vote.org/absentee-ballot/"),
        (t("Your State Election Office — U.S. EAC Directory"), "https://www.eac.gov/voters/register-and-vote-in-your-state"),
    ]
