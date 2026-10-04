"""Small shared helpers: rate limiting, party styling, HTML escaping/flattening, rep labels."""
import html
import re
import time

import streamlit as st

from civiclens.i18n import t

def esc(value) -> str:
    """Escapes text from users or APIs before it goes into HTML, so a name with "&" or "<"
    displays as written and can't add its own tags. Also safe inside quoted attributes."""
    return html.escape("" if value is None else str(value), quote=True)

def rate_limit_check(key: str, max_calls: int = 10, window: int = 60):
    """Block if user has made too many calls in the time window."""
    now = time.time()
    call_log = st.session_state.get(key, [])
    # Drop calls outside the window
    call_log = [t for t in call_log if now - t < window]
    if len(call_log) >= max_calls:
        return False
    call_log.append(now)
    st.session_state[key] = call_log
    return True

PARTY_COLORS = {
    "democratic": "#1a73e8", "democrat": "#1a73e8",
    "republican": "#c0392b",
    "libertarian": "#f39c12",
    "green": "#27ae60",
}

def party_color(party: str) -> str:
    p = party.lower()
    for key, color in PARTY_COLORS.items():
        if key in p:
            return color
    return "#7f8c8d"

def party_css(party: str) -> str:
    p = party.lower()
    if "democrat" in p:   return "democrat"
    if "republican" in p: return "republican"
    return "other"

def party_badge(party: str) -> str:
    p = party.lower()
    if "democrat" in p:   return "badge-democrat"
    if "republican" in p: return "badge-republican"
    return "badge-other"

def party_fill(party: str) -> tuple:
    p = party.lower()
    if "democrat" in p:   return "#1a73e8", 0.25
    if "republican" in p: return "#c0392b", 0.25
    return "#888888", 0.15

def html_block(markup: str) -> str:
    """Flattens HTML for st.markdown(unsafe_allow_html=True). Markdown treats a blank line
    followed by an indented line as a code block, so an empty optional line (no photo,
    no subject tags) or indented AI output would show up as raw HTML text."""
    return "\n".join(line.strip() for line in str(markup).splitlines() if line.strip())

ADDRESS_KEY = "address"
_SAVED_ADDRESS_KEY = "_saved_address"

def _save_address():
    st.session_state[_SAVED_ADDRESS_KEY] = st.session_state[ADDRESS_KEY]

def address_input(label: str, placeholder: str = "123 Main St, Charlotte, NC 28201",
                  help: str = None) -> str:
    """The address box every section shares, so an address typed once carries over when
    you switch sections. Streamlit forgets a widget's value on any run where it isn't
    drawn (e.g. a visit to Home), so the value is also kept under a plain session key
    and restored here before the widget is created."""
    st.session_state[ADDRESS_KEY] = st.session_state.get(_SAVED_ADDRESS_KEY, "")
    return st.text_input(label, key=ADDRESS_KEY, placeholder=placeholder, help=help,
                         on_change=_save_address)

def sanitize_ai_html(markup: str) -> str:
    """AI candidate cards are rendered as HTML, and the model's input includes web search
    results we don't control. Keep the formatting tags, but drop anything that could run
    code or load other pages: script-like tags, on* event attributes, and javascript: links."""
    markup = str(markup or "")
    markup = re.sub(r"(?is)<(script|style|iframe|object|embed|form)\b.*?</\1\s*>", "", markup)
    markup = re.sub(r"(?is)</?(script|style|iframe|object|embed|form|input|button|link|meta|base)\b[^>]*>", "", markup)

    def clean_tag(m):
        tag = re.sub(r"""(?is)\s+on\w+\s*=\s*(".*?"|'.*?'|[^\s>]+)""", "", m.group(0))
        return re.sub(r"""(?is)\b(href|src)\s*=\s*(["']?)\s*javascript:[^"'>]*\2""", r'\1="#"', tag)
    return re.sub(r"<[^<>]+>", clean_tag, markup)

def show_searched_address(address: str):
    """Prints the address actually being used, right above whatever results follow."""
    if address and address.strip():
        st.markdown(f"""
        <div class="info-box" style="padding:0.55rem 1rem;margin:0 0 0.9rem 0;">
            📍 <strong>{t("Address:")}</strong> {esc(address)}
        </div>
        """, unsafe_allow_html=True)

def is_federal(rep: dict) -> bool:
    return rep.get("jurisdiction", {}).get("classification", "") == "country"

def is_state(rep: dict) -> bool:
    return rep.get("jurisdiction", {}).get("classification", "") == "state"

def state_legislator_title(title: str, jurisdiction_name: str = "") -> str:
    """Prefixes a state legislator's title with "State" (e.g. "Senator" → "State Senator")
    so state legislators aren't confused with members of Congress. D.C. Council is not a
    state legislature, so its titles are left alone."""
    title = (title or "").strip()
    if not title or jurisdiction_name == "District of Columbia" or title.lower().startswith("state "):
        return title
    return f"State {title}"

def get_chamber_label(rep: dict) -> str:
    roles = rep.get("current_role", {}) or {}
    dist  = roles.get("district", "")
    org   = roles.get("org_classification", "")
    title = roles.get("title", "")
    if is_federal(rep):
        if org == "upper":
            state_name = dist or (rep.get("jurisdiction", {}) or {}).get("name", "")
            return t("U.S. Senator — {state}", state=t(state_name)) if state_name else t("U.S. Senator")
        return t("U.S. House — District {district}", district=dist)
    if is_state(rep):
        title = state_legislator_title(title, (rep.get("jurisdiction") or {}).get("name", ""))
    return t("{title} — District {district}", title=t(title), district=dist)

def party_label(party: str) -> str:
    """Party name for display. Styling helpers keep using the English name."""
    return t(party or "Unknown")

def build_rep_lookup(reps: list) -> dict:
    lookup = {}
    for rep in reps:
        roles = rep.get("current_role", {}) or {}
        dist  = str(roles.get("district", "")).strip()
        # Strip any state prefix (e.g. "NC-14" → "14", "NC-" → "")
        dist = re.sub(r"^[A-Z]{2}-", "", dist.upper()).strip()
        # Extract the numeric part and convert to int then str to drop leading zeros
        # e.g. "037" → "37", "014" → "14", "14" → "14"
        m = re.search(r"\d+", dist)
        key = str(int(m.group())) if m else dist
        if key:
            lookup[key] = rep
    return lookup
