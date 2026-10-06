"""Home: banner with the Election Day countdown, section cards, and why the data is trustworthy."""
import streamlit as st

from civiclens.helpers import esc
from civiclens.i18n import format_date, pick, t
from civiclens.ui import ELECTION_DAY, days_until_election, section_label

# One card per section, in sidebar order (keys match SECTIONS in civiclens_app.py)
FEATURES = {
    "📍 Polling Finder": {"en": "Find your polling place and your state's official voting tools.",
                         "es": "Encuentra tu lugar de votación y las herramientas oficiales de tu estado."},
    "📝 My Ballot": {"en": "See every race and ballot question on your ballot, from official data.",
                    "es": "Mira cada contienda y pregunta de tu boleta, con datos oficiales."},
    "📅 Deadlines": {"en": "Registration, early voting, and mail ballot dates for your state.",
                    "es": "Fechas de inscripción, votación anticipada y voto por correo de tu estado."},
    "🏛️ My Representatives": {"en": "Everyone who represents you, from your governor to your state legislators.",
                             "es": "Todos los que te representan, desde tu gobernador hasta tus legisladores estatales."},
    "🗺️ Rep Map": {"en": "Explore any state's districts on a map, colored by party.",
                  "es": "Explora en un mapa los distritos de cualquier estado, coloreados por partido."},
    "📋 Bill Tracker": {"en": "Browse active state legislation, with plain-language summaries.",
                       "es": "Explora la legislación estatal activa, con resúmenes en lenguaje sencillo."},
    "🔍 District Compare": {"en": "Compare who represents two different addresses.",
                           "es": "Compara quién representa a dos direcciones distintas."},
    "🗳️ Candidates": {"en": "Research 2026 candidates and their stated positions.",
                     "es": "Investiga a los candidatos de 2026 y sus posturas declaradas."},
}

TRUST = [
    ("✅", "Official sources", "Census maps, state election offices, and the Voting Information Project — every deadline links its source."),
    ("⚖️", "Nonpartisan", "No endorsements, no ads. Party labels come straight from official records."),
    ("🔒", "Private", "No accounts, no cookies, no tracking. Your address is never stored."),
    ("🌎", "English & Español", "Switch languages anytime from the sidebar."),
]


def open_section(key: str):
    st.session_state["menu"] = key


def countdown_html() -> str:
    days = days_until_election()
    date = esc(format_date(ELECTION_DAY.isoformat()))
    if days > 1:
        num, label = str(days), t("days until Election Day")
    elif days == 1:
        num, label = "1", t("day until Election Day")
    elif days == 0:
        num, label = "🗳️", t("Election Day is today")
    else:
        return ""
    return (f'<div class="cl-countdown"><div class="cl-countdown-num">{num}</div>'
            f'<div class="cl-countdown-label">{esc(label)}<br>{date}</div></div>')


def render():
    st.markdown(
        '<div class="cl-hero cl-home-hero"><div class="cl-hero-text">'
        f'<span class="cl-eyebrow">{esc(t("Nonpartisan · All 50 states + DC · English / Español"))}</span>'
        f'<h1>{esc(t("Your guide to voting in 2026"))}</h1>'
        f'<p class="cl-hero-sub">{esc(t("Your complete guide to voting and civic life — in all 50 states and DC"))}. '
        f'{esc(t("Type your address once and every section uses it."))}</p>'
        f'</div>{countdown_html()}</div>',
        unsafe_allow_html=True,
    )

    section_label(t("Get started"))
    keys = list(FEATURES)
    for row in range(0, len(keys), 4):
        for col, key in zip(st.columns(4), keys[row:row + 4]):
            icon, title = t(key).split(" ", 1)
            with col, st.container(border=True):
                st.markdown(
                    f'<div class="cl-feature-icon" aria-hidden="true">{icon}</div>'
                    f'<div class="cl-feature-title">{esc(title)}</div>'
                    f'<div class="cl-feature-desc">{esc(pick(FEATURES[key]))}</div>',
                    unsafe_allow_html=True,
                )
                st.button(t("Open →"), key=f"home_{key}", on_click=open_section, args=(key,),
                          type="secondary", width="stretch")

    section_label(t("Why you can trust it"))
    items = "".join(
        f'<div class="cl-trust-item"><div class="cl-trust-icon" aria-hidden="true">{icon}</div>'
        f'<div><b>{esc(t(title))}</b><span>{esc(t(desc))}</span></div></div>'
        for icon, title, desc in TRUST
    )
    st.markdown(f'<div class="cl-trust">{items}</div>', unsafe_allow_html=True)
    st.caption(t("Data: OpenStates · U.S. Census TIGERweb · Google Civic API · unitedstates/congress-legislators · Wikidata · Google Gemini AI"))
