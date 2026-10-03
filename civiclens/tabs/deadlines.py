"""Deadlines: Election Day, NC's verified dates, and official links for other states."""
import streamlit as st

from civiclens.data.civic import get_official_resources
from civiclens.data.geocode import geocode
from civiclens.helpers import address_input, show_searched_address
from civiclens.states import STATES


def render():
    st.header("📅 Key Voting Deadlines — 2026")
    st.caption("Election Day itself is set federally — the same date nationwide. "
               "Registration and early-voting windows are set by each state, so enter your address below to see yours.")

    dl_address = address_input("Enter your address")

    dl_state = None
    if dl_address.strip():
        with st.spinner("Locating address…"):
            _, _, dl_state = geocode(dl_address)
        if not dl_state:
            st.warning("Could not determine the state for that address — try adding your city and zip code.")

    dl_state_name = STATES.get(dl_state, {}).get("name", "")

    show_searched_address(dl_address)

    st.markdown("""
    <div class="rep-card other">
        <strong>Election Day</strong><br>
        📅 <em>November 3, 2026</em><br>
        <span style="color:var(--cl-muted);font-size:0.9rem">Polls open per your state and county's posted hours. Set by federal law — the same date nationwide.</span>
    </div>
    """, unsafe_allow_html=True)

    if not dl_state:
        st.info("Enter your address above to see registration and early-voting resources for your state.")
    elif dl_state == "NC":
        st.markdown(f'<p class="section-label">🏛️ {dl_state_name} 2026 Deadlines</p>', unsafe_allow_html=True)
        # Hand-verified against ncsbe.gov. Re-check every date (and update
        # NC_DEADLINES_LAST_VERIFIED) before each election.
        NC_DEADLINES_LAST_VERIFIED = "October 3, 2026"
        ncsbe_reg_url   = "https://www.ncsbe.gov/news/press-releases/2026/10/02/regular-voter-registration-deadline-approaching-2026-general-election"
        ncsbe_early_url = "https://www.ncsbe.gov/voting/vote-early-person"
        ncsbe_mail_url  = "https://www.ncsbe.gov/voting/vote-mail/detailed-instructions-voting-mail"
        deadlines = [
            ("Voter Registration Deadline",          "5 p.m. Friday, October 9, 2026",
             "Deadline to register to vote by mail or on Election Day.", ncsbe_reg_url),
            ("Same-Day Registration (Early Voting)",  "October 15 – October 31, 2026",
             "Missed the deadline? Register and vote at any early voting site in your county. "
             "Not available for most voters on Election Day.", ncsbe_early_url),
            ("Early Voting Begins",                   "Thursday, October 15, 2026",
             "No excuse needed in NC.", ncsbe_early_url),
            ("Early Voting Ends",                     "3 p.m. Saturday, October 31, 2026",
             "Last chance to vote early.", ncsbe_early_url),
            ("Absentee Ballot Request Deadline",      "5 p.m. Tuesday, October 20, 2026",
             "Your county board of elections must receive the request by this time. "
             "(Military and overseas voters: 5 p.m. November 2.)", ncsbe_mail_url),
            ("Absentee Ballot Return Deadline",       "7:30 p.m. Tuesday, November 3, 2026",
             "Your county board of elections must <strong>receive</strong> your ballot by this time — "
             "a postmark by Election Day is no longer enough.", ncsbe_mail_url),
        ]
        for name, date, note, source in deadlines:
            st.markdown(f"""
            <div class="rep-card other">
                <strong>{name}</strong><br>
                📅 <em>{date}</em><br>
                <span style="color:var(--cl-muted);font-size:0.9rem">{note}</span><br>
                <span style="font-size:0.8rem"><a href="{source}" target="_blank">Source: NC State Board of Elections</a></span>
            </div>
            """, unsafe_allow_html=True)
        st.caption(f"Dates last verified against ncsbe.gov on {NC_DEADLINES_LAST_VERIFIED}.")
        st.markdown('<p class="section-label">🗳️ Official Resources</p>', unsafe_allow_html=True)
        for label, url in get_official_resources(dl_state):
            st.markdown(f"- [{label}]({url})")
        st.caption(f"Always verify deadlines directly with {dl_state_name}'s official election authority — rules can change.")
    else:
        st.info(
            f"Registration cutoffs, early-voting windows, and absentee deadlines for **{dl_state_name}** "
            f"vary and can change year to year, so we don't guess at exact dates here — use the official "
            f"links below to get {dl_state_name}'s current 2026 deadlines."
        )
        st.markdown('<p class="section-label">🗳️ Official Resources</p>', unsafe_allow_html=True)
        for label, url in get_official_resources(dl_state):
            st.markdown(f"- [{label}]({url})")
        st.caption(f"Always verify deadlines directly with {dl_state_name}'s official election authority — rules can change.")
