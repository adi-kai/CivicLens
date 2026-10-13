"""Gemini bill summaries and candidate research, with a Groq + Tavily fallback."""
import re
import time

import requests
import streamlit as st

from civiclens.config import GEMINI_KEY, GROQ_KEY, TAVILY_KEY

# Every function here takes `lang` explicitly instead of reading the session: they're
# cached, so the language has to be part of the cache key. The prompts stay in English
# (the models follow them most reliably that way) and ask for Spanish output.
SPANISH_OUTPUT = """

IMPORTANT: Write all of your text in Spanish — including the "no 2026 election" message, the "Running against" phrase ("Compite contra"), the "Key Positions" heading ("Posturas principales"), and the "Campaign Website" link text ("Sitio web de campaña"). Translate party names (Democrat → Demócrata, Republican → Republicano). Keep people's names, URLs, and the HTML structure and inline styles exactly as specified. For state legislative offices, ROLE must still make clear the office is state-level (e.g. "Senador estatal", "Representante estatal")."""

def _msg(lang: str, en: str, es: str) -> str:
    return es if lang == "es" else en

class AIError(Exception):
    """Raised inside a cached AI call so a failure isn't cached; the uncached wrapper
    turns it into a message (or the next fallback) and the next click retries."""

def _gemini_text(prompt: str, generation_config: dict, tools: list | None = None, timeout: int = 20) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": generation_config}
    if tools:
        body["tools"] = tools
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": GEMINI_KEY}, json=body, timeout=timeout,
        )
    except Exception as e:
        # Only the type: a requests error message includes the URL, and the key is in it
        raise AIError(f"Gemini: {type(e).__name__}")
    if r.status_code != 200:
        raise AIError(f"Gemini {r.status_code}")
    parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
    if not text:
        raise AIError("Gemini returned empty")
    return text

def _groq_text(system: str, prompt: str, max_tokens: int, timeout: int = 30) -> str:
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        text = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise AIError(f"Groq: {type(e).__name__}")
    text = (text or "").strip()
    if not text:
        raise AIError("Groq returned empty")
    return text

def _bill_summary_prompt(title: str, latest_action: str, state_name: str, lang: str, abstract: str) -> str:
    language = "plain Spanish" if lang == "es" else "plain English"
    # With only a title to go on, the model used to invent provisions, so it's told to stay within it
    if abstract:
        source = f"""Summarize this {state_name or "state"} bill in 2-3 sentences of {language} that a first-time voter can understand.
Use ONLY the official summary below. Do not add any detail, amount, date, or effect it doesn't state.

Bill: {title}
Latest action: {latest_action}
Official summary: {abstract[:4000]}"""
    else:
        source = f"""Only this {state_name or "state"} bill's title is available, not its text or an official summary.
In 1-2 sentences of {language} that a first-time voter can understand, explain what the title says the bill is about.
Do not guess at specific provisions, amounts, dates, or effects the title doesn't state.
If the title is too general to tell (for example, chamber rules or a list of local changes), say so plainly.

Bill: {title}
Latest action: {latest_action}"""
    return f"""You are a nonpartisan civic education assistant for a voter app.

{source}

Be strictly factual and nonpartisan. Do not editorialize or take sides.
Respond with only the summary — no intro, no labels, no markdown."""

@st.cache_data(ttl=3600, show_spinner=False)
def _gemini_bill_summary(prompt: str) -> str:
    # Thinking tokens count against maxOutputTokens and were cutting summaries off
    return _gemini_text(prompt, {"temperature": 0.1, "maxOutputTokens": 500,
                                 "thinkingConfig": {"thinkingBudget": 0}})

@st.cache_data(ttl=3600, show_spinner=False)
def _groq_bill_summary(prompt: str) -> str:
    # GPT-OSS reasons before answering, and those tokens count against max_tokens too
    return _groq_text("You are a nonpartisan civic education assistant. Reply with only the summary.",
                      prompt, max_tokens=1500)

def get_bill_summary(bill_id: str, title: str, latest_action: str, state_name: str = "",
                     lang: str = "en", abstract: str = "") -> str:
    """Gemini first, then Groq (the free Gemini tier allows only a few requests a day).
    Uncached wrapper: failures come back as a message and aren't cached."""
    prompt = _bill_summary_prompt(title, latest_action, state_name, lang, abstract)
    errors = []
    for key, summarize in ((GEMINI_KEY, _gemini_bill_summary), (GROQ_KEY, _groq_bill_summary)):
        if not key:
            continue
        try:
            return summarize(prompt)
        except AIError as e:
            errors.append(str(e))
    if not errors:
        return _msg(lang, "⚠️ No AI API key is set (Gemini or Groq).",
                    "⚠️ No se configuró ninguna clave de API de IA (Gemini o Groq).")
    return _msg(lang, "⚠️ Summary unavailable right now ({err}). Please try again in a minute.",
                "⚠️ El resumen no está disponible ahora ({err}). Inténtalo de nuevo en un minuto.").format(
        err="; ".join(errors))

# ── Candidates — Gemini 2.5 Flash with Google Search grounding ───────────────
def get_candidate_info(race: str, state_name: str, lang: str = "en") -> str | None:
    """Returns Gemini's candidate HTML, or None so the tab switches to the Groq + Tavily
    fallback. Uncached wrapper, so a failure is retried on the next click."""
    if not GEMINI_KEY:
        return candidate_info_fallback(race, state_name, lang)
    try:
        return _gemini_candidate_info(race, state_name, lang)
    except AIError:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def _gemini_candidate_info(race: str, state_name: str, lang: str) -> str:
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
    if lang == "es":
        prompt += SPANISH_OUTPUT

    for attempt in range(2):
        try:
            html = _gemini_text(prompt, {"temperature": 0.1}, tools=[{"google_search": {}}], timeout=45)
            return re.sub(r"```html?\n?|```\n?", "", html).strip()
        except AIError as e:
            if attempt == 0 and str(e) == "Gemini 503":
                time.sleep(4)
                continue
            raise

def candidate_info_fallback(race: str, state_name: str, lang: str = "en") -> str:
    """Groq (GPT-OSS 120B) + Tavily search — runs when Gemini is down. Uncached wrapper:
    failures come back as a message and aren't cached."""
    if not GROQ_KEY or not TAVILY_KEY:
        return '<p style="color:#c0392b;">' + _msg(
            lang,
            "⚠️ Gemini is currently overloaded and no fallback keys are configured. Please try again in a minute.",
            "⚠️ Gemini está saturado en este momento y no hay claves de respaldo configuradas. Inténtalo de nuevo en un minuto.",
        ) + "</p>"
    try:
        return _candidate_info_fallback_cached(race, state_name, lang)
    except AIError as e:
        return '<p style="color:#c0392b;">' + str(e) + "</p>"

@st.cache_data(ttl=3600, show_spinner=False)
def _candidate_info_fallback_cached(race: str, state_name: str, lang: str) -> str:
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
        raise AIError(_msg(lang, f"⚠️ Search unavailable: {e}. Please try again.",
                           f"⚠️ La búsqueda no está disponible: {e}. Inténtalo de nuevo."))

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
    if lang == "es":
        prompt += SPANISH_OUTPUT
    try:
        html = _groq_text(
            "You are a nonpartisan civic information assistant. You output ONLY raw HTML — no greetings, "
            "no markdown, no explanations, no code fences. Your entire response must be HTML starting with a <div> tag.",
            prompt, max_tokens=4000)
    except AIError as e:
        raise AIError(_msg(lang, f"⚠️ Backup also failed: {e}. Please try again in a minute.",
                           f"⚠️ El respaldo también falló: {e}. Inténtalo de nuevo en un minuto."))
    html = re.sub(r"```html?\n?|```\n?", "", html).strip()
    label = ('<p style="font-family:sans-serif; font-size:0.85rem; color:#8a6d00; background:#fff8e1; '
             'border-radius:6px; padding:6px 10px; margin-bottom:0.75rem;">'
             + _msg(lang, "⚠️ AI-generated from web search. May be incomplete.",
                    "⚠️ Generado por IA a partir de una búsqueda web. Puede estar incompleto.")
             + '</p>')
    return label + html
