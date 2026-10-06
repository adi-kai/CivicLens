"""Fonts, card styles, and the sidebar color themes."""
import re

import streamlit as st

def apply_base_styles():
    """Fonts and the shared card/badge classes. Colors come from the --cl-* variables
    that apply_theme() sets, with light fallbacks."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'DM Serif Display', serif; letter-spacing: -0.01em; }

    /* ── Layout ── */
    .block-container, [data-testid="stMainBlockContainer"] { max-width: 1120px; padding-top: 2.2rem; }
    [data-testid="stHeaderActionElements"] { display: none; }   /* heading anchor-link icons */

    /* ── Page banner ── */
    .cl-hero {
        position: relative; overflow: hidden;
        display: flex; align-items: center; gap: 1.1rem;
        padding: 1.5rem 1.75rem; margin: 0 0 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, var(--cl-accent) 0%,
                    color-mix(in srgb, var(--cl-accent) 72%, #000) 100%);
        color: var(--cl-accent-ink);
        box-shadow: 0 14px 34px -18px color-mix(in srgb, var(--cl-accent) 80%, transparent);
    }
    .cl-hero::before, .cl-hero::after {
        content: ""; position: absolute; border-radius: 50%; pointer-events: none;
    }
    .cl-hero::before { width: 240px; height: 240px; right: -70px; top: -110px;
        background: color-mix(in srgb, var(--cl-mark) 30%, transparent); }
    .cl-hero::after  { width: 140px; height: 140px; right: 120px; bottom: -90px;
        background: color-mix(in srgb, var(--cl-accent-ink) 10%, transparent); }
    .cl-hero-icon {
        flex: 0 0 auto; width: 58px; height: 58px; border-radius: 16px;
        display: flex; align-items: center; justify-content: center; font-size: 1.85rem;
        background: color-mix(in srgb, var(--cl-accent-ink) 16%, transparent);
        position: relative; z-index: 1;
    }
    .cl-hero-text { position: relative; z-index: 1; min-width: 0; }
    .stApp .cl-hero h1 {
        color: var(--cl-accent-ink); margin: 0; padding: 0;
        font-family: 'DM Serif Display', serif !important; font-weight: 400;
        font-size: 2.1rem; line-height: 1.15;
    }
    .stApp .cl-hero .cl-hero-sub {
        color: color-mix(in srgb, var(--cl-accent-ink) 82%, transparent);
        margin: 0.35rem 0 0; font-size: 0.98rem; line-height: 1.45;
    }
    @media (max-width: 640px) {
        .cl-hero { padding: 1.15rem 1.2rem; gap: 0.85rem; border-radius: 14px; }
        .cl-hero-icon { width: 46px; height: 46px; font-size: 1.45rem; border-radius: 12px; }
        .stApp .cl-hero h1 { font-size: 1.5rem; }
    }

    /* ── Home ── */
    .cl-home-hero { padding: 2.2rem 2rem; flex-wrap: wrap; justify-content: space-between; gap: 1.5rem; }
    .cl-home-hero .cl-hero-text { flex: 1 1 420px; }
    .cl-eyebrow {
        display: inline-block; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; padding: 4px 10px; border-radius: 999px; margin-bottom: 0.7rem;
        background: color-mix(in srgb, var(--cl-accent-ink) 16%, transparent);
    }
    .stApp .cl-home-hero h1 { font-size: 2.6rem; }
    .cl-countdown {
        position: relative; z-index: 1; text-align: center; min-width: 170px;
        padding: 1rem 1.3rem; border-radius: 16px;
        background: color-mix(in srgb, var(--cl-accent-ink) 14%, transparent);
        border: 1px solid color-mix(in srgb, var(--cl-accent-ink) 22%, transparent);
    }
    .cl-countdown-num { font-family: 'DM Serif Display', serif; font-size: 3rem; line-height: 1; }
    .cl-countdown-label { font-size: 0.82rem; margin-top: 0.3rem; opacity: 0.9; }
    @media (max-width: 640px) {
        .cl-home-hero { padding: 1.4rem 1.2rem; }
        .stApp .cl-home-hero h1 { font-size: 1.85rem; }
        .cl-countdown { width: 100%; }
        .cl-eyebrow { font-size: 0.66rem; letter-spacing: 0.04em; }
        .cl-feature-desc { min-height: 0; }
    }
    .cl-feature-icon {
        width: 44px; height: 44px; border-radius: 12px; font-size: 1.35rem;
        display: flex; align-items: center; justify-content: center;
        background: var(--cl-tint, #eaf3fb); margin-bottom: 0.6rem;
    }
    .cl-feature-title { font-weight: 700; font-size: 1.02rem; color: var(--cl-ink, #1a1a1a); }
    .cl-feature-desc  { font-size: 0.88rem; color: var(--cl-muted, #666); line-height: 1.45;
                        margin: 0.25rem 0 0.4rem; min-height: 4.35em; }
    .cl-trust { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 0.8rem; margin: 0.4rem 0 1rem; }
    .cl-trust-item {
        display: flex; gap: 0.75rem; align-items: flex-start; padding: 0.9rem 1rem;
        border-radius: 14px; background: var(--cl-card, #fff);
        border: 1px solid var(--cl-border, #e0e0e0);
    }
    .cl-trust-item b { display: block; color: var(--cl-ink, #1a1a1a); margin-bottom: 2px; }
    .cl-trust-item span { display: block; font-size: 0.86rem; color: var(--cl-muted, #666); line-height: 1.45; }
    .cl-trust-icon { font-size: 1.3rem; line-height: 1.2; }

    /* ── Sidebar brand ── */
    .cl-brand { display: flex; align-items: center; gap: 0.7rem; padding: 0.2rem 0 0.9rem; }
    .cl-brand-mark {
        width: 42px; height: 42px; border-radius: 12px; font-size: 1.35rem;
        display: flex; align-items: center; justify-content: center;
        background: var(--cl-accent, #0F6B5C);
        box-shadow: 0 6px 16px -8px var(--cl-accent, #0F6B5C);
    }
    .cl-brand-name { font-family: 'DM Serif Display', serif; font-size: 1.45rem; line-height: 1;
                     color: var(--cl-ink, #1a1a1a); }
    .cl-brand-tag  { font-size: 0.76rem; color: var(--cl-muted, #666); margin-top: 3px; }

    /* ── Cards ── */
    .rep-card {
        background: var(--cl-card, #f8f9fa);
        color: var(--cl-ink, #1a1a1a);
        border: 1px solid var(--cl-border, #e6e6e6);
        border-left: 5px solid #888;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 6px 18px -12px rgba(0,0,0,0.18);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .rep-card:hover { transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 12px 24px -14px rgba(0,0,0,0.25); }
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
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: var(--cl-muted, #888);
        margin: 1.7rem 0 0.6rem 0;
        display: flex; align-items: center; gap: 0.55rem;
    }
    .section-label::after {
        content: ""; flex: 1; height: 1px; background: var(--cl-border, #e0e0e0);
    }

    .info-box {
        background: var(--cl-tint, #eaf3fb);
        color: var(--cl-ink, #1a1a1a);
        border-left: 4px solid var(--cl-accent, #0F6B5C);
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-top: 0.5rem;
    }

    /* ── Deadline calendar tile ── */
    .cl-deadline { display: flex; gap: 1rem; align-items: flex-start; }
    .cl-date-tile {
        flex: 0 0 62px; text-align: center; border-radius: 12px; overflow: hidden;
        border: 1px solid var(--cl-border, #e0e0e0); background: var(--cl-card, #fff);
    }
    .cl-date-month {
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
        padding: 3px 0; background: var(--cl-accent, #0F6B5C); color: var(--cl-accent-ink, #fff);
    }
    .cl-date-day { font-family: 'DM Serif Display', serif; font-size: 1.7rem; line-height: 1.25;
                   color: var(--cl-ink, #1a1a1a); padding: 2px 0 4px; }
    .cl-deadline-body { flex: 1; min-width: 0; }

    /* ── Ballot ── */
    .cl-race-head { display: flex; justify-content: space-between; align-items: baseline;
                    gap: 0.75rem; flex-wrap: wrap; }
    .cl-race-office { font-weight: 700; font-size: 1.05rem; }
    .cl-race-district { font-size: 0.85rem; color: var(--cl-muted, #666); }
    .cl-pill {
        display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 2px 9px;
        border-radius: 999px; background: var(--cl-tint, #eaf3fb); color: var(--cl-accent, #0F6B5C);
        white-space: nowrap;
    }
    .cl-candidate {
        display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
        padding: 0.55rem 0; border-top: 1px solid var(--cl-border, #eee);
    }
    .cl-candidate:first-of-type { margin-top: 0.6rem; }
    .cl-measure-text { font-size: 0.93rem; line-height: 1.55; margin: 0.55rem 0 0.4rem; }
    .cl-response {
        display: inline-block; font-size: 0.8rem; font-weight: 600; padding: 3px 12px;
        border-radius: 8px; border: 1px solid var(--cl-border, #ddd); margin: 4px 6px 0 0;
    }

    /* ── Footer ── */
    .cl-footer { text-align: center; font-size: 0.8rem; color: var(--cl-muted, #888);
                 padding: 0.6rem 0 1.2rem; }

    .map-legend {
        background: var(--cl-card, white);
        color: var(--cl-ink, #1a1a1a);
        border-radius: 12px;
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

    /* Primary buttons: filled accent. Secondary: outlined, so a page has one obvious action. */
    .stButton button, .stFormSubmitButton button {{
        background: var(--cl-accent); color: var(--cl-accent-ink); border: 0;
        border-radius: 10px; font-weight: 600; padding: 0.5rem 1.15rem;
        box-shadow: 0 6px 16px -10px var(--cl-accent);
        transition: filter 0.15s ease, transform 0.15s ease;
    }}
    .stButton button p, .stFormSubmitButton button p {{ color: var(--cl-accent-ink); font-weight: 600; }}
    .stButton button:hover, .stButton button:focus:not(:active) {{
        background: var(--cl-accent); color: var(--cl-accent-ink); filter: brightness(1.08);
        transform: translateY(-1px);
    }}
    .stButton [data-testid="stBaseButton-secondary"] {{
        background: var(--cl-card); border: 1.5px solid var(--cl-accent); box-shadow: none;
    }}
    .stButton [data-testid="stBaseButton-secondary"] p {{ color: var(--cl-accent); }}
    .stButton [data-testid="stBaseButton-secondary"]:hover,
    .stButton [data-testid="stBaseButton-secondary"]:focus:not(:active) {{
        background: var(--cl-tint); filter: none;
    }}

    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
    [data-baseweb="textarea"] {{
        background: var(--cl-card) !important; border-color: var(--cl-border) !important;
        border-radius: 10px !important;
    }}
    [data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {{
        border-color: var(--cl-accent) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--cl-accent) 22%, transparent);
    }}

    /* Sidebar navigation as pills: hide the radio circles, highlight the current section */
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]),
    [data-testid="stSidebar"] [data-testid="stRadio"],
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{ width: 100% !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{ gap: 3px; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {{
        width: 100%; margin: 0; padding: 0.5rem 0.75rem; border-radius: 10px;
        transition: background 0.15s ease;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {{ display: none; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover {{ background: var(--cl-tint); }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background: var(--cl-accent);
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: var(--cl-accent-ink) !important; font-weight: 600;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:focus-visible) {{
        outline: 2px solid var(--cl-accent); outline-offset: 2px;
    }}
    [data-testid="stSidebar"] {{ border-right: 1px solid var(--cl-border); }}

    /* Bordered containers holding a Home section card */
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-icon) {{
        background: var(--cl-card); border-radius: 16px !important;
        border-color: var(--cl-border) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 8px 22px -16px rgba(0,0,0,0.25);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-icon):hover {{
        transform: translateY(-2px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 14px 28px -16px rgba(0,0,0,0.3);
    }}

    [data-testid="stAlert"] > div {{ border-radius: 12px; }}
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

    [data-testid="stExpander"] details {{ background: var(--cl-card); border-color: var(--cl-border); border-radius: 12px; }}
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
