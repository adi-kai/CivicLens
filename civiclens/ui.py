"""Shared page pieces: the page header, section labels, the Election Day countdown, and
official link lists. Colors come from the --cl-* theme variables, so every piece works
on every theme."""
import datetime

import streamlit as st

from civiclens.helpers import esc, plain
from civiclens.i18n import format_date, t

ELECTION_DAY = datetime.date(2026, 11, 3)


def days_until_election(today: datetime.date = None) -> int:
    return (ELECTION_DAY - (today or datetime.date.today())).days


def countdown_html() -> str:
    """"21 days until Election Day" with the date, or "" once Election Day has passed."""
    days = days_until_election()
    date = esc(format_date(ELECTION_DAY.isoformat(), weekday=False))
    if days > 1:
        num, label = str(days), t("days until Election Day")
    elif days == 1:
        num, label = "1", t("day until Election Day")
    elif days == 0:
        num, label = t("Today"), t("Election Day is today")
    else:
        return ""
    return (f'<div class="cl-countdown"><div class="cl-countdown-num">{esc(num)}</div>'
            f'<div class="cl-countdown-label">{esc(label)}<br><span>{date}</span></div></div>')


def page_header(heading: str, subtitle: str = "", eyebrow: str = "", countdown: bool = False,
                css_class: str = ""):
    """The title block at the top of each section: an optional small eyebrow line, the
    serif title, a subtitle, and optionally the Election Day countdown on the right. A
    leading emoji on `heading` ("📍 Find Your Polling Place") is dropped."""
    sub = f'<p class="cl-hero-sub">{esc(subtitle)}</p>' if subtitle else ""
    top = f'<div class="cl-eyebrow">{esc(eyebrow)}</div>' if eyebrow else ""
    st.markdown(
        f'<div class="cl-hero {css_class}"><div class="cl-hero-text">{top}'
        f'<h1>{esc(plain(heading))}</h1>{sub}</div>{countdown_html() if countdown else ""}</div>',
        unsafe_allow_html=True,
    )


def section_label(text: str):
    """A small ruled heading inside a section. Callers pass already-escaped text."""
    st.markdown(f'<p class="section-label">{plain(text)}</p>', unsafe_allow_html=True)


def official_links(links: list):
    """A ruled list of (label, url) links. A label ending in " — Source" (how
    get_official_resources names them, e.g. "Register to Vote — NCSBE") shows the source
    as a small tag on the right."""
    rows = ""
    for label, url in links:
        text, _, source = label.rpartition(" — ") if " — " in label else (label, "", "")
        tag = f"<span>{esc(source)}</span>" if source else ""
        rows += f'<a href="{esc(url)}" target="_blank">{esc(text)}{tag}</a>'
    st.markdown(f'<div class="cl-links">{rows}</div>', unsafe_allow_html=True)
