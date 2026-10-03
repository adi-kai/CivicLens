"""Gemini bill summaries and candidate research, with a Groq + Tavily fallback."""
import re
import time

import requests
import streamlit as st

from civiclens.config import GEMINI_KEY, GROQ_KEY, TAVILY_KEY

@st.cache_data(ttl=3600, show_spinner=False)
def get_bill_summary(bill_id: str, title: str, latest_action: str, state_name: str = "") -> str:
    if not GEMINI_KEY:
        return "⚠️ Gemini API key not set."
    prompt = f"""You are a nonpartisan civic education assistant for a voter app.

Summarize this {state_name or "state"} bill in 2-3 plain English sentences that a first-time voter can understand.
Be strictly factual and nonpartisan. Do not editorialize or take sides.

Bill: {title}
Latest action: {latest_action}

Respond with only the summary — no intro, no labels, no markdown."""
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": GEMINI_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 500},
            },
            timeout=20,
        )
        if r.status_code != 200:
            return f"⚠️ Gemini error {r.status_code}"
        parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# ── Candidates — Gemini 2.5 Flash with Google Search grounding ───────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_candidate_info(race: str, state_name: str) -> str:
    if not GEMINI_KEY:
        return candidate_info_fallback(race, state_name)

    prompt = f"""You are a nonpartisan civic information assistant for CivicLens, a voter education app.

Search and find all major candidates running in the 2026 {state_name} {race} election.

If there is no 2026 election for this office in {state_name} (for example, the seat is not up until a later year), do not invent candidates. Return only:
<p style="font-family:sans-serif;">No 2026 {race} election was found for {state_name} — this seat may not be on the ballot this year. Check your state's election office to confirm.</p>

For each candidate provide:
1. Full name and party affiliation
2. Their main opponent(s) and those opponents' parties
3. Top 4-5 policy positions from their official campaign website
4. Official campaign website URL if available

Return your ENTIRE response as pure HTML — no markdown, no code fences, just raw HTML.
Use this card structure for each candidate:

<div style="border-left:5px solid BORDER_COLOR; background:#f8f9fa; border-radius:8px; padding:1rem 1.25rem; margin-bottom:1rem;">
  <h4 style="margin:0 0 2px 0; font-family:sans-serif;">NAME <span style="font-size:0.78rem; padding:2px 10px; border-radius:20px; background:BADGE_BG; color:BADGE_FG; font-weight:600; margin-left:6px;">PARTY</span></h4>
  <p style="color:#555; font-size:0.88rem; margin:0 0 8px 0; font-family:sans-serif;">ROLE — Running against: OPPONENT(S)</p>
  <strong style="font-family:sans-serif;">Key Positions:</strong>
  <ul style="margin:6px 0 10px 20px; font-family:sans-serif; color:#333;">
    <li>POSITION 1</li>
    <li>POSITION 2</li>
    <li>POSITION 3</li>
  </ul>
  <a href="WEBSITE" target="_blank" style="font-size:0.85rem; font-family:sans-serif; color:#1a73e8;">🌐 Campaign Website</a>
</div>

Color guide:
- Democrat:   BORDER_COLOR=#1a73e8  BADGE_BG=#d6e4ff  BADGE_FG=#1a3c8f
- Republican: BORDER_COLOR=#c0392b  BADGE_BG=#ffe0dd  BADGE_FG=#8b1a1a
- Other:      BORDER_COLOR=#7f8c8d  BADGE_BG=#e8e8e8  BADGE_FG=#444444

For state legislative offices, ROLE must start with the word "State" (e.g. "State Senator", "State Representative", "State Assembly Member", "State Delegate") so they aren't confused with members of Congress.

Be strictly factual and nonpartisan. List ALL major-party candidates."""

    try:
        for attempt in range(2):
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": GEMINI_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"google_search": {}}],
                    "generationConfig": {"temperature": 0.1}
                },
                timeout=45
            )
            if r.status_code == 503:
                if attempt == 0:
                    time.sleep(4)
                    continue
                raise Exception("Gemini 503")
            if r.status_code != 200:
                raise Exception(f"Gemini {r.status_code}: {r.text[:200]}")

            data  = r.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            html  = "".join(p.get("text", "") for p in parts if "text" in p)
            html  = re.sub(r"```html?\n?|```\n?", "", html).strip()
            if html:
                return html
            raise Exception("Gemini returned empty")

    except Exception:
        return None  # the tab switches to the Groq + Tavily fallback

def candidate_info_fallback(race: str, state_name: str) -> str:
    """Groq (GPT-OSS 120B) + Tavily search — runs when Gemini is down."""
    if not GROQ_KEY or not TAVILY_KEY:
        return '<p style="color:#c0392b;">⚠️ Gemini is currently overloaded and no fallback keys are configured. Please try again in a minute.</p>'

    # Step 1 — Tavily search for live candidate data
    try:
        # First search: who's running
        search_r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": f"2026 {state_name} {race} election candidates",
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=20
        )
        search_data    = search_r.json()
        search_context = search_data.get("answer", "")
        for result in search_data.get("results", []):
            search_context += f"\n\nSource: {result.get('title')}\n{result.get('content', '')}"

        # Second search: policy positions and campaign websites
        policy_r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": f"2026 {state_name} {race} candidates policy positions issues campaign website",
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=20
        )
        policy_data = policy_r.json()
        search_context += "\n\n" + policy_data.get("answer", "")
        for result in policy_data.get("results", []):
            search_context += f"\n\nSource: {result.get('title')}\n{result.get('content', '')}"

    except Exception as e:
        return f'<p style="color:#c0392b;">⚠️ Search unavailable: {e}. Please try again.</p>'

    # Step 2 — Groq summarizes the search results
    prompt = f"""Based on the search results below, find all major candidates running in the 2026 {state_name} {race} election.

If the search results show no 2026 election for this office in {state_name}, do not invent candidates and ignore the card instructions below. Return only:
<p style="font-family:sans-serif;">No 2026 {race} election was found for {state_name} — this seat may not be on the ballot this year. Check your state's election office to confirm.</p>

SEARCH RESULTS:
{search_context[:8000]}

Use ONLY facts stated in the search results above. Do not use outside knowledge, and do not infer anything from a candidate's party, party platform, or the type of race. If something is not in the search results, leave it out.

For each candidate provide:
1. Full name and party affiliation
2. Their main opponent(s) and those opponents' parties
3. Policy positions stated in the search results, each with a brief explanation drawn from the results. List only what the results actually say — one or two positions is fine. If none are found, replace the Key Positions heading and list with: <p style="font-family:sans-serif; font-size:0.9rem; color:#555;">No policy positions found in search results.</p>
4. A short biography using only facts from the search results. If there are none, omit the bio paragraph entirely.
5. Official campaign website URL, only if it appears in the search results — otherwise omit the link entirely

Return your ENTIRE response as pure HTML using this card structure for each candidate:

<div style="border-left:5px solid BORDER_COLOR; background:#f8f9fa; border-radius:8px; padding:1rem 1.25rem; margin-bottom:1rem;">
  <h4 style="margin:0 0 2px 0; font-family:sans-serif;">NAME <span style="font-size:0.78rem; padding:2px 10px; border-radius:20px; background:BADGE_BG; color:BADGE_FG; font-weight:600; margin-left:6px;">PARTY</span></h4>
  <p style="color:#555; font-size:0.88rem; margin:0 0 8px 0; font-family:sans-serif;">ROLE — Running against: OPPONENT(S)</p>
  <p style="font-family:sans-serif; font-size:0.9rem; color:#333; margin:0 0 10px 0;">BIO HERE</p>
  <strong style="font-family:sans-serif;">Key Positions:</strong>
  <ul style="margin:6px 0 10px 20px; font-family:sans-serif; color:#333;">
    <li><strong>ISSUE:</strong> Explanation from the search results.</li>
    <!-- one <li> per position found; omit any you cannot support from the results -->
  </ul>
  <a href="WEBSITE" target="_blank" style="font-size:0.85rem; font-family:sans-serif; color:#1a73e8;">🌐 Campaign Website</a>
</div>

Color guide:
- Democrat:   BORDER_COLOR=#1a73e8  BADGE_BG=#d6e4ff  BADGE_FG=#1a3c8f
- Republican: BORDER_COLOR=#c0392b  BADGE_BG=#ffe0dd  BADGE_FG=#8b1a1a
- Other:      BORDER_COLOR=#7f8c8d  BADGE_BG=#e8e8e8  BADGE_FG=#444444

For state legislative offices, ROLE must start with the word "State" (e.g. "State Senator", "State Representative", "State Assembly Member", "State Delegate") so they aren't confused with members of Congress.

Be strictly factual and nonpartisan."""
    try:
        groq_r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a nonpartisan civic information assistant. You output ONLY raw HTML — no greetings, no markdown, no explanations, no code fences. Your entire response must be HTML starting with a <div> tag."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            timeout=30
        )
        html = groq_r.json()["choices"][0]["message"]["content"]
        html = re.sub(r"```html?\n?|```\n?", "", html).strip()

        if not html:
            raw = groq_r.json()["choices"][0]["message"]["content"]
            return f'<pre style="font-size:0.75rem">{raw[:500]}</pre>'

        label = ('<p style="font-family:sans-serif; font-size:0.85rem; color:#8a6d00; background:#fff8e1; '
                 'border-radius:6px; padding:6px 10px; margin-bottom:0.75rem;">'
                 '⚠️ AI-generated from web search. May be incomplete.</p>')
        return label + html
    except Exception as e:
        return f'<p style="color:#c0392b;">⚠️ Backup also failed: {e}. Please try again in a minute.</p>'
