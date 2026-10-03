"""My Representatives: governor, members of Congress, and state legislators for an address."""
import streamlit as st

from civiclens.data.geocode import geocode
from civiclens.data.governors import get_governor, governor_links_html
from civiclens.data.openstates import get_reps_by_location
from civiclens.helpers import (get_chamber_label, html_block, is_federal, is_state,
                               party_badge, party_css, show_searched_address)
from civiclens.states import LOWER_CHAMBER_NAMES, STATES


def render():
    st.header("🏛️ Who Represents You?")
    st.caption("Shows your state legislators AND your federal representatives in Congress — for any U.S. address.")
    address = st.text_input("Enter your address", placeholder="123 Main St, Charlotte, NC 28201")

    if st.button("Find My Reps", type="primary"):
        if not address.strip():
            st.error("Please enter an address.")
        else:
            with st.spinner("Locating address…"):
                lat, lng, detected_state = geocode(address)

            if lat is None:
                st.error("Could not locate that address. Try adding your city and zip code.")
            else:
                state_name = STATES.get(detected_state, {}).get("name", "")
                show_searched_address(address)
                if state_name:
                    st.caption(f"Detected state: **{state_name}**")

                # Governor (or DC's Mayor) — looked up live for any state. Rendered before
                # the OpenStates call and outside its failure branch on purpose: it comes
                # from a different source, so a rate-limited or failed legislator lookup
                # (OpenStates allows only 10 requests/min) must not hide the governor too.
                governor, governor_err = get_governor(detected_state)
                office_label = "Mayor" if detected_state == "DC" else "Governor"
                st.markdown(
                    f'<p class="section-label">🏛️ {office_label}'
                    f'{" of " + state_name if state_name else ""}</p>',
                    unsafe_allow_html=True,
                )
                if governor:
                    gov_party = governor["party"]
                    gov_css, gov_badge = party_css(gov_party), party_badge(gov_party)
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if governor["photo"]: st.image(governor["photo"], width=75)
                        else: st.markdown("👤")
                    with col2:
                        st.markdown(html_block(f"""
                        <div class="rep-card {gov_css}">
                            <strong style="font-size:1.05rem">{governor['name']}</strong>
                            <span class="party-badge {gov_badge}">{gov_party}</span><br>
                            <span style="color:var(--cl-muted);font-size:0.88rem">{governor['office']}{" — " + state_name if state_name else ""}</span><br>
                            {governor_links_html(governor)}
                        </div>"""), unsafe_allow_html=True)
                else:
                    st.caption(
                        f"Could not load the current {office_label.lower()} right now"
                        f"{' — ' + governor_err if governor_err else ''}."
                    )

                with st.spinner("Loading your representatives…"):
                    all_reps = get_reps_by_location(lat, lng)

                if not all_reps:
                    st.warning(
                        "Could not load legislators for this address — OpenStates may be "
                        "rate-limiting (10 requests/min). Wait a moment and search again."
                    )
                else:
                    federal_reps = [r for r in all_reps if is_federal(r)]
                    state_reps   = [r for r in all_reps if is_state(r)]

                    st.markdown(f'<p class="section-label">🇺🇸 U.S. Senate{" — " + state_name if state_name else ""}</p>', unsafe_allow_html=True)
                    us_senators = [r for r in federal_reps if (r.get("current_role") or {}).get("org_classification") == "upper"]
                    for rep in us_senators:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:var(--cl-muted);font-size:0.88rem">U.S. Senator{" — " + state_name if state_name else ""}</span><br>
                                {"📧 <a href='" + email + "' target='_blank'>Contact</a>" if email else ""}
                            </div>""", unsafe_allow_html=True)

                    st.markdown('<p class="section-label">🇺🇸 U.S. House of Representatives</p>', unsafe_allow_html=True)
                    us_house = [r for r in federal_reps if (r.get("current_role") or {}).get("org_classification") == "lower"]
                    for rep in us_house:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        label = get_chamber_label(rep)
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:var(--cl-muted);font-size:0.88rem">{label}</span><br>
                                {"📧 <a href='" + email + "' target='_blank'>Contact</a>" if email else ""}
                            </div>""", unsafe_allow_html=True)

                    st.markdown(f'<p class="section-label">🏛️ {state_name + " " if state_name else ""}State Senate</p>', unsafe_allow_html=True)
                    nc_senate = [r for r in state_reps if (r.get("current_role") or {}).get("org_classification") == "upper"]
                    for rep in nc_senate:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        label = get_chamber_label(rep)
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:var(--cl-muted);font-size:0.88rem">{label}</span><br>
                                {"📧 <a href='mailto:" + email + "'>" + email + "</a>" if email and not email.startswith("http") else ""}
                            </div>""", unsafe_allow_html=True)

                    st.markdown(f'<p class="section-label">🏛️ {state_name + " " if state_name else ""}{LOWER_CHAMBER_NAMES.get(detected_state, "State House of Representatives")}</p>', unsafe_allow_html=True)
                    nc_house = [r for r in state_reps if (r.get("current_role") or {}).get("org_classification") == "lower"]
                    for rep in nc_house:
                        name  = rep.get("name", "Unknown")
                        party = rep.get("party", "Unknown")
                        label = get_chamber_label(rep)
                        photo = rep.get("image", "")
                        email = rep.get("email", "")
                        css, badge = party_css(party), party_badge(party)
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if photo: st.image(photo, width=75)
                            else: st.markdown("👤")
                        with col2:
                            st.markdown(f"""
                            <div class="rep-card {css}">
                                <strong style="font-size:1.05rem">{name}</strong>
                                <span class="party-badge {badge}">{party}</span><br>
                                <span style="color:var(--cl-muted);font-size:0.88rem">{label}</span><br>
                                {"📧 <a href='mailto:" + email + "'>" + email + "</a>" if email and not email.startswith("http") else ""}
                            </div>""", unsafe_allow_html=True)
