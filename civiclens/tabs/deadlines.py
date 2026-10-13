"""Deadlines: Election Day, hand-verified dates for some states, official links for all."""
import datetime

import streamlit as st

from civiclens.data.civic import get_official_resources
from civiclens.data.geocode import geocode
from civiclens.deadline_data import STATE_DEADLINES
from civiclens.helpers import address_input, esc, html_block, show_searched_address
from civiclens.i18n import format_date, format_range, month_day, pick, t
from civiclens.states import STATES
from civiclens.ui import official_links, page_header, section_label

ELECTION_DAY = "2026-11-03"


def today() -> datetime.date:
    return datetime.date.today()


def status_badge(last_day: str) -> str:
    """Passed / Today / In N days (within a week), or nothing for later deadlines.
    The next two days get a filled tag, the rest of the week an outlined one."""
    days = (datetime.date.fromisoformat(last_day) - today()).days
    if days < 0:
        label, style = t("Passed"), "plain"
    elif days == 0:
        label, style = t("Today"), "solid"
    elif days <= 7:
        label = t("Tomorrow") if days == 1 else t("In {days} days", days=days)
        style = "solid" if days <= 2 else "outline"
    else:
        return ""
    return f'<span class="cl-tag {style}">{label}</span>'


def deadline_card(name: str, when: str, note: str, first_day: str, last_day: str,
                  source_html: str = "", final: bool = False):
    """A deadline row with a ballot-stub tile for its (first) date. Passed deadlines are
    dimmed; `final` (Election Day) gets a solid tile."""
    passed = (datetime.date.fromisoformat(last_day) - today()).days < 0
    month, day = month_day(first_day)
    st.markdown(html_block(f"""
    <div class="rep-card" style="{'opacity:0.6' if passed else ''}">
        <div class="cl-deadline">
            <div class="cl-date-tile{' final' if final else ''}" aria-hidden="true">
                <div class="cl-date-month">{month}</div><div class="cl-date-day">{day}</div>
            </div>
            <div class="cl-deadline-body">
                <div class="cl-deadline-name">{name}</div>
                <div class="cl-deadline-when">{when}</div>
                <div class="cl-deadline-note">{note}</div>
                {source_html}
            </div>
            {status_badge(last_day)}
        </div>
    </div>"""), unsafe_allow_html=True)


def show_official_resources(state_abbr: str, state_name: str):
    section_label(t("🗳️ Official Resources"))
    official_links(get_official_resources(state_abbr))
    st.caption(t("Always verify deadlines directly with {state}'s official election authority — rules can change.", state=state_name))


def render():
    page_header(t("📅 Key Voting Deadlines — 2026"),
                t("Election Day itself is set federally — the same date nationwide. Registration and early-voting windows are set by each state, so enter your address below to see yours."),
                countdown=True)

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
                  ELECTION_DAY, ELECTION_DAY, final=True)

    if not dl_state:
        st.info(t("Enter your address above to see registration and early-voting resources for your state."))
        return

    data = STATE_DEADLINES.get(dl_state)
    if not data:
        st.info(t("Registration cutoffs, early-voting windows, and absentee deadlines for **{state}** vary and can change year to year, so we don't guess at exact dates here — use the official links below to get {state}'s current 2026 deadlines.",
                  state=dl_state_name))
        show_official_resources(dl_state, dl_state_name)
        return

    section_label(esc(t("{state} 2026 Deadlines", state=dl_state_name)))
    source = t("Source: {source}", source=t(data["source"]))
    for item in data["items"]:
        if "date" in item:
            when = format_date(item["date"], item.get("time", ""))
            first_day = last_day = item["date"]
        else:
            when = format_range(item["start"], item["end"])
            first_day, last_day = item["start"], item["end"]
        source_html = f'<div style="font-size:0.85rem"><a href="{esc(item["url"])}" target="_blank">{esc(source)}</a></div>'
        deadline_card(t(item["name"]), when, pick(item["note"]), first_day, last_day, source_html)

    verified = format_date(data["verified"], weekday=False)
    st.caption(t("Dates last verified against {site} on {date}.", site=data["site"], date=verified))
    show_official_resources(dl_state, dl_state_name)
