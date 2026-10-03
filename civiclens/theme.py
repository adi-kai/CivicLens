"""Fonts, card styles, and the sidebar color themes."""
import re

import streamlit as st

def apply_base_styles():
    """Fonts and the shared card/badge classes. Colors come from the --cl-* variables
    that apply_theme() sets, with light fallbacks."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'DM Serif Display', serif; }

    .rep-card {
        background: var(--cl-card, #f8f9fa);
        color: var(--cl-ink, #1a1a1a);
        border-left: 5px solid #888;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .rep-card.republican { border-left-color: #c0392b; }
    .rep-card.democrat   { border-left-color: #1a73e8; }
    .rep-card.other      { border-left-color: #7f8c8d; }

    .party-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-democrat   { background: #d6e4ff; color: #1a3c8f; }
    .badge-republican { background: #ffe0dd; color: #8b1a1a; }
    .badge-other      { background: #e8e8e8; color: #444; }

    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--cl-muted, #888);
        margin: 1.5rem 0 0.5rem 0;
    }

    .info-box {
        background: var(--cl-tint, #eaf3fb);
        color: var(--cl-ink, #1a1a1a);
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin-top: 0.5rem;
    }

    .map-legend {
        background: var(--cl-card, white);
        color: var(--cl-ink, #1a1a1a);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--cl-border, #e0e0e0);
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem 1.5rem;
        align-items: center;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }
    .legend-dot  { width: 14px; height: 14px; border-radius: 50%; display: inline-block; }

    .subject-tag {
        display: inline-block;
        padding: 1px 8px;
        border-radius: 12px;
        font-size: 0.72rem;
        background: #e9ecef;
        color: #495057;
        margin-right: 4px;
        margin-top: 4px;
    }
</style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# COLOR THEMES
# ─────────────────────────────────────────────
# paper, card, ink, accent, accent_ink, mark
PALETTES = {
    "civic-teal": ("Civic Teal",        "#F2F5F3", "#FFFFFF", "#14211F", "#0F6B5C", "#FFFFFF", "#F2B632"),
    "pine":       ("Pine & Marigold",   "#F1F4EE", "#FFFFFF", "#1B2E21", "#2F6B3F", "#FFFFFF", "#E9A23B"),
    "plum":       ("Plum & Mint",       "#F3F0F6", "#FFFFFF", "#2A1838", "#5B2A86", "#FFFFFF", "#7FE0BC"),
    "slate":      ("Slate & Tangerine", "#F4F6F8", "#FFFFFF", "#222B36", "#2F3E52", "#FFFFFF", "#F58A2E"),
    "midnight":   ("Midnight Violet",   "#15112B", "#201A3E", "#F0EEFB", "#9B8CFF", "#15112B", "#FFD166"),
    "classic":    ("Classic Civic",     "#F5F4EF", "#FFFFFF", "#17233B", "#1F3A68", "#FFFFFF", "#D9A93A"),
    "rwb":        ("Red, White & Blue", "#F7F8FB", "#FFFFFF", "#0A1F44", "#1D4ED8", "#FFFFFF", "#E11D2E"),
}

def apply_theme(key: str):
    """Sets the --cl-* CSS variables used by the app's own markup, and restyles Streamlit's
    widgets to match. Spans aren't recolored globally so party badges, subject tags, and
    other self-colored labels keep their colors."""
    _, paper, card, ink, accent, accent_ink, mark = PALETTES[key]
    st.markdown(f"""
    <style>
    :root {{
        --cl-paper: {paper}; --cl-card: {card}; --cl-ink: {ink};
        --cl-accent: {accent}; --cl-accent-ink: {accent_ink}; --cl-mark: {mark};
        --cl-muted:  color-mix(in srgb, {ink} 62%, {card});
        --cl-border: color-mix(in srgb, {ink} 16%, {card});
        --cl-tint:   color-mix(in srgb, {accent} 14%, {card});
    }}
    .stApp, [data-testid="stHeader"] {{ background: var(--cl-paper); }}
    .stApp, .stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{ color: var(--cl-ink); }}
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {{ color: var(--cl-muted); }}
    .stApp a {{ color: var(--cl-accent); }}
    .stApp hr {{ border-color: var(--cl-border); }}
    .stApp td, .stApp th {{ border-color: var(--cl-border) !important; }}
    mark {{ background: var(--cl-mark); }}
    [data-baseweb="tab-highlight"] {{ background-color: var(--cl-mark) !important; }}
    [data-testid="stSidebar"] {{ background: var(--cl-card); }}

    .stButton button, .stFormSubmitButton button {{
        background: var(--cl-accent); color: var(--cl-accent-ink); border: 0;
    }}
    .stButton button p, .stFormSubmitButton button p {{ color: var(--cl-accent-ink); }}
    .stButton button:hover, .stButton button:focus:not(:active) {{
        background: var(--cl-accent); color: var(--cl-accent-ink); filter: brightness(1.1);
    }}

    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
    [data-baseweb="textarea"] {{
        background: var(--cl-card) !important; border-color: var(--cl-border) !important;
    }}
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] div {{ color: var(--cl-ink) !important; caret-color: var(--cl-ink); }}
    [data-baseweb="input"] input::placeholder, [data-baseweb="textarea"] textarea::placeholder {{
        color: var(--cl-muted) !important;
    }}
    [data-baseweb="select"] svg {{ fill: var(--cl-ink); }}
    [data-baseweb="popover"] ul, [data-baseweb="popover"] li {{
        background: var(--cl-card) !important; color: var(--cl-ink) !important;
    }}
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {{
        background: var(--cl-tint) !important;
    }}

    [data-baseweb="radio"] > div:first-child {{ background: var(--cl-border) !important; }}
    [data-baseweb="radio"] > div:first-child > div {{ background: var(--cl-card) !important; }}
    [data-baseweb="radio"]:has(input:checked) > div:first-child {{ background: var(--cl-accent) !important; }}
    [data-baseweb="radio"]:has(input:checked) > div:first-child > div {{ background: var(--cl-accent-ink) !important; }}
    [data-baseweb="checkbox"] > span {{ border-color: var(--cl-border) !important; background-color: var(--cl-card) !important; }}
    [data-baseweb="checkbox"]:has(input:checked) > span {{
        border-color: var(--cl-accent) !important; background-color: var(--cl-accent) !important;
    }}

    [data-testid="stExpander"] details {{ background: var(--cl-card); border-color: var(--cl-border); }}
    [data-testid="stExpander"] summary svg {{ fill: var(--cl-ink); color: var(--cl-ink); }}
    </style>
    """, unsafe_allow_html=True)

def theme_ai_html(markup: str) -> str:
    """AI candidate cards come back with the light-theme inline colors from the prompt
    template; swap them for theme variables so the cards read correctly on every theme."""
    markup = re.sub(r"background:\s*#f8f9fa\b", "background:var(--cl-card)", markup, flags=re.I)
    markup = re.sub(r"(?<![-\w])color:\s*#(?:555|555555)\b", "color:var(--cl-muted)", markup, flags=re.I)
    markup = re.sub(r"(?<![-\w])color:\s*#(?:333|333333)\b", "color:var(--cl-ink)", markup, flags=re.I)
    markup = re.sub(r"(?<![-\w])color:\s*#1a73e8\b", "color:var(--cl-accent)", markup, flags=re.I)
    return markup
