"""My Representatives: governor, members of Congress, and state legislators for an address."""
import streamlit as st

from civiclens.data.geocode import geocode
from civiclens.data.governors import get_governor, governor_links_html
from civiclens.data.openstates import get_reps_by_location
from civiclens.helpers import (address_input, esc, get_chamber_label, html_block, is_federal,
                               is_state, party_badge, party_css, party_label,
                               show_searched_address)
from civiclens.i18n import t
from civiclens.states import LOWER_CHAMBER_NAMES, STATES


def rep_card(name: str, party: str, label: str, photo: str = "", contact_html: str = ""):
    """One representative: photo on the left, name/party/role card on the right.
    contact_html is already-built (escaped) markup, or "" for none."""
    css, badge = party_css(party), party_badge(party)
    col1, col2 = st.columns([1, 5])
    with col1:
        # Plain <img> rather than st.image, which has no way to set alt text for screen readers
        if photo:
            alt = t("Photo of {name}", name=name)
            st.markdown(f"<img src='{esc(photo)}' alt='{esc(alt)}' width='75' "
                        f"style='max-width:100%;border-radius:6px'/>", unsafe_allow_html=True)
        else:
            st.markdown("👤")
    with col2:
        st.markdown(html_block(f"""
        <div class="rep-card {css}">
            <strong style="font-size:1.05rem">{esc(name)}</strong>
            <span class="party-badge {badge}">{esc(party_label(party))}</span><br>
            <span style="color:var(--cl-muted);font-size:0.88rem">{esc(label)}</span><br>
            {contact_html}
        </div>"""), unsafe_allow_html=True)


def contact_form_link(url: str) -> str:
    """Members of Congress list a contact-form URL rather than an email address."""
    return f"📧 <a href='{esc(url)}' target='_blank'>{t('Contact')}</a>" if url else ""


def mailto_link(email: str) -> str:
    """State legislators list an email address; skip it if it's actually a URL."""
    if not email or email.startswith("http"):
        return ""
    return f"📧 <a href='mailto:{esc(email)}'>{esc(email)}</a>"


def by_chamber(reps: list, chamber: str) -> list:
    return [r for r in reps if (r.get("current_role") or {}).get("org_classification") == chamber]


def section_label(text: str):
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)


def render():
    st.header(t("🏛️ Who Represents You?"))
    st.caption(t("Shows your state legislators AND your federal representatives in Congress — for any U.S. address."))
    address = address_input(t("Enter your address"))

    if st.button(t("Find My Reps"), type="primary"):
        if not address.strip():
            st.error(t("Please enter an address."))
        else:
            with st.spinner(t("Locating address…")):
                lat, lng, detected_state = geocode(address)

            if lat is None:
                st.error(t("Could not locate that address. Try adding your city and zip code."))
            else:
                state_name = t(STATES.get(detected_state, {}).get("name", ""))
                show_searched_address(address)
                if state_name:
                    st.caption(t("Detected state: **{state}**", state=state_name))

                # Governor (or DC's Mayor) — looked up live for any state. Rendered before
                # the OpenStates call and outside its failure branch on purpose: it comes
                # from a different source, so a rate-limited or failed legislator lookup
                # (OpenStates allows only 10 requests/min) must not hide the governor too.
                governor, governor_err = get_governor(detected_state)
                office_label = t("Mayor") if detected_state == "DC" else t("Governor")
                if state_name:
                    section_label(t("🏛️ {office} of {state}", office=office_label, state=state_name))
                else:
                    section_label(f"🏛️ {office_label}")
                if governor:
                    rep_card(governor["name"], governor["party"],
                             f"{t(governor['office'])}{' — ' + state_name if state_name else ''}",
                             governor["photo"], governor_links_html(governor))
                else:
                    st.caption(t("Could not load the current {office} right now.", office=office_label.lower())
                               + (f" ({governor_err})" if governor_err else ""))

                with st.spinner(t("Loading your representatives…")):
                    all_reps = get_reps_by_location(lat, lng)

                if not all_reps:
                    st.warning(t("Could not load legislators for this address — OpenStates may be rate-limiting (10 requests/min). Wait a moment and search again."))
                else:
                    federal_reps = [r for r in all_reps if is_federal(r)]
                    state_reps   = [r for r in all_reps if is_state(r)]

                    senate_header = t("🇺🇸 U.S. Senate")
                    section_label(f"{senate_header} — {state_name}" if state_name else senate_header)
                    for rep in by_chamber(federal_reps, "upper"):
                        senator = t("U.S. Senator")
                        rep_card(rep.get("name", "Unknown"), rep.get("party", "Unknown"),
                                 f"{senator} — {state_name}" if state_name else senator,
                                 rep.get("image", ""), contact_form_link(rep.get("email", "")))

                    section_label(t("🇺🇸 U.S. House of Representatives"))
                    for rep in by_chamber(federal_reps, "lower"):
                        rep_card(rep.get("name", "Unknown"), rep.get("party", "Unknown"),
                                 get_chamber_label(rep), rep.get("image", ""),
                                 contact_form_link(rep.get("email", "")))

                    section_label(f"🏛️ {t('State Senate')}" + (f" — {state_name}" if state_name else ""))
                    for rep in by_chamber(state_reps, "upper"):
                        rep_card(rep.get("name", "Unknown"), rep.get("party", "Unknown"),
                                 get_chamber_label(rep), rep.get("image", ""),
                                 mailto_link(rep.get("email", "")))

                    lower = t(LOWER_CHAMBER_NAMES.get(detected_state, "State House of Representatives"))
                    section_label(f"🏛️ {lower}" + (f" — {state_name}" if state_name else ""))
                    for rep in by_chamber(state_reps, "lower"):
                        rep_card(rep.get("name", "Unknown"), rep.get("party", "Unknown"),
                                 get_chamber_label(rep), rep.get("image", ""),
                                 mailto_link(rep.get("email", "")))
