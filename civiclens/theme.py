"""Fonts, the Ballot Paper styles, and its light/dark color themes."""
import re

import streamlit as st

def apply_base_styles():
    """Fonts and the shared classes. Colors come from the --cl-* variables that
    apply_theme() sets, with Ballot Paper light fallbacks."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
    .stApp h1, .stApp h2, .stApp h3 { font-family: 'Source Serif 4', Georgia, serif !important;
        font-weight: 600; letter-spacing: -0.01em; }

    /* ── Layout ── */
    .block-container, [data-testid="stMainBlockContainer"] { max-width: 1120px; padding-top: 2.2rem; }
    [data-testid="stHeaderActionElements"] { display: none; }   /* heading anchor-link icons */

    /* Small monospace label used for offices, eyebrows, and section labels */
    .cl-kicker, .cl-eyebrow, .section-label, .cl-brand-tag, .cl-date-month, .cl-tag,
    .cl-pill, .cl-shared, .cl-feature-num, .subject-tag, .cl-footer {
        font-family: 'IBM Plex Mono', ui-monospace, monospace; letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* ── Page header: eyebrow, serif title, double rule ── */
    .cl-hero {
        display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end;
        gap: 1.5rem; padding: 0 0 1.4rem; margin: 0 0 1.6rem;
        border-bottom: 3px double var(--cl-ink, #1A1A1A);
    }
    .cl-hero-text { flex: 1 1 420px; min-width: 0; display: flex; flex-direction: column; gap: 0.35rem; }
    .cl-eyebrow { font-size: 0.75rem; color: var(--cl-accent, #B8321A); }
    .stApp .cl-hero h1 {
        margin: 0; padding: 0; font-size: 3.1rem; line-height: 1.05; letter-spacing: -0.02em;
        color: var(--cl-ink, #1A1A1A);
    }
    .stApp .cl-hero .cl-hero-sub { margin: 0; color: var(--cl-muted, #555); font-size: 1rem; line-height: 1.5; max-width: 640px; }
    .cl-countdown { display: flex; align-items: baseline; gap: 0.75rem; }
    .cl-countdown-num {
        font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 5rem;
        line-height: 0.9; color: var(--cl-accent, #B8321A);
    }
    .cl-countdown-label { font-size: 0.88rem; line-height: 1.35; color: var(--cl-ink, #1A1A1A); }
    .cl-countdown-label span { color: var(--cl-muted, #555); }
    @media (max-width: 640px) {
        .stApp .cl-hero h1 { font-size: 2.2rem; }
        .cl-countdown-num { font-size: 3.4rem; }
    }

    /* ── Home ── */
    .stApp .cl-home-hero h1 { font-size: 3.8rem; max-width: 760px; }
    @media (max-width: 640px) { .stApp .cl-home-hero h1 { font-size: 2.4rem; } }
    .cl-feature-num { font-size: 0.75rem; color: var(--cl-accent, #B8321A); }
    .cl-feature-title { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 1.4rem;
                        line-height: 1.2; color: var(--cl-ink, #1A1A1A); margin: 0.3rem 0 0.2rem; }
    .cl-feature-desc  { font-size: 0.93rem; color: var(--cl-muted, #555); line-height: 1.45;
                        margin: 0 0 0.6rem; min-height: 4.2em; }
    @media (max-width: 640px) { .cl-feature-desc { min-height: 0; } }
    /* Section cards fill their column and share one height; the Open button sits at the bottom */
    [data-testid="stColumn"]:has(.cl-feature-num) > [data-testid="stVerticalBlock"] { height: 100%; }
    [data-testid="stColumn"]:has(.cl-feature-num) > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] { flex: 1; }
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-num) {
        height: 100%; min-height: 16.5rem; }
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-num)
        > [data-testid="stElementContainer"]:last-child { margin-top: auto; }
    /* Four across gets too narrow beside the sidebar ("Representatives" breaks mid-word): two per row */
    @media (min-width: 641px) and (max-width: 1300px) {
        [data-testid="stHorizontalBlock"]:has(.cl-feature-num) { flex-wrap: wrap; }
        [data-testid="stHorizontalBlock"]:has(.cl-feature-num) > [data-testid="stColumn"] {
            flex: 1 1 calc(50% - 1rem) !important; min-width: calc(50% - 1rem) !important; } }
    @media (max-width: 640px) {
        [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-num) { min-height: 11.75rem; } }
    .cl-trust { display: grid; grid-template-columns: repeat(4, 1fr);
                gap: 1.5rem; margin: 0.4rem 0 1rem; }
    @media (max-width: 1100px) { .cl-trust { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px) { .cl-trust { grid-template-columns: 1fr; } }
    .cl-trust-item { border-top: 3px solid var(--cl-ink, #1A1A1A); padding-top: 0.75rem; }
    .cl-trust-item b { display: block; font-family: 'Source Serif 4', Georgia, serif; font-weight: 600;
                       font-size: 1.2rem; color: var(--cl-ink, #1A1A1A); margin-bottom: 4px; }
    .cl-trust-item span { display: block; font-size: 0.93rem; color: var(--cl-muted, #555); line-height: 1.5; }

    /* ── Sidebar brand ── */
    .cl-brand { padding: 0.4rem 0 1.2rem; }
    .cl-brand-name { font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 1.9rem;
                     line-height: 1.1; letter-spacing: -0.02em; color: var(--cl-ink, #1A1A1A); }
    .cl-brand-tag  { font-size: 0.68rem; color: var(--cl-muted, #555); margin-top: 4px; }

    /* ── Section label: monospace caps. The rows and link lists below it bring the rule. ── */
    .section-label { font-size: 0.75rem; font-weight: 500; color: var(--cl-ink, #1A1A1A); margin: 2.2rem 0 0.1rem 0; }

    /* ── Rows: every card is a ruled row, like a line on a ballot ── */
    .rep-card {
        color: var(--cl-ink, #1A1A1A); padding: 1.1rem 0; margin: 0;
        border-top: 1px solid var(--cl-ink, #1A1A1A);
    }
    .cl-row { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 1.25rem; align-items: center; }
    .cl-row-mark { display: flex; justify-content: center; }
    .cl-row-mark img { width: 64px; height: 64px; object-fit: cover; border: 1px solid var(--cl-ink, #1A1A1A); }
    .cl-oval { width: 30px; height: 18px; border: 2px solid var(--cl-ink, #1A1A1A); border-radius: 50%;
               background: var(--cl-ink, #1A1A1A); }
    .cl-kicker { font-size: 0.75rem; color: var(--cl-muted, #555); }
    .cl-name { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 1.65rem;
               line-height: 1.15; color: var(--cl-ink, #1A1A1A); }
    .cl-row-actions { display: flex; flex-wrap: wrap; gap: 0.4rem 1.25rem; font-size: 0.9rem; justify-content: flex-end; }
    @media (max-width: 640px) {
        .cl-row { grid-template-columns: 44px minmax(0, 1fr); gap: 0.9rem; }
        .cl-row-mark img { width: 44px; height: 44px; }
        .cl-row-actions { grid-column: 2; justify-content: flex-start; }
        .cl-name { font-size: 1.35rem; }
    }

    /* Party: a small square swatch and the party name in words */
    .party-badge { display: inline-flex; align-items: center; gap: 0.45rem; font-size: 0.9rem;
                   color: var(--cl-ink, #1A1A1A); margin-left: 0.6rem; }
    .cl-row .party-badge { margin-left: 0; }
    .party-badge::before { content: ""; width: 10px; height: 10px; flex: none; background: var(--cl-other, #6B6B6B); }
    .badge-democrat::before   { background: var(--cl-dem, #1F3F7A); }
    .badge-republican::before { background: var(--cl-rep, #C0392B); }

    .cl-shared, .cl-pill {
        display: inline-block; font-size: 0.68rem; padding: 2px 8px; margin-left: 0.5rem;
        border: 1.5px solid var(--cl-ink, #1A1A1A); color: var(--cl-ink, #1A1A1A); white-space: nowrap;
    }
    .cl-searched { font-size: 0.85rem; color: var(--cl-muted, #555); margin: 0 0 0.6rem; }
    .cl-searched b { color: var(--cl-ink, #1A1A1A); font-weight: 600; }

    /* ── Official link lists ── */
    .cl-links { border-top: 1px solid var(--cl-ink, #1A1A1A); margin: 0.4rem 0 0.8rem; }
    .cl-links a {
        display: flex; justify-content: space-between; align-items: center; gap: 1rem;
        min-height: 52px; padding: 0 4px; border-bottom: 1px solid var(--cl-ink, #1A1A1A);
        text-decoration: none; font-size: 1.02rem; color: var(--cl-ink, #1A1A1A) !important;
    }
    .cl-links a:hover { color: var(--cl-accent, #B8321A) !important; }
    .cl-links a span { font-family: 'IBM Plex Mono', ui-monospace, monospace; font-size: 0.7rem;
                       letter-spacing: 0.1em; text-transform: uppercase; color: var(--cl-muted, #555); }

    .info-box { border: 1.5px solid var(--cl-ink, #1A1A1A); background: var(--cl-card, #fff);
                color: var(--cl-ink, #1A1A1A); padding: 1rem 1.25rem; margin-top: 0.5rem; }

    /* ── Deadlines: a dashed "ballot stub" date tile per row ── */
    .cl-deadline { display: grid; grid-template-columns: 84px minmax(0, 1fr) auto; gap: 1.5rem; align-items: start; }
    .cl-date-tile { text-align: center; padding: 6px 0 8px; border: 1.5px dashed var(--cl-ink, #1A1A1A);
                    background: var(--cl-card, #fff); }
    .cl-date-tile.final { border-style: solid; background: var(--cl-ink, #1A1A1A); }
    .cl-date-tile.final div { color: var(--cl-paper, #F3F0E8); }
    .cl-date-month { font-size: 0.75rem; color: var(--cl-ink, #1A1A1A); }
    .cl-date-day { font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 2.1rem;
                   line-height: 1; color: var(--cl-ink, #1A1A1A); }
    .cl-deadline-body { min-width: 0; }
    .cl-deadline-name { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; }
    .cl-deadline-when { font-size: 0.9rem; }
    .cl-deadline-note { font-size: 0.95rem; color: var(--cl-muted, #555); }
    .cl-deadline-note strong { color: var(--cl-ink, #1A1A1A); }
    .cl-tag { font-size: 0.72rem; padding: 3px 9px; white-space: nowrap; }
    .cl-tag.solid   { color: #FFFFFF; background: var(--cl-accent, #B8321A); border: 1.5px solid var(--cl-accent, #B8321A); }
    .cl-tag.outline { color: var(--cl-accent, #B8321A); border: 1.5px solid var(--cl-accent, #B8321A); }
    .cl-tag.plain   { color: var(--cl-ink, #1A1A1A); padding-left: 0; padding-right: 0; }
    @media (max-width: 640px) {
        .cl-deadline { grid-template-columns: 64px minmax(0, 1fr); gap: 1rem; }
        .cl-deadline .cl-tag { grid-column: 2; justify-self: start; }
    }

    /* ── Ballot ── */
    .cl-race-head { display: flex; justify-content: space-between; align-items: baseline;
                    gap: 0.75rem; flex-wrap: wrap; }
    .cl-race-office { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 1.35rem; }
    .cl-race-district { font-size: 0.88rem; color: var(--cl-muted, #555); }
    .cl-candidate {
        display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
        padding: 0.6rem 0 0.6rem 2.6rem; border-top: 1px solid var(--cl-border, #ccc); position: relative;
    }
    .cl-candidate::before { content: ""; position: absolute; left: 0; width: 26px; height: 15px;
                            border: 2px solid var(--cl-ink, #1A1A1A); border-radius: 50%; }
    .cl-candidate:first-of-type { margin-top: 0.6rem; }
    .cl-measure-text { font-size: 0.95rem; line-height: 1.55; margin: 0.55rem 0 0.4rem; }
    .cl-response { display: inline-block; font-size: 0.85rem; font-weight: 600; padding: 3px 12px;
                   border: 1.5px solid var(--cl-ink, #1A1A1A); margin: 4px 6px 0 0; }

    /* ── Bills ── */
    .cl-bill-id { font-family: 'IBM Plex Mono', ui-monospace, monospace; font-size: 0.9rem;
                  letter-spacing: 0.06em; color: var(--cl-accent, #B8321A); margin-right: 0.6rem; }
    .cl-bill-title { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 1.45rem; line-height: 1.2; }
    .cl-bill-meta { font-size: 0.88rem; color: var(--cl-muted, #555); margin-top: 0.3rem; }
    .subject-tag { display: inline-block; padding: 1px 8px; font-size: 0.68rem; margin: 6px 6px 0 0;
                   border: 1px solid var(--cl-muted, #555); color: var(--cl-muted, #555); }

    /* AI candidate cards: the prompt's inline card styles become ruled rows */
    .cl-ai > div[style] {
        border: 0 !important; border-top: 1px solid var(--cl-ink, #1A1A1A) !important;
        border-radius: 0 !important; background: transparent !important;
        padding: 1.1rem 0 !important; margin: 0 !important;
    }
    .cl-ai h4 { font-family: 'Source Serif 4', Georgia, serif !important; font-size: 1.5rem !important; font-weight: 600; }

    /* ── Map legend ── */
    .map-legend {
        color: var(--cl-ink, #1A1A1A); padding: 0.75rem 0; margin-bottom: 1rem;
        border-top: 1px solid var(--cl-ink, #1A1A1A); border-bottom: 1px solid var(--cl-ink, #1A1A1A);
        display: flex; flex-wrap: wrap; gap: 0.5rem 1.5rem; align-items: center;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.88rem; }
    .legend-dot  { width: 12px; height: 12px; display: inline-block; }

    /* ── Footer ── */
    .cl-footer { text-align: center; font-size: 0.68rem; color: var(--cl-muted, #555); padding: 0.8rem 0 1.4rem; }
</style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# COLOR THEMES
# ─────────────────────────────────────────────
# paper, card, ink, accent, accent_ink, mark
PALETTES = {
    "paper": ("Ballot Paper",       "#F3F0E8", "#FFFFFF", "#1A1A1A", "#B8321A", "#FFFFFF", "#B8321A"),
    "night": ("Ballot Paper Night", "#16140F", "#221F18", "#EDE8DC", "#E36B4F", "#16140F", "#E36B4F"),
}
# Party swatch colors per theme: the light ones are too dark to read on the night paper
PARTY_SWATCHES = {
    "paper": ("#1F3F7A", "#C0392B", "#6B6B6B"),
    "night": ("#8FB0FF", "#FF8A75", "#A8A196"),
}

def apply_theme(key: str):
    """Sets the --cl-* CSS variables used by the app's own markup, and restyles Streamlit's
    widgets to match. Spans aren't recolored globally so self-colored labels keep their colors."""
    _, paper, card, ink, accent, accent_ink, mark = PALETTES[key]
    dem, rep, other = PARTY_SWATCHES[key]
    st.markdown(f"""
    <style>
    :root {{
        --cl-paper: {paper}; --cl-card: {card}; --cl-ink: {ink};
        --cl-accent: {accent}; --cl-accent-ink: {accent_ink}; --cl-mark: {mark};
        --cl-muted:  color-mix(in srgb, {ink} 72%, {card});
        --cl-border: color-mix(in srgb, {ink} 30%, {card});
        --cl-tint:   color-mix(in srgb, {ink} 6%, {paper});
        --cl-dem: {dem}; --cl-rep: {rep}; --cl-other: {other};
    }}
    .stApp, [data-testid="stHeader"] {{ background: var(--cl-paper); }}
    .stApp, .stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{ color: var(--cl-ink); }}
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * {{
        color: var(--cl-muted) !important; opacity: 1;
    }}
    .stApp a {{ color: var(--cl-ink); text-underline-offset: 3px; }}
    .stApp a:hover {{ color: var(--cl-accent); }}
    .stApp hr {{ border-color: var(--cl-ink); }}
    .stApp td, .stApp th {{ border-color: var(--cl-border) !important; }}
    mark {{ background: var(--cl-mark); color: var(--cl-accent-ink); }}
    [data-baseweb="tab-highlight"] {{ background-color: var(--cl-mark) !important; }}
    [data-testid="stSidebar"] {{ background: var(--cl-paper); border-right: 1px solid var(--cl-ink); }}
    *:focus-visible {{ outline: 3px solid var(--cl-accent) !important; outline-offset: 2px; }}
    /* Text boxes and dropdowns show focus on their whole border instead (below). Without this
       the outline lands on the small inner field and draws a box around the text cursor. */
    [data-baseweb="input"] input:focus-visible, [data-baseweb="textarea"] textarea:focus-visible,
    [data-baseweb="select"] input:focus-visible {{ outline: none !important; }}

    /* Buttons: square. Primary is filled ink, secondary is outlined. */
    .stButton button, .stFormSubmitButton button {{
        background: var(--cl-ink); color: var(--cl-paper); border: 1.5px solid var(--cl-ink);
        border-radius: 0; font-weight: 600; padding: 0.55rem 1.4rem; min-height: 46px; box-shadow: none;
    }}
    .stButton button p, .stFormSubmitButton button p {{ color: var(--cl-paper); font-weight: 600; }}
    .stButton button:hover, .stButton button:focus:not(:active) {{
        background: var(--cl-accent); border-color: var(--cl-accent); color: var(--cl-accent-ink);
    }}
    .stButton button:hover p {{ color: var(--cl-accent-ink); }}
    .stButton [data-testid="stBaseButton-secondary"] {{ background: transparent; border: 1.5px solid var(--cl-ink); }}
    .stButton [data-testid="stBaseButton-secondary"] p {{ color: var(--cl-ink); }}
    .stButton [data-testid="stBaseButton-secondary"]:hover,
    .stButton [data-testid="stBaseButton-secondary"]:focus:not(:active) {{
        background: var(--cl-ink); border-color: var(--cl-ink);
    }}
    .stButton [data-testid="stBaseButton-secondary"]:hover p {{ color: var(--cl-paper); }}

    /* Inputs: square, ink outline */
    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
    [data-baseweb="textarea"] {{
        background: var(--cl-card) !important; border-color: var(--cl-ink) !important;
        border-radius: 0 !important;
    }}
    [data-baseweb="input"], [data-baseweb="select"] > div {{ border-width: 1.5px !important; }}
    [data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {{
        border-color: var(--cl-accent) !important; box-shadow: none;
    }}
    .stApp [data-testid="stWidgetLabel"] p {{
        font-family: 'IBM Plex Mono', ui-monospace, monospace; font-size: 0.75rem;
        letter-spacing: 0.1em; text-transform: uppercase;
    }}
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] div {{ color: var(--cl-ink) !important; caret-color: var(--cl-ink); }}
    /* Dropdowns aren't typed into (type-to-filter still works), so no blinking cursor */
    [data-baseweb="select"] input {{ caret-color: transparent !important; }}
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

    /* Sidebar navigation: a ballot oval per section, filled for the current one */
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]),
    [data-testid="stSidebar"] [data-testid="stRadio"],
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{ width: 100% !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{ gap: 0; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {{
        width: 100%; margin: 0; padding: 0.45rem 0; min-height: 40px; align-items: center;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {{ display: none; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]::before {{
        content: ""; width: 18px; height: 11px; flex: none; margin-right: 12px;
        border: 1.5px solid var(--cl-ink); border-radius: 50%;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover p {{ color: var(--cl-accent) !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked)::before {{
        background: var(--cl-ink);
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        font-weight: 600;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:focus-visible) {{
        outline: 3px solid var(--cl-accent); outline-offset: 2px;
    }}

    /* Home section cards: a ruled grid cell, no rounded box or shadow */
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-num) {{
        background: transparent; border-radius: 0 !important; border-color: var(--cl-ink) !important;
    }}
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .cl-feature-num):hover {{
        background: var(--cl-card);
    }}

    /* Alerts: a plain ruled box in the theme's colors */
    [data-testid="stAlert"] > div {{
        border-radius: 0; background: var(--cl-card) !important; border: 1.5px solid var(--cl-ink);
    }}
    [data-testid="stAlert"] p {{ color: var(--cl-ink) !important; }}

    [data-baseweb="radio"] > div:first-child {{ background: var(--cl-border) !important; }}
    [data-baseweb="radio"] > div:first-child > div {{ background: var(--cl-card) !important; }}
    [data-baseweb="radio"]:has(input:checked) > div:first-child {{ background: var(--cl-ink) !important; }}
    [data-baseweb="radio"]:has(input:checked) > div:first-child > div {{ background: var(--cl-paper) !important; }}
    [data-baseweb="checkbox"] > span {{ border-color: var(--cl-ink) !important; background-color: var(--cl-card) !important; border-radius: 0 !important; }}
    [data-baseweb="checkbox"]:has(input:checked) > span {{
        border-color: var(--cl-ink) !important; background-color: var(--cl-ink) !important;
    }}

    [data-testid="stExpander"] details {{ background: transparent; border: 0; border-top: 1px solid var(--cl-ink); border-radius: 0; }}
    [data-testid="stExpander"] summary svg {{ fill: var(--cl-ink); color: var(--cl-ink); }}
    [data-testid="stStatusWidget"], [data-testid="stExpander"] summary p {{ color: var(--cl-ink); }}
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
