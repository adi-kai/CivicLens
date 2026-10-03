"""Polling Finder: polling place and voting links for an address."""
import streamlit as st

from civiclens.data.civic import get_official_resources, get_voter_info
from civiclens.data.geocode import geocode
from civiclens.helpers import esc, show_searched_address
from civiclens.states import STATES


def render():
    st.header("📍 Find Your Polling Place")
    st.caption("Works for any U.S. address — powered by the Google Civic Information API.")
    address = st.text_input("Enter your full address (e.g. 123 Main St, Charlotte, NC 28201)")

    if st.button("Search", type="primary"):
        if not address.strip():
            st.error("Please enter an address.")
        else:
            with st.spinner("Looking up your polling place…"):
                data = get_voter_info(address)
                _, _, detected_state = geocode(address)

            state_info = STATES.get(detected_state, {})
            state_name = state_info.get("name", "")

            show_searched_address(address)

            if "pollingLocations" in data and data["pollingLocations"]:
                loc  = data["pollingLocations"][0]
                addr = loc.get("address", {})
                st.success("✅ Polling location found!")
                st.markdown(f"""
                <div class="info-box">
                    <strong>{esc(addr.get('locationName', 'Polling Location'))}</strong><br>
                    {esc(addr.get('line1', ''))}<br>
                    {esc(addr.get('city', ''))}, {esc(addr.get('state', ''))} {esc(addr.get('zip', ''))}
                </div>
                """, unsafe_allow_html=True)
                hours = loc.get("pollingHours", "")
                if hours:
                    st.caption(f"🕐 Hours: {hours}")
            else:
                st.warning("Polling location not available right now — no active election. Use these resources:")

            # Prefer any official links Google's Civic API returns for this
            # address's state administration body; fall back to our curated list.
            admin_bodies = (data.get("state") or [{}])[0].get("electionAdministrationBody", {}) if data.get("state") else {}
            civic_links = [
                ("Voting Location Finder", admin_bodies.get("votingLocationFinderUrl")),
                ("Register to Vote", admin_bodies.get("electionRegistrationUrl")),
                ("Absentee / Mail Voting Info", admin_bodies.get("absenteeVotingInfoUrl")),
                ("Ballot Information", admin_bodies.get("ballotInfoUrl")),
            ]
            civic_links = [(label, url) for label, url in civic_links if url]

            st.subheader(f"🗳️ {state_name + ' ' if state_name else ''}Voting Resources")
            links_to_show = civic_links if civic_links else get_official_resources(detected_state)
            for label, url in links_to_show:
                st.markdown(f"- [{label}]({url})")
