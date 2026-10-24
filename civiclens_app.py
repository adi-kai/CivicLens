import os

import streamlit as st

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
# Must be the first Streamlit call, before anything below renders.
st.set_page_config(page_title="CivicLens", layout="wide",
                   page_icon=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "assets", "favicon.png"))

from civiclens.helpers import plain  # noqa: E402
from civiclens.i18n import LANG_KEY, LANGUAGES, label_func, t, translate  # noqa: E402
from civiclens.tabs import (ballot, bills, candidates, compare, deadlines, home,  # noqa: E402
                            my_reps, polling, rep_map)
from civiclens.theme import PALETTES, apply_base_styles, apply_theme  # noqa: E402

apply_base_styles()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
# The language and theme pickers seed from the URL once, then let the keyed widget own
# the value. Recomputing `index` from the URL on every run changed the widget's identity,
# so a dropdown could lag a click behind. Both are remembered in the URL — no cookies.
if LANG_KEY not in st.session_state:
    url_lang = st.query_params.get(LANG_KEY, "en")
    st.session_state[LANG_KEY] = url_lang if url_lang in LANGUAGES else "en"

st.sidebar.markdown(
    '<div class="cl-brand"><div class="cl-brand-name">CivicLens</div>'
    f'<div class="cl-brand-tag">{t("Nonpartisan voter guide")}</div></div>',
    unsafe_allow_html=True,
)

# Keyed widgets whose displayed labels are translated
TRANSLATED_CHOICES = ("menu", "theme")


def keep_translated_choices():
    """Streamlit 1.58 remembers a radio or selectbox choice as its displayed label. Those
    labels change with the language, so after a switch the old label matched no option and
    the widget handed back the raw label ("Deadlines" instead of "📅 Deadlines"), crashing
    the page. Re-saving each choice by its key before the rerun makes Streamlit send the
    new language's labels instead."""
    for key in TRANSLATED_CHOICES:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


# Labeled in both languages so a Spanish speaker can find it before switching
lang_choice = st.sidebar.selectbox("Language / Idioma", list(LANGUAGES), key=LANG_KEY,
                                   format_func=LANGUAGES.get, on_change=keep_translated_choices)
st.query_params[LANG_KEY] = lang_choice

SECTIONS = {
    "🏠 Home":               home.render,
    "📍 Polling Finder":     polling.render,
    "📝 My Ballot":          ballot.render,
    "📅 Deadlines":          deadlines.render,
    "🏛️ My Representatives": my_reps.render,
    "🗺️ Rep Map":            rep_map.render,
    "📋 Bill Tracker":       bills.render,
    "🔍 District Compare":   compare.render,
    "🗳️ Candidates":         candidates.render,
}
# Keyed so the Home page's section cards can switch sections through session state.
# The keys keep their emoji (they're the translation keys); the nav shows text only.
nav_label = label_func()
menu = st.sidebar.radio(t("Navigate"), list(SECTIONS), key="menu",
                        format_func=lambda key: plain(nav_label(key)))
# Backstop for the label problem above: map a stray label (in either language) to its section
if menu not in SECTIONS:
    nav_labels = {plain(translate(key, lang)): key for key in SECTIONS for lang in LANGUAGES}
    menu = nav_labels.get(menu, next(iter(SECTIONS)))

theme_keys = list(PALETTES)
if "theme" not in st.session_state:
    url_theme = st.query_params.get("theme", theme_keys[0])
    st.session_state["theme"] = url_theme if url_theme in PALETTES else theme_keys[0]
theme_choice = st.sidebar.selectbox(
    t("Color theme"),
    theme_keys,
    key="theme",
    format_func=label_func(lambda k: PALETTES[k][0]),
)
if theme_choice not in PALETTES:
    theme_names = {translate(PALETTES[key][0], lang): key for key in PALETTES for lang in LANGUAGES}
    theme_choice = theme_names.get(theme_choice, theme_keys[0])
st.query_params["theme"] = theme_choice
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

for policy_title, policy_path in [("Privacy Policy", "privacy-policy.html"),
                                  ("Terms of Service", "terms-of-service.html")]:
    with st.expander(t(policy_title)):
        policy_html = read_policy_file(policy_path)
        if policy_html:
            if lang_choice != "en":
                st.caption(t("This document is available in English only."))
            st.iframe(policy_html, height=600)
        else:
            st.info(t("The {title} is temporarily unavailable.", title=t(policy_title)))
st.markdown(
    f'<div class="cl-footer">{t("CivicLens is nonpartisan and not affiliated with any government agency.")}</div>',
    unsafe_allow_html=True
)
