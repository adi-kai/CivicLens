"""Home: banner with the Election Day countdown, section cards, and why the data is trustworthy."""
import streamlit as st

from civiclens.helpers import esc, plain
from civiclens.i18n import pick, t
from civiclens.ui import page_header, section_label

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


def render():
    page_header(t("Your guide to voting in 2026"),
                f'{t("Your complete guide to voting and civic life — in all 50 states and DC")}. '
                f'{t("Type your address once and every section uses it.")}',
                eyebrow=t("Nonpartisan · All 50 states + DC · English / Español"),
                countdown=True, css_class="cl-home-hero")

    section_label(t("Get started"))
    keys = list(FEATURES)
    for row in range(0, len(keys), 4):
        for col, (number, key) in zip(st.columns(4), enumerate(keys[row:row + 4], start=row + 1)):
            with col, st.container(border=True):
                st.markdown(
                    f'<div class="cl-feature-num">{number:02d}</div>'
                    f'<div class="cl-feature-title">{esc(plain(t(key)))}</div>'
                    f'<div class="cl-feature-desc">{esc(pick(FEATURES[key]))}</div>',
                    unsafe_allow_html=True,
                )
                st.button(t("Open →"), key=f"home_{key}", on_click=open_section, args=(key,),
                          type="secondary", width="stretch")

    section_label(t("Why you can trust it"))
    items = "".join(
        f'<div class="cl-trust-item"><b>{esc(t(title))}</b><span>{esc(t(desc))}</span></div>'
        for _, title, desc in TRUST
    )
    st.markdown(f'<div class="cl-trust">{items}</div>', unsafe_allow_html=True)
    st.caption(t("Data: OpenStates · U.S. Census TIGERweb · Google Civic API · unitedstates/congress-legislators · Wikidata · Google Gemini AI"))
