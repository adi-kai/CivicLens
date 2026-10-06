"""My Ballot: the races and ballot questions on an address's ballot, from official data.

The data comes from the Voting Information Project (through Google's voterinfo call),
which election offices publish to state by state as Election Day approaches. A state
that hasn't published yet gets an explanation and its official links, never a guess.
"""
import streamlit as st

from civiclens.data.civic import get_official_resources, get_voter_info, parse_ballot
from civiclens.data.geocode import geocode
from civiclens.helpers import (address_input, esc, html_block, party_badge, party_css,
                               party_label, show_searched_address)
from civiclens.i18n import format_date, t
from civiclens.states import STATES
from civiclens.ui import page_header, section_label

# Google's messages when it can't match the address itself (vs. a state with no data yet)
ADDRESS_ERRORS = ("parse", "no information", "invalid")


def go_to_candidates():
    st.session_state["menu"] = "🗳️ Candidates"


def race_card(race: dict):
    rows = ""
    for c in race["candidates"]:
        name = esc(c["name"])
        if c["url"]:
            name = f'<a href="{esc(c["url"])}" target="_blank">{name}</a>'
        badge = (f'<span class="party-badge {party_badge(c["party"])}">{esc(party_label(c["party"]))}</span>'
                 if c["party"] else "")
        rows += f'<div class="cl-candidate"><span>{name}</span>{badge}</div>'
    if not rows:
        rows = f'<div class="cl-candidate"><span style="color:var(--cl-muted)">{t("No candidates listed.")}</span></div>'
    vote_for = (f'<span class="cl-pill">{t("Vote for {n}", n=race["vote_for"])}</span>'
                if race["vote_for"] else "")
    # Single-candidate or all-one-party races still get the neutral border
    parties = {c["party"] for c in race["candidates"] if c["party"]}
    css = party_css(parties.pop()) if len(parties) == 1 else "other"
    st.markdown(html_block(f"""
    <div class="rep-card {css}">
        <div class="cl-race-head">
            <div><div class="cl-race-office">{esc(race["office"])}</div>
            <div class="cl-race-district">{esc(race["district"])}</div></div>
            {vote_for}
        </div>
        {rows}
    </div>"""), unsafe_allow_html=True)


def measure_card(measure: dict):
    responses = "".join(f'<span class="cl-response">{esc(r)}</span>' for r in measure["responses"])
    subtitle = f'<div class="cl-race-district">{esc(measure["subtitle"])}</div>' if measure["subtitle"] else ""
    text = f'<div class="cl-measure-text">{esc(measure["text"])}</div>' if measure["text"] else ""
    link = (f'<a href="{esc(measure["url"])}" target="_blank" style="font-size:0.85rem">{t("Full text →")}</a>'
            if measure["url"] else "")
    district = f'<span class="cl-pill">{esc(measure["district"])}</span>' if measure["district"] else ""
    st.markdown(html_block(f"""
    <div class="rep-card other">
        <div class="cl-race-head">
            <div class="cl-race-office">{esc(measure["title"])}</div>
            {district}
        </div>
        {subtitle}
        {text}
        <div>{responses}</div>
        {link}
    </div>"""), unsafe_allow_html=True)


def render():
    page_header(t("📝 My Ballot"),
                t("Every race and ballot question on your 2026 ballot, from official election data."))
    address = address_input(t("Enter your address"))

    if not address.strip():
        st.info(t("Enter your address to see what's on your ballot."))
        return

    with st.spinner(t("Looking up your ballot…")):
        data = get_voter_info(address)
        _, _, state = geocode(address)
    state_name = t(STATES.get(state, {}).get("name", ""))
    show_searched_address(address)

    error = ((data.get("error") or {}).get("message") or "").lower()
    ballot = parse_ballot(data) if not error else {"races": [], "measures": []}

    if error and any(word in error for word in ADDRESS_ERRORS):
        st.warning(t("We couldn't match that address to a ballot. Try adding your city and zip code."))
        return
    if not ballot["races"] and not ballot["measures"]:
        where = state_name or t("your state")
        st.info(t("{state} hasn't published its ballot data yet. Election offices add official ballots state by state as Election Day gets closer — check back soon, or use the official resources below.",
                  state=where))
        section_label(t("🗳️ Official Resources"))
        for label, url in get_official_resources(state):
            st.markdown(f"- [{label}]({url})")
        return

    n_races, n_measures = len(ballot["races"]), len(ballot["measures"])
    counts = [t("1 race") if n_races == 1 else t("{n} races", n=n_races)]
    if n_measures:
        counts.append(t("1 ballot question") if n_measures == 1 else t("{n} ballot questions", n=n_measures))
    day = format_date(ballot["day"]) if ballot.get("day") else ""
    summary = t("{counts} on your ballot", counts=t(" and ").join(counts))
    st.success(f"{summary} · {day}" if day else summary)

    if ballot["races"]:
        section_label(t("🏛️ Races"))
        for race in ballot["races"]:
            race_card(race)
    if ballot["measures"]:
        section_label(t("📜 Ballot Questions"))
        for measure in ballot["measures"]:
            measure_card(measure)

    st.button(t("🔎 Research these candidates"), on_click=go_to_candidates, type="secondary")
    st.caption(t("Official ballot data from the Voting Information Project, via the Google Civic Information API. Race names and ballot questions appear exactly as election officials published them. Your exact ballot can vary by precinct — check your official sample ballot before you vote."))
