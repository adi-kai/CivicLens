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

# Leading emoji and symbols on a label ("📍 Address 1", "✅ Map data loaded!"). Translations
# keep them, so both languages share one key; the design shows text only. Spanish ¿ and ¡
# are kept.
_LEADING_ICON = re.compile(r"^[^\w¿¡\"'(\[]+\s*")

def plain(text: str) -> str:
    """A label without its leading emoji: plain("📍 Address 1") → "Address 1"."""
    return _LEADING_ICON.sub("", text or "")

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
    p = (party or "").lower()
    for key, color in PARTY_COLORS.items():
        if key in p:
            return color
    return "#7f8c8d"

def party_css(party: str) -> str:
    p = (party or "").lower()
    if "democrat" in p:   return "democrat"
    if "republican" in p: return "republican"
    return "other"

def party_badge(party: str) -> str:
    p = (party or "").lower()
    if "democrat" in p:   return "badge-democrat"
    if "republican" in p: return "badge-republican"
    return "badge-other"

def party_fill(party: str) -> tuple:
    p = (party or "").lower()
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
        st.markdown(f'<p class="cl-searched"><b>{t("Address:")}</b> {esc(address)}</p>',
                    unsafe_allow_html=True)

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

AT_LARGE_DISTRICTS = {"0", "AL", "AT-LARGE", "AT LARGE"}

def house_district_label(dist) -> str:
    """"NC-14" → "U.S. House — District 14". congress-legislators numbers a state's single
    seat 0, so "WY-0" (or "AL") is labeled at-large rather than "District WY-0"."""
    raw = str(dist or "").strip().upper()
    # Check before stripping the state prefix, which would turn "AT-LARGE" into "LARGE"
    dist = raw if raw in AT_LARGE_DISTRICTS else re.sub(r"^[A-Z]{2}-", "", raw)
    if dist.isdigit():
        dist = str(int(dist))
    if dist in AT_LARGE_DISTRICTS:
        return t("U.S. House At-Large")
    return t("U.S. House — District {district}", district=dist)

def get_chamber_label(rep: dict) -> str:
    roles = rep.get("current_role", {}) or {}
    dist  = roles.get("district", "")
    org   = roles.get("org_classification", "")
    title = roles.get("title", "")
    if is_federal(rep):
        if org == "upper":
            state_name = dist or (rep.get("jurisdiction", {}) or {}).get("name", "")
            return t("U.S. Senator — {state}", state=t(state_name)) if state_name else t("U.S. Senator")
        return house_district_label(dist)
    if is_state(rep):
        title = state_legislator_title(title, (rep.get("jurisdiction") or {}).get("name", ""))
    return t("{title} — District {district}", title=t(title), district=dist)

def party_label(party: str) -> str:
    """Party name for display. Styling helpers keep using the English name."""
    return t(party or "Unknown")

def district_key(raw) -> str:
    """Normalizes a district name so Census shapes and OpenStates / congress-legislators
    people can be joined on it. Numbers lose leading zeros and state prefixes
    ("037", "NC-14", "District 14" → "37", "14", "14"); a single at-large seat is "0".
    Named districts keep their words, ignoring case, spacing, punctuation, "and", and
    zero-padding: "Chittenden Southeast" / "Chittenden South East", "Belknap 01" /
    "Belknap 1", "Norfolk, Plymouth and Bristol" / "Norfolk Plymouth Bristol"."""
    s = str(raw or "").strip().upper()
    if s in ("", "NONE"):
        return ""
    if "AT LARGE" in s or "AT-LARGE" in s:
        return "0"
    s = re.sub(r"^[A-Z]{2}-(?=\d)", "", s)
    # "Congressional District 10", "State House District Hillsborough 10"
    s = re.sub(r"^(?:.*\s)?DISTRICT\s+(?=\S)", "", s)
    if s.isdigit():
        return str(int(s))
    s = re.sub(r"\bAND\b", " ", s)
    s = re.sub(r"\b0+(?=\d)", "", s)
    return re.sub(r"[^A-Z0-9]+", "", s)

def build_rep_lookup(reps: list) -> dict:
    """{district_key: [reps]}. A list, because many states elect more than one member
    per district (Vermont, New Hampshire, Arizona, New Jersey, Washington, ...)."""
    lookup = {}
    for rep in reps:
        roles = rep.get("current_role", {}) or {}
        key = district_key(roles.get("district", ""))
        if key:
            lookup.setdefault(key, []).append(rep)
    return lookup
