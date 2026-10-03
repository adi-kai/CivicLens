import os

import streamlit as st

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
# Must be the first Streamlit call, before anything below renders.
st.set_page_config(page_title="CivicLens", layout="wide", page_icon="🗳️")

from civiclens.tabs import (bills, candidates, compare, deadlines, home, my_reps,  # noqa: E402
                            polling, rep_map)
from civiclens.theme import PALETTES, apply_base_styles, apply_theme  # noqa: E402

apply_base_styles()

# ─────────────────────────────────────────────
# SIDEBAR NAV
# ─────────────────────────────────────────────
SECTIONS = {
    "🏠 Home":               home.render,
    "📍 Polling Finder":     polling.render,
    "📅 Deadlines":          deadlines.render,
    "🏛️ My Representatives": my_reps.render,
    "🗺️ Rep Map":            rep_map.render,
    "📋 Bill Tracker":       bills.render,
    "🔍 District Compare":   compare.render,
    "🗳️ Candidates":         candidates.render,
}
menu = st.sidebar.radio("Navigate", list(SECTIONS))

theme_keys = list(PALETTES)
# Seed from the URL once, then let the keyed widget own the value. Recomputing `index`
# from the URL on every run changed the widget's identity, so the dropdown could lag a
# click behind the colors.
if "theme" not in st.session_state:
    url_theme = st.query_params.get("theme", theme_keys[0])
    st.session_state["theme"] = url_theme if url_theme in PALETTES else theme_keys[0]
theme_choice = st.sidebar.selectbox(
    "Color theme",
    theme_keys,
    key="theme",
    format_func=lambda k: PALETTES[k][0],
)
st.query_params["theme"] = theme_choice  # remembered in the URL, no cookies or accounts
apply_theme(theme_choice)

SECTIONS[menu]()

# Privacy Policy and Terms of Use
def read_policy_file(path: str):
    # Resolve next to this script so the app works no matter which folder it's launched from
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None

st.markdown("---")
for policy_title, policy_path in [("Privacy Policy", "privacy-policy.html"),
                                  ("Terms of Service", "terms-of-service.html")]:
    with st.expander(policy_title):
        policy_html = read_policy_file(policy_path)
        if policy_html:
            st.iframe(policy_html, height=600)
        else:
            st.info(f"The {policy_title} is temporarily unavailable.")
st.markdown(
    '<div style="text-align:center;font-size:0.8rem;color:var(--cl-muted);padding:0.5rem 0 1rem">'
    'CivicLens is nonpartisan and not affiliated with any government agency.</div>',
    unsafe_allow_html=True
)
