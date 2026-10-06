"""Deadlines: Election Day, hand-verified dates for some states, official links for all."""
import datetime

import streamlit as st

from civiclens.data.civic import get_official_resources
from civiclens.data.geocode import geocode
from civiclens.deadline_data import STATE_DEADLINES
from civiclens.helpers import address_input, html_block, show_searched_address
from civiclens.i18n import format_date, format_range, month_day, pick, t
from civiclens.states import STATES
from civiclens.ui import page_header

ELECTION_DAY = "2026-11-03"


def today() -> datetime.date:
    return datetime.date.today()


def status_badge(last_day: str) -> str:
    """Passed / Today / In N days (within a week), or nothing for later deadlines.
    Badges set their own background and text color, so they read on every theme."""
    days = (datetime.date.fromisoformat(last_day) - today()).days
    if days < 0:
        label, bg, fg = t("Passed"), "#e8e8e8", "#555555"
    elif days == 0:
        label, bg, fg = t("Today"), "#ffe0dd", "#8b1a1a"
    elif days <= 7:
        label = t("Tomorrow") if days == 1 else t("In {days} days", days=days)
        bg, fg = "#fff3cd", "#7a5a00"
    else:
        return ""
    return (f'<span style="background:{bg};color:{fg};padding:1px 8px;border-radius:10px;'
            f'font-size:0.72rem;font-weight:600;margin-left:6px">{label}</span>')


def deadline_card(name: str, when: str, note: str, first_day: str, last_day: str,
                  source_html: str = ""):
    """A deadline with a calendar tile for its (first) date. Passed deadlines are dimmed."""
    passed = (datetime.date.fromisoformat(last_day) - today()).days < 0
    month, day = month_day(first_day)
    st.markdown(html_block(f"""
    <div class="rep-card other" style="{'opacity:0.6' if passed else ''}">
        <div class="cl-deadline">
            <div class="cl-date-tile" aria-hidden="true">
                <div class="cl-date-month">{month}</div><div class="cl-date-day">{day}</div>
            </div>
            <div class="cl-deadline-body">
                <strong>{name}</strong>{status_badge(last_day)}<br>
                <em style="font-size:0.93rem">{when}</em><br>
                <span style="color:var(--cl-muted);font-size:0.9rem">{note}</span>
                {"<br>" + source_html if source_html else ""}
            </div>
        </div>
    </div>"""), unsafe_allow_html=True)


def show_official_resources(state_abbr: str, state_name: str):
    st.markdown(f'<p class="section-label">{t("🗳️ Official Resources")}</p>', unsafe_allow_html=True)
    for label, url in get_official_resources(state_abbr):
        st.markdown(f"- [{label}]({url})")
    st.caption(t("Always verify deadlines directly with {state}'s official election authority — rules can change.", state=state_name))


def render():
    page_header(t("📅 Key Voting Deadlines — 2026"),
                t("Election Day itself is set federally — the same date nationwide. Registration and early-voting windows are set by each state, so enter your address below to see yours."))

    dl_address = address_input(t("Enter your address"))

    dl_state = None
    if dl_address.strip():
        with st.spinner(t("Locating address…")):
            _, _, dl_state = geocode(dl_address)
        if not dl_state:
            st.warning(t("Could not determine the state for that address — try adding your city and zip code."))

    dl_state_name = t(STATES.get(dl_state, {}).get("name", ""))

    show_searched_address(dl_address)

    deadline_card(t("Election Day"), format_date(ELECTION_DAY),
                  t("Polls open per your state and county's posted hours. Set by federal law — the same date nationwide."),
                  ELECTION_DAY, ELECTION_DAY)

    if not dl_state:
        st.info(t("Enter your address above to see registration and early-voting resources for your state."))
        return

    data = STATE_DEADLINES.get(dl_state)
    if not data:
        st.info(t("Registration cutoffs, early-voting windows, and absentee deadlines for **{state}** vary and can change year to year, so we don't guess at exact dates here — use the official links below to get {state}'s current 2026 deadlines.",
                  state=dl_state_name))
        show_official_resources(dl_state, dl_state_name)
        return

    st.markdown(f'<p class="section-label">🏛️ {t("{state} 2026 Deadlines", state=dl_state_name)}</p>',
                unsafe_allow_html=True)
    source = t("Source: {source}", source=t(data["source"]))
    for item in data["items"]:
        if "date" in item:
            when = format_date(item["date"], item.get("time", ""))
            first_day = last_day = item["date"]
        else:
            when = format_range(item["start"], item["end"])
            first_day, last_day = item["start"], item["end"]
        source_html = f'<span style="font-size:0.8rem"><a href="{item["url"]}" target="_blank">{source}</a></span>'
        deadline_card(t(item["name"]), when, pick(item["note"]), first_day, last_day, source_html)

    verified = format_date(data["verified"], weekday=False)
    st.caption(t("Dates last verified against {site} on {date}.", site=data["site"], date=verified))
    show_official_resources(dl_state, dl_state_name)
