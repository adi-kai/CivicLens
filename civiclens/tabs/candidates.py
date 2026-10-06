"""Candidates: AI-assisted 2026 candidate research for a race."""
import streamlit as st

from civiclens.data.ai import candidate_info_fallback, get_candidate_info
from civiclens.helpers import html_block, rate_limit_check, sanitize_ai_html
from civiclens.i18n import current_lang, t
from civiclens.states import DEFAULT_STATE, STATES, get_candidate_races
from civiclens.theme import theme_ai_html
from civiclens.ui import page_header


def render():
    page_header(t("🗳️ 2026 Candidates"),
                t("Powered by Google Gemini 2.5 Flash + Groq + Tavily + Google Search — free, nonpartisan, live from official campaign websites"))

    col_state, col_race = st.columns([1, 3])
    with col_state:
        cand_state_abbrs = sorted(STATES.keys())
        cand_state = st.selectbox(t("State"), cand_state_abbrs, index=cand_state_abbrs.index(DEFAULT_STATE), key="cand_state")
    cand_state_name = STATES[cand_state]["name"]   # English — goes into the AI search
    state_disp = t(cand_state_name)
    lang = current_lang()

    race_options = get_candidate_races(cand_state)
    with col_race:
        race_label = st.selectbox(t("Select Race"), list(race_options.keys()))
    race_type, district_word = race_options[race_label]
    needs_district = district_word is not None

    district = ""
    if needs_district:
        district = st.text_input(t("{word} Number", word=t(district_word)), placeholder=t("e.g. 14"))

    if st.button(t("Find Candidates & Positions"), type="primary", key="candidates_btn"):
        clean_race = race_type
        race_disp = t(race_type)
        if needs_district and district.strip():
            clean_race = f"{race_type} {district_word} {district.strip()}"
            race_disp = f"{t(race_type)} — {t(district_word)} {district.strip()}"

        if needs_district and not district.strip():
            st.error(t("Please enter a {word} number for this race type.", word=t(district_word).lower()))
        else:
            with st.spinner(t("Searching for 2026 {state} {race} candidates — may take 15–30 seconds…",
                              state=state_disp, race=race_disp)):
                if not rate_limit_check("gemini_calls", max_calls=5, window=60):
                    st.toast(t("⚡ Gemini limit reached, switching to backup…"), icon="🔄")
                    html_output = candidate_info_fallback(clean_race, cand_state_name, lang)
                else:
                    html_output = get_candidate_info(clean_race, cand_state_name, lang)
                    if html_output is None:
                        st.toast(t("⚡ Gemini unavailable, switching to backup…"), icon="🔄")
                        html_output = candidate_info_fallback(clean_race, cand_state_name, lang)

            st.markdown(html_block(theme_ai_html(sanitize_ai_html(html_output))), unsafe_allow_html=True)
            if cand_state == "NC":
                verify_link = "[ncsbe.gov](https://www.ncsbe.gov)"
            else:
                office = t("{state}'s election office", state=state_disp)
                verify_link = f"[{office}](https://www.eac.gov/voters/register-and-vote-in-your-state)"
            st.caption(t("⚠️ AI-assisted research from public web sources. Always verify with official campaign sites and {link}. Results cached for 1 hour.",
                         link=verify_link))
