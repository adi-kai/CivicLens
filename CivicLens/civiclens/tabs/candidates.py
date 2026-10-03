"""Candidates: AI-assisted 2026 candidate research for a race."""
import streamlit as st

from civiclens.data.ai import _candidate_info_fallback, get_candidate_info
from civiclens.helpers import html_block, rate_limit_check
from civiclens.states import DEFAULT_STATE, STATES, get_candidate_races
from civiclens.theme import theme_ai_html


def render():
    st.header("🗳️ 2026 Candidates")
    st.caption("Powered by Google Gemini 2.5 Flash + Groq + Tavily + Google Search — free, nonpartisan, live from official campaign websites")

    col_state, col_race = st.columns([1, 3])
    with col_state:
        cand_state_abbrs = sorted(STATES.keys())
        cand_state = st.selectbox("State", cand_state_abbrs, index=cand_state_abbrs.index(DEFAULT_STATE), key="cand_state")
    cand_state_name = STATES[cand_state]["name"]

    race_options = get_candidate_races(cand_state)
    with col_race:
        race_label = st.selectbox("Select Race", list(race_options.keys()))
    race_type, district_word = race_options[race_label]
    needs_district = district_word is not None

    district = ""
    if needs_district:
        district = st.text_input(f"{district_word} Number", placeholder="e.g. 14")

    if st.button("Find Candidates & Positions", type="primary", key="candidates_btn"):
        clean_race = race_type
        if needs_district and district.strip():
            clean_race = f"{race_type} {district_word} {district.strip()}"

        if needs_district and not district.strip():
            st.error(f"Please enter a {district_word.lower()} number for this race type.")
        else:
            with st.spinner(f"Searching for 2026 {cand_state_name} {clean_race} candidates — may take 15–30 seconds…"):
                if not rate_limit_check("gemini_calls", max_calls=5, window=60):
                    st.toast("⚡ Gemini limit reached, switching to backup…", icon="🔄")
                    html_output = _candidate_info_fallback(clean_race, cand_state_name)
                else:
                    html_output = get_candidate_info(clean_race, cand_state_name)
                    if html_output is None:
                        st.toast("⚡ Gemini unavailable, switching to backup…", icon="🔄")
                        html_output = _candidate_info_fallback(clean_race, cand_state_name)

            st.markdown(html_block(theme_ai_html(html_output)), unsafe_allow_html=True)
            if cand_state == "NC":
                verify_link = "[ncsbe.gov](https://www.ncsbe.gov)"
            else:
                verify_link = f"[{cand_state_name}'s election office](https://www.eac.gov/voters/register-and-vote-in-your-state)"
            st.caption(
                "⚠️ AI-assisted research from public web sources. "
                f"Always verify with official campaign sites and {verify_link}. "
                "Results cached for 1 hour."
            )
