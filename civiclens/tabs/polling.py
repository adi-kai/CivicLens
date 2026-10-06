"""Polling Finder: polling place and voting links for an address."""
import streamlit as st

from civiclens.data.civic import get_official_resources, get_voter_info
from civiclens.data.geocode import geocode
from civiclens.helpers import address_input, esc, show_searched_address
from civiclens.i18n import t
from civiclens.states import STATES
from civiclens.ui import page_header


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

            if "pollingLocations" in data and data["pollingLocations"]:
                loc  = data["pollingLocations"][0]
                addr = loc.get("address", {})
                st.success(t("✅ Polling location found!"))
                st.markdown(f"""
                <div class="info-box">
                    <strong>{esc(addr.get('locationName', t('Polling Location')))}</strong><br>
                    {esc(addr.get('line1', ''))}<br>
                    {esc(addr.get('city', ''))}, {esc(addr.get('state', ''))} {esc(addr.get('zip', ''))}
                </div>
                """, unsafe_allow_html=True)
                hours = loc.get("pollingHours", "")
                if hours:
                    st.caption(t("🕐 Hours: {hours}", hours=hours))
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
                st.subheader(t("🗳️ {state} Voting Resources", state=state_name))
            else:
                st.subheader(t("🗳️ Voting Resources"))
            links_to_show = civic_links if civic_links else get_official_resources(detected_state)
            for label, url in links_to_show:
                st.markdown(f"- [{label}]({url})")
