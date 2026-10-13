"""Bill Tracker: recent and searched state bills, with AI summaries."""
import streamlit as st

from civiclens.data.ai import get_bill_summary
from civiclens.data.openstates import get_state_bills
from civiclens.helpers import esc, html_block, party_label, plain, state_legislator_title
from civiclens.i18n import current_lang, label_func, t
from civiclens.states import DEFAULT_STATE, STATES
from civiclens.ui import page_header


def bill_abstract(bill: dict) -> str:
    """The first non-empty official abstract, or "" (some states, e.g. NC, publish none)."""
    return next((a["abstract"].strip() for a in bill.get("abstracts") or []
                 if (a.get("abstract") or "").strip()), "")


def primary_sponsor(bill: dict) -> tuple:
    """(name, party, title) of the primary sponsor, falling back to the first sponsor.
    Party and title live on sponsorship["person"]; name and title can be empty."""
    sponsors = bill.get("sponsorships") or []
    primary = next((s for s in sponsors if s.get("primary")), sponsors[0] if sponsors else None)
    person = (primary or {}).get("person") or {}
    name = (primary or {}).get("name") or person.get("name") or ""
    return name, person.get("party") or "", (person.get("current_role") or {}).get("title", "")


def subject_tags(bill: dict, limit: int = 3) -> list:
    """Up to `limit` subject terms. Some states (e.g. NC) send one long "A; B; C" string
    per subject instead of separate terms, so those are split apart."""
    terms = []
    for subject in bill.get("subject") or []:
        for term in str(subject).split(";"):
            term = term.strip()
            if term and term not in terms:
                terms.append(term)
    return terms[:limit]


def render():
    page_header(t("📋 State Bill Tracker"),
                t("Browse and search active state legislation for any state · Via OpenStates · Updated every 30 min"))

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input(t("Search by keyword"), placeholder=t("e.g. school funding, gun safety, Medicaid"))
    with col2:
        chamber = st.selectbox(t("Chamber"), ["All", "House", "Senate"], format_func=label_func())
    with col3:
        bill_state_abbrs = sorted(STATES.keys())
        bill_state = st.selectbox(t("State"), bill_state_abbrs, index=bill_state_abbrs.index(DEFAULT_STATE), key="bill_state")

    search_clicked = st.button(t("Search Bills"), type="primary")

    if "bills" not in st.session_state or search_clicked:
        load_query   = query      if search_clicked else ""
        load_chamber = chamber    if search_clicked else "All"
        load_state   = bill_state if search_clicked else DEFAULT_STATE
        with st.spinner(t("Loading bills…")):
            bills_result, bills_err = get_state_bills(load_state, query=load_query, chamber=load_chamber)
            st.session_state.bills     = bills_result
            st.session_state.bills_err = bills_err
            # The state the bills were actually loaded for — the dropdown can change without a new search
            st.session_state.bills_state = load_state

    bills     = st.session_state.get("bills", [])
    bills_err = st.session_state.get("bills_err", "")
    bills_state_name = STATES.get(st.session_state.get("bills_state", DEFAULT_STATE), {}).get("name", "")
    lang = current_lang()

    if bills_err:
        st.error(t("Could not load bills — {err}", err=bills_err))
    elif not bills:
        st.info(t("No bills found. Try a different keyword or chamber."))
    else:
        st.caption(t("Showing {count} bills — sorted by most recent activity", count=len(bills)))
        for bill in bills:
            identifier  = bill.get("identifier", "—")
            title       = bill.get("title", t("No title"))
            latest_act  = bill.get("latest_action_description", t("No recent action"))
            latest_date = (bill.get("latest_action_date") or "")[:10]
            url         = bill.get("openstates_url", "#")
            bill_id     = bill.get("id", identifier)
            abstract    = bill_abstract(bill)
            subjects    = subject_tags(bill)
            sponsor_name, sponsor_party, sponsor_title = primary_sponsor(bill)
            sponsor_name  = sponsor_name or t("Unknown")
            sponsor_title = state_legislator_title(sponsor_title, bills_state_name)
            tags_html     = "".join(f'<span class="subject-tag">{esc(s)}</span>' for s in subjects)
            party_part    = f" ({party_label(sponsor_party)})" if sponsor_party else ""
            if sponsor_title:
                sponsor_line = t("{title} {name}{party}", title=t(sponsor_title), name=sponsor_name, party=party_part)
            else:
                sponsor_line = f"{sponsor_name}{party_part}"
            st.markdown(html_block(f"""
            <div class="rep-card">
                <div><span class="cl-bill-id">{esc(identifier)}</span><span class="cl-bill-title">{esc(title)}</span></div>
                <div class="cl-bill-meta">{esc(sponsor_line)} · {esc(latest_date)} · {esc(latest_act)}</div>
                {f"<div>{tags_html}</div>" if tags_html else ""}
                <div style="margin-top:0.4rem;font-size:0.9rem"><a href="{esc(url)}" target="_blank">{t("View full bill on OpenStates →")}</a></div>
            </div>
            """), unsafe_allow_html=True)

            # Summaries are kept per language, so switching languages asks for a fresh one
            summary_key = f"summary_{bill_id}_{lang}"
            if st.button(plain(t("✨ Plain-English Summary")), key=f"btn_{bill_id}", type="secondary"):
                with st.spinner(t("Summarizing…")):
                    st.session_state[summary_key] = get_bill_summary(bill_id, title, latest_act, bills_state_name, lang, abstract)
            if summary_key in st.session_state:
                st.info(st.session_state[summary_key])
                if not st.session_state[summary_key].startswith("⚠️"):
                    st.caption(t("Based on the official bill summary.") if abstract else
                               t("Based on the bill title only — no official summary was published for this bill."))
