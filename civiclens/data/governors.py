"""Governors (and D.C.'s Mayor) from Wikidata."""
import re
import time

import requests
import streamlit as st

from civiclens.states import STATE_NAME_TO_ABBR

# ── Governor / head of state government (all 50 states + DC) ──────────────────
# There's no free government API for this any more: Google Civic Information's
# "representatives" endpoint (which used to answer roles=headOfGovernment) now returns
# 404 Method not found, and OpenStates' executive roster is incomplete — it lists the
# Lt. Governor and Attorney General but no Governor for several states, NC and CA
# included. So we query Wikidata instead:
#   - each state entity names its head-of-government office via P1313
#     ("office held by head of government"), which is "Governor of X" — and for DC,
#     "Mayor of the District of Columbia";
#   - the current holder is the person with a P39 ("position held") statement for that
#     office that has a start date (P580) and no end date (P582);
#   - the office item's own P856 is the official .gov site (populated for 50 of 51 —
#     California's is missing), which is why we read the website off the office rather
#     than the person: a person's P856 is often their campaign site.
# Requiring a start date is what keeps stale statements out — several state entities
# still carry no-end-date statements for governors who left years ago, and those
# statements are exactly the ones missing P580.
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
WIKIDATA_USER_AGENT = "CivicLens/1.0 (civic information app)"
GOVERNORS_SPARQL = """
SELECT ?placeLabel ?govLabel ?partyLabel ?start ?img ?possite ?article WHERE {
  { ?place wdt:P31 wd:Q35657 } UNION { VALUES ?place { wd:Q61 } }
  ?place wdt:P1313 ?pos .
  ?gov p:P39 ?stmt .
  ?stmt ps:P39 ?pos .
  FILTER NOT EXISTS { ?stmt pq:P582 ?end }
  ?stmt pq:P580 ?start .
  OPTIONAL { ?gov wdt:P102 ?party }
  OPTIONAL { ?gov wdt:P18  ?img }
  OPTIONAL { ?pos wdt:P856 ?possite }
  OPTIONAL { ?article schema:about ?gov ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
"""

class GovernorFetchError(Exception):
    pass

# Official .gov sites for offices whose Wikidata item has no P856. Only used when the
# live lookup comes back without one, so a site added upstream later wins automatically.
GOVERNOR_SITE_FALLBACKS = {
    "CA": "https://www.gov.ca.gov/",
}

def normalize_party(party: str) -> str:
    """Wikidata party labels carry "Party" and sometimes a state chapter name
    ("Democratic Party of Oregon") — the badges want the bare name."""
    p = (party or "").strip()
    if not p:
        return "Unknown"
    low = p.lower()
    if "democrat" in low:    return "Democratic"
    if "republican" in low:  return "Republican"
    if "independent" in low: return "Independent"
    return re.sub(r"\s*\bParty\b.*$", "", p).strip() or p

def commons_thumb(image_url: str, width: int = 220) -> str:
    """Turns a Wikimedia Commons Special:FilePath URL into a width-limited https
    thumbnail, so we aren't loading multi-megabyte originals into a card."""
    if not image_url:
        return ""
    url = image_url.replace("http://", "https://")
    return f"{url}{'&' if '?' in url else '?'}width={width}"

@st.cache_data(ttl=21600, show_spinner=False)
def _fetch_governors_cached() -> dict:
    """{state_abbr: {name, party, office, start, photo, site, wikipedia}} for all 51.
    Raises so a failed lookup is never cached (same reasoning as _fetch_tiger_geojson_cached)."""
    r = requests.get(
        WIKIDATA_SPARQL_URL,
        params={"query": GOVERNORS_SPARQL, "format": "json"},
        headers={"User-Agent": WIKIDATA_USER_AGENT,
                 "Accept": "application/sparql-results+json"},
        timeout=30,
    )
    if r.status_code != 200:
        raise GovernorFetchError(f"HTTP {r.status_code}")
    try:
        bindings = r.json().get("results", {}).get("bindings", [])
    except Exception as e:
        raise GovernorFetchError(f"unreadable response: {e}")

    today = time.strftime("%Y-%m-%d")
    rows_by_state: dict = {}
    for b in bindings:
        def val(key: str) -> str:
            return (b.get(key) or {}).get("value", "")
        abbr = STATE_NAME_TO_ABBR.get(val("placeLabel").strip().lower())
        if not abbr:
            continue
        start = val("start")[:10]
        # Skip a governor-elect whose term hasn't started yet
        if not start or start > today:
            continue
        rows_by_state.setdefault(abbr, []).append({
            "name": val("govLabel"), "party": val("partyLabel"), "start": start,
            "img": val("img"), "site": val("possite"), "article": val("article"),
        })

    governors = {}
    for abbr, rows in rows_by_state.items():
        # The sitting officeholder is the one who took office most recently. Optional
        # fields (photo, site, article, party chapter) split one person across several
        # rows, so collapse them back into a single record.
        latest = max(row["start"] for row in rows)
        current = [row for row in rows if row["start"] == latest]
        def first_of(key: str) -> str:
            return next((row[key] for row in current if row[key]), "")
        governors[abbr] = {
            "name":      current[0]["name"],
            "party":     normalize_party(first_of("party")),
            "office":    "Mayor" if abbr == "DC" else "Governor",
            "start":     latest,
            "photo":     commons_thumb(first_of("img")),
            "site":      first_of("site") or GOVERNOR_SITE_FALLBACKS.get(abbr, ""),
            "wikipedia": first_of("article"),
        }
    if not governors:
        raise GovernorFetchError("no results returned")
    return governors

def get_governor(state_abbr: str) -> tuple:
    """Returns (governor_dict_or_None, error_message). Uncached wrapper so a failure is
    retried on the next click and the tab code owns the warning."""
    abbr = (state_abbr or "").upper()
    if not abbr:
        return None, ""
    try:
        governors = _fetch_governors_cached()
    except Exception as e:
        return None, str(e)
    gov = governors.get(abbr)
    if not gov:
        office = "mayor" if abbr == "DC" else "governor"
        return None, f"no current {office} listed for {abbr}"
    return gov, ""

def governor_links_html(gov: dict) -> str:
    """Official-site and Wikipedia links for a governor card — both optional."""
    links = []
    if gov.get("site"):
        host = re.sub(r"^https?://(www\.)?", "", gov["site"]).rstrip("/")
        links.append(f"🌐 <a href='{gov['site']}' target='_blank'>{host}</a>")
    if gov.get("wikipedia"):
        links.append(f"<a href='{gov['wikipedia']}' target='_blank'>Wikipedia</a>")
    return " &nbsp;·&nbsp; ".join(links)
