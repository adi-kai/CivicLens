"""District Compare: two addresses' representatives side by side."""
import streamlit as st

from civiclens.data.geocode import geocode
from civiclens.data.openstates import get_reps_by_location
from civiclens.helpers import (esc, get_chamber_label, html_block, is_federal, is_state,
                               party_badge, party_css)
from civiclens.states import STATES


def render():
    st.header("🔍 District Comparison")
    st.caption("Enter any two U.S. addresses — in the same state or different states — to compare their representatives side by side. Shared reps are highlighted in green.")

    col1, col2 = st.columns(2)
    with col1:
        addr1 = st.text_input("📍 Address 1", placeholder="123 Main St, Charlotte, NC 28201", key="dc_addr1")
    with col2:
        addr2 = st.text_input("📍 Address 2", placeholder="100 Congress Ave, Austin, TX 78701", key="dc_addr2")

    if st.button("Compare Districts", type="primary"):
        if not addr1.strip() or not addr2.strip():
            st.error("Please enter both addresses.")
        else:
            with st.spinner("Looking up representatives for both addresses…"):
                lat1, lng1, state1 = geocode(addr1)
                lat2, lng2, state2 = geocode(addr2)
                reps1 = get_reps_by_location(lat1, lng1) if lat1 else []
                reps2 = get_reps_by_location(lat2, lng2) if lat2 else []

            if not lat1: st.error(f"Could not locate: **{addr1}**")
            if not lat2: st.error(f"Could not locate: **{addr2}**")

            if reps1 or reps2:
                ids1, ids2     = {r.get("id") for r in reps1}, {r.get("id") for r in reps2}
                shared_ids     = ids1 & ids2

                def rep_card_compare(rep: dict, shared: bool) -> str:
                    name  = rep.get("name", "Unknown")
                    party = rep.get("party", "Unknown")
                    label = get_chamber_label(rep)
                    # State legislator labels don't name the state — needed when comparing across states
                    if is_state(rep):
                        rep_state = (rep.get("jurisdiction") or {}).get("name", "")
                        if rep_state:
                            label = f"{rep_state} {label}"
                    photo = rep.get("image", "")
                    css, badge = party_css(party), party_badge(party)
                    shared_html = (
                        ' <span style="background:#d4edda;color:#155724;padding:1px 8px;'
                        'border-radius:10px;font-size:0.72rem;font-weight:600;">Shared</span>'
                    ) if shared else ""
                    img_html = (f"<img src='{esc(photo)}' alt='{esc(name)}' width='45' "
                                f"style='border-radius:50%;float:right;margin-left:8px'/>" if photo else "")
                    return html_block(f"""
                    <div class="rep-card {css}">
                        {img_html}
                        <strong>{esc(name)}</strong>{shared_html}
                        <span class="party-badge {badge}">{esc(party)}</span><br>
                        <span style="color:var(--cl-muted);font-size:0.85rem">{esc(label)}</span>
                    </div>""")

                def sort_reps(reps):
                    return sorted(reps, key=lambda r: (0 if is_federal(r) else 1, r.get("name", "")))

                left_col, right_col = st.columns(2)
                with left_col:
                    st.subheader(f"📍 {addr1[:45]}{'…' if len(addr1) > 45 else ''}")
                    if state1 and state1 in STATES:
                        st.caption(STATES[state1]["name"])
                    if reps1:
                        for rep in sort_reps(reps1):
                            st.markdown(rep_card_compare(rep, rep.get("id") in shared_ids), unsafe_allow_html=True)
                    else:
                        st.warning("No representatives found.")
                with right_col:
                    st.subheader(f"📍 {addr2[:45]}{'…' if len(addr2) > 45 else ''}")
                    if state2 and state2 in STATES:
                        st.caption(STATES[state2]["name"])
                    if reps2:
                        for rep in sort_reps(reps2):
                            st.markdown(rep_card_compare(rep, rep.get("id") in shared_ids), unsafe_allow_html=True)
                    else:
                        st.warning("No representatives found.")

                if shared_ids:
                    st.success(f"✅ These addresses share **{len(shared_ids)}** representative(s) — marked in green above.")
                elif reps1 and reps2:
                    if state1 and state2 and state1 != state2:
                        st.info(
                            f"These addresses are in different states ({STATES[state1]['name']} and "
                            f"{STATES[state2]['name']}), so they don't share any representatives — each state "
                            f"has its own legislators and U.S. Senators."
                        )
                    else:
                        st.info("These addresses have entirely separate sets of representatives.")
