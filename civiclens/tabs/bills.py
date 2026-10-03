"""Bill Tracker: recent and searched state bills, with AI summaries."""
import streamlit as st

from civiclens.data.ai import get_bill_summary
from civiclens.data.openstates import get_state_bills
from civiclens.helpers import html_block, party_css, state_legislator_title
from civiclens.states import DEFAULT_STATE, STATES


def render():
    st.header("📋 State Bill Tracker")
    st.caption("Browse and search active state legislation for any state · Via OpenStates · Updated every 30 min")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input("Search by keyword", placeholder="e.g. school funding, gun safety, Medicaid")
    with col2:
        chamber = st.selectbox("Chamber", ["All", "House", "Senate"])
    with col3:
        bill_state_abbrs = sorted(STATES.keys())
        bill_state = st.selectbox("State", bill_state_abbrs, index=bill_state_abbrs.index(DEFAULT_STATE), key="bill_state")

    search_clicked = st.button("Search Bills", type="primary")

    if "bills" not in st.session_state or search_clicked:
        load_query   = query      if search_clicked else ""
        load_chamber = chamber    if search_clicked else "All"
        load_state   = bill_state if search_clicked else DEFAULT_STATE
        with st.spinner("Loading bills…"):
            bills_result, bills_err = get_state_bills(load_state, query=load_query, chamber=load_chamber)
            st.session_state.bills     = bills_result
            st.session_state.bills_err = bills_err
            # The state the bills were actually loaded for — the dropdown can change without a new search
            st.session_state.bills_state = load_state

    bills     = st.session_state.get("bills", [])
    bills_err = st.session_state.get("bills_err", "")
    bills_state_name = STATES.get(st.session_state.get("bills_state", DEFAULT_STATE), {}).get("name", "")

    if bills_err:
        st.error(f"Could not load bills — {bills_err}")
    elif not bills:
        st.info("No bills found. Try a different keyword or chamber.")
    else:
        st.caption(f"Showing {len(bills)} bills — sorted by most recent activity")
        for bill in bills:
            identifier  = bill.get("identifier", "—")
            title       = bill.get("title", "No title")
            latest_act  = bill.get("latest_action_description", "No recent action")
            latest_date = (bill.get("latest_action_date") or "")[:10]
            url         = bill.get("openstates_url", "#")
            bill_id     = bill.get("id", identifier)
            subjects    = (bill.get("subject") or [])[:3]
            sponsors    = bill.get("sponsorships", [])
            primary     = next((s for s in sponsors if s.get("primary")), sponsors[0] if sponsors else None)
            sponsor_person = (primary or {}).get("person") or {}
            sponsor_name  = (primary or {}).get("name") or sponsor_person.get("name") or "Unknown"
            sponsor_party = sponsor_person.get("party") or ""
            sponsor_title = state_legislator_title((sponsor_person.get("current_role") or {}).get("title", ""), bills_state_name)
            css           = party_css(sponsor_party)
            tags_html     = "".join(f'<span class="subject-tag">{s}</span>' for s in subjects)
            st.markdown(html_block(f"""
            <div class="rep-card {css}" style="padding:0.85rem 1.1rem">
                <strong>{identifier}</strong>
                <span style="color:var(--cl-ink);font-size:0.97rem"> — {title}</span><br>
                <span style="color:var(--cl-muted);font-size:0.83rem">
                    👤 {sponsor_title + ' ' if sponsor_title else ''}{sponsor_name}{' (' + sponsor_party + ')' if sponsor_party else ''}
                    &nbsp;·&nbsp; 📅 {latest_date}
                    &nbsp;·&nbsp; {latest_act}
                </span>
                {"<br>" + tags_html if tags_html else ""}
                <br><a href="{url}" target="_blank" style="font-size:0.8rem;color:var(--cl-accent);">View full bill on OpenStates →</a>
            </div>
            """), unsafe_allow_html=True)

            summary_key = f"summary_{bill_id}"
            if st.button("✨ Plain-English Summary", key=f"btn_{bill_id}"):
                with st.spinner("Summarizing…"):
                    st.session_state[summary_key] = get_bill_summary(bill_id, title, latest_act, bills_state_name)
            if summary_key in st.session_state:
                st.info(f"💡 {st.session_state[summary_key]}")
