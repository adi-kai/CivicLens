"""Shared page pieces: the banner header, section labels, and small display helpers.
Colors come from the --cl-* theme variables, so every piece works on every theme."""
import datetime

import streamlit as st

from civiclens.helpers import esc

ELECTION_DAY = datetime.date(2026, 11, 3)


def page_header(heading: str, subtitle: str = ""):
    """The colored banner at the top of each section. `heading` is the section's title
    with its emoji first ("📍 Find Your Polling Place"); the emoji becomes the icon."""
    icon, _, title = heading.partition(" ")
    sub = f'<p class="cl-hero-sub">{esc(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<div class="cl-hero"><div class="cl-hero-icon" aria-hidden="true">{icon}</div>'
        f'<div class="cl-hero-text"><h1>{esc(title)}</h1>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def section_label(text: str):
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)


def days_until_election(today: datetime.date = None) -> int:
    return (ELECTION_DAY - (today or datetime.date.today())).days
