"""Polling Finder: polling place and voting links for an address."""
import datetime

import streamlit as st

from civiclens.data.civic import get_official_resources, get_voter_info
from civiclens.data.geocode import geocode
from civiclens.helpers import address_input, esc, html_block, plain, show_searched_address
from civiclens.i18n import t
from civiclens.states import STATES
from civiclens.ui import official_links, page_header, section_label


def render():
    page_header(t("📍 Find Your Polling Place"),
                t("Works for any U.S. address — powered by the Google Civic Information API."))
    address = address_input(t("Enter your full address"))

    if st.button(t("Search"), type="primary"):
        if not address.strip():
            st.error(t("Please enter an address."))
        else:
            with st.spinner(t("Looking up your polling place…")):
                data = get_voter_info(address)
                _, _, detected_state = geocode(address)

            state_name = t(STATES.get(detected_state, {}).get("name", ""))

            show_searched_address(address)

            polls = data.get("pollingLocations") or []
            year = (data.get("election") or {}).get("electionDay", "")[:4]
            # A site whose listed days have all passed is closed for this election
            early = [loc for loc in data.get("earlyVoteSites") or []
                     if not loc.get("pollingHours") or upcoming_hours(loc["pollingHours"], year)]

            if polls:
                st.success(plain(t("✅ Polling location found!")))
                section_label(t("🗳️ Election Day"))
                site_card(polls[0], year)
            if early:
                section_label(t("🗳️ Early Voting Sites"))
                for loc in early[:MAX_EARLY_SITES]:
                    site_card(loc, year)
                if len(early) > MAX_EARLY_SITES:
                    st.caption(t("{n} more early voting sites — see the official links below.",
                                 n=len(early) - MAX_EARLY_SITES))
            if not polls and not early:
                if data.get("election") and "error" not in data:
                    st.warning(t("Your election office hasn't published polling places for this address yet. Use these resources:"))
                else:
                    st.warning(t("Polling location not available right now — no active election. Use these resources:"))

            # Prefer any official links Google's Civic API returns for this
            # address's state administration body; fall back to our curated list.
            admin_bodies = (data.get("state") or [{}])[0].get("electionAdministrationBody", {}) if data.get("state") else {}
            civic_links = [
                (t("Voting Location Finder"), admin_bodies.get("votingLocationFinderUrl")),
                (t("Register to Vote"), admin_bodies.get("electionRegistrationUrl")),
                (t("Absentee / Mail Voting Info"), admin_bodies.get("absenteeVotingInfoUrl")),
                (t("Ballot Information"), admin_bodies.get("ballotInfoUrl")),
            ]
            civic_links = [(label, url) for label, url in civic_links if url]

            if state_name:
                section_label(esc(t("🗳️ {state} Voting Resources", state=state_name)))
            else:
                section_label(t("🗳️ Voting Resources"))
            official_links(civic_links if civic_links else get_official_resources(detected_state))


MAX_EARLY_SITES = 5


def upcoming_hours(hours: str, year: str, today: datetime.date = None) -> str:
    """Google lists one "Sun, Oct 18: 12 pm - 5 pm" line per day, past days included.
    Keeps today and later; lines without a readable date are kept as they are."""
    today = today or datetime.date.today()
    kept = []
    for line in hours.splitlines():
        day = line.split(":", 1)[0].strip()
        try:
            d = datetime.datetime.strptime(f"{day} {year}", "%a, %b %d %Y").date()
        except ValueError:
            kept.append(line)
            continue
        if d >= today:
            kept.append(line)
    return "\n".join(kept)


def site_card(loc: dict, year: str):
    addr = loc.get("address", {})
    hours = upcoming_hours(loc.get("pollingHours", ""), year)
    hours_html = "<br>".join(esc(h) for h in hours.splitlines())
    if hours_html:
        label = plain(t("🕐 Hours: {hours}", hours="")).strip()
        hours_html = f"<br><br>{esc(label)}<br>{hours_html}"
    st.markdown(html_block(f"""
    <div class="info-box">
        <strong>{esc(addr.get('locationName', t('Polling Location')))}</strong><br>
        {esc(addr.get('line1', ''))}<br>
        {esc(addr.get('city', ''))}, {esc(addr.get('state', ''))} {esc(addr.get('zip', ''))}
        {hours_html}
    </div>
    """), unsafe_allow_html=True)
