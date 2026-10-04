"""Per-state metadata: the state registry and the races each state has."""
from civiclens.i18n import t

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

# ── Candidate race options per state ─────────────────────────────────────────
# States with a single at-large U.S. House seat (no district number needed)
AT_LARGE_HOUSE_STATES = {"AK", "DE", "ND", "SD", "VT", "WY"}
# States whose lower chamber isn't called the House. State legislative races always
# start with "State" so they aren't confused with Congress.
LOWER_CHAMBER_NAMES = {
    "CA": "State Assembly", "NY": "State Assembly", "WI": "State Assembly",
    "NV": "State Assembly", "NJ": "State Assembly",
    "MD": "State House of Delegates", "VA": "State House of Delegates", "WV": "State House of Delegates",
}

def get_candidate_races(state_abbr: str) -> dict:
    """Returns {dropdown label: (race name, district word)} for a state's major races.
    Labels are in the current language; race names and district words ("District"/"Ward")
    stay English, since they go into the AI search. district word is None when the race
    is statewide or at-large."""
    abbr = (state_abbr or DEFAULT_STATE).upper()
    name = t(STATES.get(abbr, {}).get("name", abbr))
    if abbr == "DC":
        # No governor, U.S. Senators, or state legislature
        return {
            t("Mayor"): ("Mayor", None),
            t("Delegate to the U.S. House"): ("Delegate to the U.S. House", None),
            t("D.C. Council (enter ward below)"): ("D.C. Council", "Ward"),
        }
    races = {t("Governor"): ("Governor", None), t("U.S. Senate"): ("U.S. Senate", None)}
    if abbr in AT_LARGE_HOUSE_STATES:
        races[t("U.S. House (at-large)")] = ("U.S. House At-Large", None)
    else:
        races[t("U.S. House (enter district below)")] = ("U.S. House", "District")
    if abbr == "NE":
        # Nebraska's legislature is unicameral
        races[t("Nebraska State Legislature (enter district below)")] = ("State Legislature", "District")
    else:
        lower = LOWER_CHAMBER_NAMES.get(abbr, "State House")
        races[t("{state} {chamber} (enter district below)", state=name, chamber=t("State Senate"))] = ("State Senate", "District")
        races[t("{state} {chamber} (enter district below)", state=name, chamber=t(lower))] = (lower, "District")
    return races
