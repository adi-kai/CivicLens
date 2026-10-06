"""Render check for every CivicLens section, with all network calls faked.

Run from the project root:
    python tests/smoke_test.py
    python tests/smoke_test.py --snapshot out.txt   # also dump every page's rendered output

Exits non-zero if any section raises or is missing its expected content. No API keys
or network access needed — requests.get/post are replaced with canned responses below.
"""
import os
import sys

import requests
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "civiclens_app.py")
# `streamlit run` puts the app's folder on sys.path so `import civiclens` works; AppTest doesn't
sys.path.insert(0, ROOT)


# ── Canned API responses ─────────────────────────────────────────────────────
def os_person(name, party, title, org, district, jur_class, jur_name, pid):
    return {"id": pid, "name": name, "party": party, "image": "", "email": "",
            "current_role": {"title": title, "org_classification": org, "district": district},
            "jurisdiction": {"classification": jur_class, "name": jur_name}}

GEO_REPS = [
    dict(os_person("Sen One", "Republican", "Senator", "upper", "North Carolina", "country", "United States", "f1"),
         image="https://example.com/sen-one.jpg"),
    os_person("Rep House", "Democratic", "Representative", "lower", "12", "country", "United States", "f2"),
    os_person("State Sen", "Democratic", "Senator", "upper", "37", "state", "North Carolina", "s1"),
    os_person("State Rep", "Republican", "Representative", "lower", "99", "state", "North Carolina", "s2"),
]

CONGRESS = [
    {"id": {"bioguide": "A000001"}, "name": {"first": "Ann", "last": "House", "official_full": "Ann House"},
     "terms": [{"type": "rep", "state": "NC", "district": 12, "party": "Democrat"}]},
    {"id": {"bioguide": "B000001"}, "name": {"first": "Bob", "last": "Senior", "official_full": "Bob Senior"},
     "terms": [{"type": "sen", "state": "NC", "party": "Republican", "state_rank": "senior",
                "url": "https://senior.senate.gov", "phone": "", "contact_form": ""}]},
    {"id": {"bioguide": "C000001"}, "name": {"first": "Cat", "last": "Junior", "official_full": "Cat Junior"},
     "terms": [{"type": "sen", "state": "NC", "party": "Republican", "state_rank": "junior",
                "url": "https://junior.senate.gov", "phone": "", "contact_form": ""}]},
]

def wd(value):
    return {"value": value}

WIKIDATA = {"results": {"bindings": [
    {"placeLabel": wd("North Carolina"), "govLabel": wd("Gov Person"), "partyLabel": wd("Democratic Party"),
     "start": wd("2025-01-01T00:00:00Z"), "img": wd(""), "possite": wd("https://governor.nc.gov/"),
     "article": wd("https://en.wikipedia.org/wiki/Gov_Person")},
]}}

def tiger(field, district):
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature", "properties": {field: district},
        "geometry": {"type": "Polygon", "coordinates": [[[-80, 35], [-79, 35], [-79, 36], [-80, 35]]]}}]}

US_STATES = {"type": "FeatureCollection", "features": [{
    "type": "Feature", "properties": {"name": "North Carolina"},
    "geometry": {"type": "Polygon", "coordinates": [[[-84, 34], [-75, 34], [-75, 37], [-84, 34]]]}}]}

BILLS = {"results": [{
    "id": "ocd-bill/1", "identifier": "HB 1", "title": "An Act About Schools",
    "latest_action_description": "Passed 1st reading", "latest_action_date": "2026-09-01",
    "openstates_url": "https://openstates.org/nc/bills/HB1", "subject": ["Education"],
    "sponsorships": [{"primary": True, "name": "Jay Sponsor",
                      "person": {"name": "Jay Sponsor", "party": "Democratic",
                                 "current_role": {"title": "Senator"}}}],
}]}

# Includes markup the sanitizer must strip, as if it came from a hostile search result
CANDIDATE_HTML = ('<div><h4 onclick="steal()">Candidate A</h4>\n\n    <p>Positions</p>'
                  '<script>steal()</script><a href="javascript:steal()">site</a></div>')


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = str(payload)

    def json(self):
        return self._payload


PROMPTS = []   # every AI prompt sent, so tests can check what was asked for


def fake_get(url, params=None, **kwargs):
    params = params or {}
    if "nominatim" in url:
        if ", SC" in params.get("q", ""):
            return FakeResponse([{"lat": "34.00", "lon": "-81.03",
                                  "address": {"ISO3166-2-lvl4": "US-SC", "state": "South Carolina"}}])
        return FakeResponse([{"lat": "35.22", "lon": "-80.84",
                              "address": {"ISO3166-2-lvl4": "US-NC", "state": "North Carolina"}}])
    if "civicinfo/v2/elections" in url:
        return FakeResponse({"elections": [{"id": "9000"}]})
    if "civicinfo/v2/voterinfo" in url:
        if ", SC" in params.get("address", ""):
            # A state whose ballot data isn't published yet
            return FakeResponse({"error": {"message": "Election unknown"}}, status=400)
        return FakeResponse({
            "election": {"id": "9000", "name": "2026 General Midterm Election", "electionDay": "2026-11-03"},
            "contests": [
                {"type": "General", "ballotPlacement": "1", "office": "Member, United States Senate",
                 "district": {"name": "North Carolina"}, "numberVotingFor": 1,
                 "candidates": [{"name": "Senate Hopeful", "party": "Democratic"},
                                {"name": "Other Hopeful", "party": "Republican"}]},
                {"type": "ballot-measure", "ballotPlacement": "9", "district": {"name": "North Carolina"},
                 "referendumTitle": "Constitutional Amendment 1",
                 "referendumText": "Should the <constitution> be amended?",
                 "referendumBallotResponses": ["Yes", "No"]},
            ],
            "pollingLocations": [{"address": {"locationName": "Fire Station 1", "line1": "1 Main St",
                                              "city": "Charlotte", "state": "NC", "zip": "28202"},
                                  "pollingHours": "6:30am-7:30pm"}],
            "state": [{"electionAdministrationBody": {"electionRegistrationUrl": "https://example.gov/reg"}}],
        })
    if "people.geo" in url:
        return FakeResponse({"results": GEO_REPS})
    if "v3.openstates.org/people" in url:
        org = params.get("org_classification")
        dist = "37" if org == "upper" else "99"
        title = "Senator" if org == "upper" else "Representative"
        return FakeResponse({"results": [
            os_person(f"Roster {org}", "Democratic", title, org, dist, "state", "North Carolina", f"r-{org}")]})
    if "v3.openstates.org/bills" in url:
        return FakeResponse(BILLS)
    if "congress-legislators" in url:
        return FakeResponse(CONGRESS)
    if "wikidata" in url:
        return FakeResponse(WIKIDATA)
    if "tigerweb" in url:
        layer = url.rstrip("/").split("/")[-2]
        return FakeResponse({"0": tiger("CD119", "12"), "1": tiger("SLDU", "037"),
                             "2": tiger("SLDL", "099")}[layer])
    if "us-states.json" in url:
        return FakeResponse(US_STATES)
    raise AssertionError(f"unexpected GET {url}")


def fake_post(url, params=None, json=None, **kwargs):
    if "generativelanguage" in url:
        PROMPTS.append(json["contents"][0]["parts"][0]["text"])
        is_summary = "Summarize" in json["contents"][0]["parts"][0]["text"]
        text = "This bill funds schools." if is_summary else CANDIDATE_HTML
        return FakeResponse({"candidates": [{"content": {"parts": [{"text": text}]}}]})
    if "tavily" in url:
        return FakeResponse({"answer": "Candidate A is running.", "results": []})
    if "groq" in url:
        return FakeResponse({"choices": [{"message": {"content": CANDIDATE_HTML}}]})
    raise AssertionError(f"unexpected POST {url}")


# ── Helpers ──────────────────────────────────────────────────────────────────
def new_app(lang="en"):
    at = AppTest.from_file(APP, default_timeout=60)
    if lang != "en":
        at.query_params["lang"] = lang
    at.secrets["google"] = {"api_key": "test"}
    at.secrets["openstates"] = {"api_key": "test"}
    at.secrets["gemini"] = {"api_key": "test"}
    at.secrets["groq"] = {"api_key": "test"}
    at.secrets["tavily"] = {"api_key": "test"}
    return at.run()


def walk(node):
    for child in getattr(node, "children", {}).values():
        yield child
        yield from walk(child)


def describe(el):
    for attr in ("value", "label", "body"):
        try:
            v = getattr(el, attr)
        except Exception:
            continue
        if v is not None and not callable(v):
            return f"{type(el).__name__}: {v}"
    return type(el).__name__


def rendered(at):
    return [describe(el) for el in walk(at._tree)]


def button(at, label):
    return next(b for b in at.button if b.label == label)


def go(at, section):
    # AppTest matches radio options by their displayed label, which is translated in Spanish
    from civiclens.i18n import ES
    radio = at.sidebar.radio[0]
    label = section if section in radio.options else ES[section]
    return radio.set_value(label).run()


# ── Sections ─────────────────────────────────────────────────────────────────
ADDR = "600 E 4th St, Charlotte, NC 28202"

def home(at):
    go(at, "🏠 Home")
    return ["CivicLens", "Your guide to voting in 2026", "Why you can trust it"]

def home_card(at):
    # A section card on Home switches sections without reloading
    go(at, "🏠 Home")
    at.button(key="home_📝 My Ballot").click().run()
    return ["Every race and ballot question"]

def ballot(at):
    go(at, "📝 My Ballot")
    at.text_input(key="address").input(ADDR).run()
    # API text is escaped, so "<constitution>" shows as written instead of becoming a tag
    return ["Member, United States Senate", "Senate Hopeful", "Vote for 1", "Constitutional Amendment 1",
            "&lt;constitution&gt;", "1 race and 1 ballot question on your ballot"], ["<constitution>"]

def ballot_not_published(at):
    go(at, "📝 My Ballot")
    at.text_input(key="address").input("1101 Main St, Columbia, SC 29201").run()
    return ["South Carolina hasn't published its ballot data yet", "SC Election Commission"]

def polling(at):
    go(at, "📍 Polling Finder")
    at.text_input[0].input(ADDR)
    button(at, "Search").click().run()
    return ["Fire Station 1", "North Carolina Voting Resources"]

def deadlines(at):
    go(at, "📅 Deadlines")
    at.text_input(key="address").input(ADDR).run()
    return ["Voter Registration Deadline", "Absentee Ballot Return Deadline"]

def my_reps(at):
    go(at, "🏛️ My Representatives")
    at.text_input[0].input(ADDR)
    button(at, "Find My Reps").click().run()
    return ["Gov Person", "Sen One", "Rep House", "State Senator — District 37", "State Rep",
            "alt='Photo of Sen One'"]

def shared_address(at):
    # Typed once in Polling Finder, still there in My Representatives — even after Home,
    # which has no address box and so makes Streamlit drop the widget's own state
    go(at, "📍 Polling Finder")
    at.text_input(key="address").input(ADDR).run()
    go(at, "🏠 Home")
    go(at, "🏛️ My Representatives")
    return [f"TextInput: {ADDR}"]

def rep_map(at):
    go(at, "🗺️ Rep Map")
    at.text_input[0].input(ADDR)
    for cb in at.checkbox:
        cb.check()
    button(at, "Show Map").click().run()
    return ["Map data loaded", "Party Key"]

def bills(at):
    go(at, "📋 Bill Tracker")
    button(at, "✨ Plain-English Summary").click().run()
    return ["HB 1", "State Senator Jay Sponsor (Democratic)", "This bill funds schools."]

def compare(at):
    go(at, "🔍 District Compare")
    at.text_input(key="address").input(ADDR)
    at.text_input(key="dc_addr2").input("1 Other St, Raleigh, NC 27601")
    button(at, "Compare Districts").click().run()
    return ["North Carolina State Senator — District 37", "share **4**"]

def candidates(at):
    go(at, "🗳️ Candidates")
    at.selectbox(key="cand_state").set_value("NC").run()
    next(s for s in at.selectbox if s.label == "Select Race").set_value("U.S. Senate").run()
    button(at, "Find Candidates & Positions").click().run()
    return ["Candidate A", "ncsbe.gov"], ["<script", "onclick", "javascript:"]

def deadlines_sc(at):
    # A researched state other than NC; its in-person registration deadline (Oct 2) has passed
    go(at, "📅 Deadlines")
    at.text_input(key="address").input("1101 Main St, Columbia, SC 29201").run()
    return ["Voter Registration Deadline — Online, Fax, or Email", "SC State Election Commission",
            ">Passed<", "SC Election Commission"]

def theme(at):
    next(s for s in at.sidebar.selectbox if s.label == "Color theme").set_value("midnight").run()
    return ["--cl-paper: #15112B"]


# ── Spanish ──────────────────────────────────────────────────────────────────
# Run with ?lang=es. Navigation values are the same internal keys in both languages;
# buttons are found by their Spanish labels.
def es_home(at):
    go(at, "🏠 Home")
    return ["Tu guía para votar en 2026", "Para empezar", "Por qué puedes confiar", "Mi boleta"], ["Get started"]

def es_ballot(at):
    go(at, "📝 My Ballot")
    at.text_input(key="address").input(ADDR).run()
    return ["Mi boleta", "Vota por 1", "Preguntas en la boleta", "Demócrata"], ["Vote for 1"]

def es_deadlines(at):
    go(at, "📅 Deadlines")
    at.text_input(key="address").input(ADDR).run()
    return ["Fecha límite de inscripción de votantes", "5 p. m. del viernes 9 de octubre de 2026",
            "Junta Electoral del Estado de Carolina del Norte", "Recursos oficiales"], ["Voter Registration Deadline"]

def es_my_reps(at):
    go(at, "🏛️ My Representatives")
    at.text_input[0].input(ADDR)
    button(at, "Buscar mis representantes").click().run()
    return ["Gobernador(a) de Carolina del Norte", "Senado estatal — Distrito 37", "Demócrata",
            "Foto de Sen One", "Cámara de Representantes de EE. UU. — Distrito 12"], ["Who Represents"]

def es_rep_map(at):
    go(at, "🗺️ Rep Map")
    at.text_input[0].input(ADDR)
    for cb in at.checkbox:
        cb.check()
    button(at, "Mostrar mapa").click().run()
    return ["¡Datos del mapa cargados!", "Partidos:"], ["Party Key"]

def es_bills(at):
    PROMPTS.clear()
    go(at, "📋 Bill Tracker")
    button(at, "✨ Resumen en lenguaje sencillo").click().run()
    asked_spanish = any("plain Spanish" in p for p in PROMPTS)
    return ["Proyectos de ley estatales", "Jay Sponsor (Demócrata) · Senado estatal",
            "This bill funds schools."] + ([] if asked_spanish else ["<summary prompt asked for Spanish>"])

def es_candidates(at):
    PROMPTS.clear()
    go(at, "🗳️ Candidates")
    at.selectbox(key="cand_state").set_value("NC").run()
    next(s for s in at.selectbox if s.label == "Selecciona la contienda").set_value("Senado de EE. UU.").run()
    button(at, "Buscar candidatos y posturas").click().run()
    asked_spanish = any("Write all of your text in Spanish" in p for p in PROMPTS)
    return (["Candidate A", "Investigación asistida por IA"]
            + ([] if asked_spanish else ["<candidate prompt asked for Spanish>"])), ["<script"]


def switch_language(at):
    # Start in English, type an address, switch to Spanish, then use another section
    go(at, "📍 Polling Finder")
    at.text_input(key="address").input(ADDR).run()
    next(s for s in at.sidebar.selectbox if s.label == "Language / Idioma").set_value("es").run()
    go(at, "🏛️ My Representatives")
    button(at, "Buscar mis representantes").click().run()
    return [f"TextInput: {ADDR}", "Senado estatal — Distrito 37"]


SECTIONS = [home, home_card, polling, ballot, ballot_not_published, deadlines, deadlines_sc,
            my_reps, shared_address, rep_map, bills, compare, candidates, theme, switch_language]
SPANISH_SECTIONS = [es_home, es_ballot, es_deadlines, es_my_reps, es_rep_map, es_bills, es_candidates]


def main():
    os.chdir(ROOT)
    requests.get, requests.post = fake_get, fake_post
    snapshot = sys.argv[sys.argv.index("--snapshot") + 1] if "--snapshot" in sys.argv else None

    failures, dump = [], []
    runs = [(s, "en") for s in SECTIONS] + [(s, "es") for s in SPANISH_SECTIONS]
    for section, lang in runs:
        at = new_app(lang)
        if at.exception:
            failures.append(f"{section.__name__}: app failed to start — {at.exception[0].value}")
            continue
        try:
            # A section returns the text that must appear, optionally with text that must not
            result = section(at)
            expected, forbidden = result if isinstance(result, tuple) else (result, [])
        except Exception as e:
            failures.append(f"{section.__name__}: test step failed — {e!r}")
            continue
        out = rendered(at)
        text = "\n".join(out)
        problems = [f"exception: {ex.value}" for ex in at.exception]
        problems += [f"missing {s!r}" for s in expected if s not in text]
        problems += [f"should not contain {s!r}" for s in forbidden if s in text]
        for p in problems:
            failures.append(f"{section.__name__}: {p}")
        print(f"{'FAIL' if problems else 'ok  '} {section.__name__}")
        dump.append(f"===== {section.__name__} =====\n{text}")

    if snapshot:
        with open(snapshot, "w", encoding="utf-8") as f:
            f.write("\n".join(dump))
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("All sections rendered.")


if __name__ == "__main__":
    main()
