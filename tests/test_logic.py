"""Unit tests for the pure logic: district matching, labels, party names, races, and HTML
safety. No network or API keys needed.

Run from the project root:
    python -m unittest discover -s tests -v
"""
import os
import unittest

import support  # noqa: F401  (fake API keys; must come before civiclens imports)

from civiclens.data.governors import commons_thumb, normalize_party  # noqa: E402
from civiclens.data.tiger import extract_district_key  # noqa: E402
from civiclens.helpers import (build_rep_lookup, esc, get_chamber_label, html_block,  # noqa: E402
                               party_css, sanitize_ai_html, state_legislator_title)
from civiclens.states import get_candidate_races  # noqa: E402
from civiclens.theme import theme_ai_html  # noqa: E402


def rep(district, title="Senator", org="upper", jur_class="state", jur_name="North Carolina"):
    return {"name": f"Rep {district}",
            "current_role": {"district": district, "title": title, "org_classification": org},
            "jurisdiction": {"classification": jur_class, "name": jur_name}}


class DistrictMatching(unittest.TestCase):
    """The map's shapes (Census) and people (OpenStates / congress-legislators) are joined
    on district number, so both sides must normalize "037", "NC-14", and "14" the same way."""

    def test_rep_lookup_normalizes_district_numbers(self):
        lookup = build_rep_lookup([rep("037"), rep("NC-14"), rep("5")])
        self.assertEqual(sorted(lookup), ["14", "37", "5"])

    def test_rep_lookup_keeps_letter_districts(self):
        # Matching is number-based; a district with no digits is kept as written
        self.assertIn("A", build_rep_lookup([rep("A")]))

    def test_rep_lookup_skips_missing_district(self):
        self.assertEqual(build_rep_lookup([rep("")]), {})

    def test_district_key_reads_named_field(self):
        self.assertEqual(extract_district_key({"SLDU": "037"}, "SLDU"), "37")

    def test_district_key_pulls_number_from_text(self):
        self.assertEqual(extract_district_key({"CD119": "District 5"}, "CD119"), "5")

    def test_district_key_falls_back_to_legacy_fields(self):
        self.assertEqual(extract_district_key({"CD118": "12"}, "CD119"), "12")

    def test_district_key_empty_when_nothing_matches(self):
        self.assertEqual(extract_district_key({"OTHER": "x"}, "CD119"), "")

    def test_both_sides_agree(self):
        shape_key = extract_district_key({"SLDL": "099"}, "SLDL")
        self.assertIn(shape_key, build_rep_lookup([rep("99", org="lower")]))


class Labels(unittest.TestCase):
    def test_state_prefix_added(self):
        self.assertEqual(state_legislator_title("Senator"), "State Senator")

    def test_state_prefix_not_doubled(self):
        self.assertEqual(state_legislator_title("State Representative"), "State Representative")

    def test_dc_council_left_alone(self):
        self.assertEqual(state_legislator_title("Councilmember", "District of Columbia"), "Councilmember")

    def test_empty_title(self):
        self.assertEqual(state_legislator_title(""), "")

    def test_chamber_label_state_legislator(self):
        self.assertEqual(get_chamber_label(rep("15")), "State Senator — District 15")

    def test_chamber_label_us_senator_uses_state_name(self):
        senator = rep("North Carolina", org="upper", jur_class="country", jur_name="United States")
        self.assertEqual(get_chamber_label(senator), "U.S. Senator — North Carolina")

    def test_chamber_label_us_house(self):
        house = rep("NC-14", org="lower", jur_class="country", jur_name="North Carolina")
        self.assertEqual(get_chamber_label(house), "U.S. House — District 14")


class Parties(unittest.TestCase):
    def test_wikidata_party_names(self):
        self.assertEqual(normalize_party("Democratic Party of Oregon"), "Democratic")
        self.assertEqual(normalize_party("Republican Party"), "Republican")
        self.assertEqual(normalize_party("Green Party"), "Green")
        self.assertEqual(normalize_party(""), "Unknown")

    def test_party_css(self):
        self.assertEqual(party_css("Democratic"), "democrat")
        self.assertEqual(party_css("Republican"), "republican")
        self.assertEqual(party_css("Libertarian"), "other")

    def test_commons_thumb(self):
        url = "http://commons.wikimedia.org/wiki/Special:FilePath/Gov.jpg"
        self.assertEqual(commons_thumb(url),
                         "https://commons.wikimedia.org/wiki/Special:FilePath/Gov.jpg?width=220")
        self.assertEqual(commons_thumb(""), "")


class CandidateRaces(unittest.TestCase):
    def test_dc_has_mayor_and_council(self):
        races = get_candidate_races("DC")
        self.assertIn("Mayor", races)
        self.assertNotIn("Governor", races)
        self.assertEqual(races["D.C. Council (enter ward below)"], ("D.C. Council", "Ward"))

    def test_at_large_state_has_no_district(self):
        self.assertEqual(get_candidate_races("WY")["U.S. House (at-large)"], ("U.S. House At-Large", None))

    def test_nebraska_unicameral(self):
        races = get_candidate_races("NE")
        self.assertIn("Nebraska State Legislature (enter district below)", races)
        self.assertFalse(any("State Senate" in label for label in races))

    def test_california_assembly(self):
        self.assertIn("California State Assembly (enter district below)", get_candidate_races("CA"))


class HtmlSafety(unittest.TestCase):
    def test_esc_escapes_tags_and_quotes(self):
        self.assertEqual(esc("<b>A & B's</b>"), "&lt;b&gt;A &amp; B&#x27;s&lt;/b&gt;")
        self.assertEqual(esc(None), "")

    def test_sanitize_removes_script(self):
        self.assertNotIn("script", sanitize_ai_html("<p>Hi</p><script>alert(1)</script>"))

    def test_sanitize_removes_event_attributes(self):
        out = sanitize_ai_html('<h4 onclick="x()" style="margin:0">Name</h4>')
        self.assertEqual(out, '<h4 style="margin:0">Name</h4>')

    def test_sanitize_neutralizes_javascript_links(self):
        self.assertEqual(sanitize_ai_html('<a href="javascript:x()">site</a>'), '<a href="#">site</a>')

    def test_sanitize_keeps_normal_links_and_text(self):
        markup = '<a href="https://example.com" target="_blank">Campaign</a> runs on transit'
        self.assertEqual(sanitize_ai_html(markup), markup)

    def test_html_block_drops_blank_and_indented_lines(self):
        self.assertEqual(html_block("<div>\n\n    <p>x</p>\n</div>"), "<div>\n<p>x</p>\n</div>")

    def test_theme_ai_html_swaps_light_colors(self):
        self.assertEqual(theme_ai_html("background:#f8f9fa; color:#555"),
                         "background:var(--cl-card); color:var(--cl-muted)")


class Ballot(unittest.TestCase):
    """parse_ballot() against the shape of a real voterinfo response (Virginia, Oct 2026)."""
    SAMPLE = {
        "election": {"name": "2026 General Midterm Election", "electionDay": "2026-11-03"},
        "contests": [
            {"type": "ballot-measure", "ballotPlacement": "27", "district": {"name": "Virginia"},
             "referendumTitle": "Proposed Constitutional Amendment Question 1",
             "referendumText": "Question: Should the Constitution be amended?",
             "referendumBallotResponses": ["Yes", "No"]},
            {"type": "General", "ballotPlacement": "2", "office": "Member, House of Representatives (4th District)",
             "district": {"name": "04"}, "numberVotingFor": 1,
             "candidates": [{"name": "A. Candidate", "party": "Democratic"}, {"name": "B. Candidate"}]},
            {"type": "General", "ballotPlacement": "1", "office": "Member, United States Senate",
             "district": {"name": "United States Of America"}, "numberVotingFor": 1,
             "candidates": [{"name": "C. Candidate", "party": "Republican", "candidateUrl": "https://example.com"}]},
        ],
    }

    def test_races_and_measures_split_in_ballot_order(self):
        from civiclens.data.civic import parse_ballot
        ballot = parse_ballot(self.SAMPLE)
        self.assertEqual(ballot["election"], "2026 General Midterm Election")
        self.assertEqual([r["office"] for r in ballot["races"]],
                         ["Member, United States Senate", "Member, House of Representatives (4th District)"])
        self.assertEqual(ballot["measures"][0]["responses"], ["Yes", "No"])

    def test_missing_fields_default_cleanly(self):
        from civiclens.data.civic import parse_ballot
        race = parse_ballot(self.SAMPLE)["races"][1]
        self.assertEqual(race["candidates"][1], {"name": "B. Candidate", "party": "", "url": ""})
        self.assertEqual(parse_ballot(self.SAMPLE)["races"][0]["candidates"][0]["url"], "https://example.com")

    def test_no_contests(self):
        from civiclens.data.civic import parse_ballot
        self.assertEqual(parse_ballot({})["races"], [])
        self.assertEqual(parse_ballot({"error": {"message": "Election unknown"}})["measures"], [])


class Spanish(unittest.TestCase):
    """Every t("...") literal needs a Spanish entry with the same {placeholders} —
    a missing one silently shows English, a mismatched one crashes the page."""

    @staticmethod
    def literal_keys():
        import ast
        import glob
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = glob.glob(os.path.join(root, "civiclens", "**", "*.py"), recursive=True)
        paths.append(os.path.join(root, "civiclens_app.py"))
        keys = set()
        for path in paths:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "t" and node.args
                        and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    keys.add(node.args[0].value)
        return keys

    def test_every_literal_has_spanish(self):
        from civiclens.i18n import ES
        missing = sorted(k for k in self.literal_keys() if k not in ES)
        self.assertEqual(missing, [])

    def test_data_driven_labels_have_spanish(self):
        from civiclens.data.civic import STATE_OFFICIAL_LINKS
        from civiclens.deadline_data import STATE_DEADLINES
        from civiclens.i18n import ES
        from civiclens.states import STATES
        labels = [s["name"] for s in STATES.values()]
        for data in STATE_DEADLINES.values():
            labels += [data["source"]] + [item["name"] for item in data["items"]]
        for _, links in STATE_OFFICIAL_LINKS.values():
            labels += [label for label, _ in links]
        from civiclens.tabs.home import FEATURES, TRUST
        labels += list(FEATURES) + [text for _, title, desc in TRUST for text in (title, desc)]
        self.assertEqual(sorted(set(label for label in labels if label not in ES)), [])

    def test_placeholders_match(self):
        import string
        from civiclens.i18n import ES
        fields = lambda s: sorted(f for _, f, _, _ in string.Formatter().parse(s) if f)
        bad = [k for k, v in ES.items() if fields(k) != fields(v)]
        self.assertEqual(bad, [])

    def test_dates(self):
        import streamlit as st
        from civiclens.i18n import format_date, format_range
        st.session_state["lang"] = "es"
        try:
            self.assertEqual(format_date("2026-10-09", "5 p.m."), "5 p. m. del viernes 9 de octubre de 2026")
            self.assertEqual(format_range("2026-10-15", "2026-10-31"), "15 de octubre – 31 de octubre de 2026")
        finally:
            st.session_state["lang"] = "en"
        self.assertEqual(format_date("2026-10-09", "5 p.m."), "5 p.m. Friday, October 9, 2026")
        self.assertEqual(format_range("2026-09-18", "2026-10-31"), "September 18 – October 31, 2026")


class DeadlineData(unittest.TestCase):
    def test_items_are_well_formed(self):
        import datetime
        from civiclens.deadline_data import STATE_DEADLINES
        election = datetime.date(2026, 11, 3)
        for abbr, data in STATE_DEADLINES.items():
            datetime.date.fromisoformat(data["verified"])
            for item in data["items"]:
                where = f"{abbr}: {item['name']}"
                self.assertTrue(item["url"].startswith("https://"), where)
                self.assertTrue(item["note"]["en"] and item["note"]["es"], where)
                if "date" in item:
                    days = [datetime.date.fromisoformat(item["date"])]
                else:
                    days = [datetime.date.fromisoformat(item["start"]), datetime.date.fromisoformat(item["end"])]
                    self.assertLessEqual(days[0], days[1], where)
                # Every 2026 general election deadline falls between September and a few days after Election Day
                for day in days:
                    self.assertTrue(datetime.date(2026, 9, 1) <= day <= election + datetime.timedelta(days=7), where)




class HouseLabels(unittest.TestCase):
    """U.S. House labels show the district number, not the raw "NC-14" / "WY-0" code."""

    def house(self, district):
        return rep(district, org="lower", jur_class="country", jur_name="Wyoming")

    def test_state_prefix_and_leading_zeros_dropped(self):
        self.assertEqual(get_chamber_label(self.house("014")), "U.S. House — District 14")

    def test_at_large_seat(self):
        for district in ("WY-0", "0", "00", "AL", "At-Large"):
            self.assertEqual(get_chamber_label(self.house(district)), "U.S. House At-Large", district)


class PartyHelpers(unittest.TestCase):
    def test_missing_party_does_not_crash(self):
        from civiclens.helpers import party_badge, party_color, party_fill, party_label
        self.assertEqual(party_css(None), "other")
        self.assertEqual(party_badge(None), "badge-other")
        self.assertEqual(party_color(None), "#7f8c8d")
        self.assertEqual(party_fill(None), ("#888888", 0.15))
        self.assertEqual(party_label(None), "Unknown")

    def test_colors_and_badges(self):
        from civiclens.helpers import party_badge, party_color, party_fill
        self.assertEqual(party_color("Democratic-Farmer-Labor"), "#1a73e8")
        self.assertEqual(party_color("Libertarian"), "#f39c12")
        self.assertEqual(party_color("Green"), "#27ae60")
        self.assertEqual(party_badge("Republican"), "badge-republican")
        self.assertEqual(party_fill("Democratic"), ("#1a73e8", 0.25))

    def test_federal_or_state(self):
        from civiclens.helpers import is_federal, is_state
        self.assertTrue(is_federal(rep("NC-1", jur_class="country")))
        self.assertTrue(is_state(rep("15")))
        self.assertFalse(is_federal({}) or is_state({}))


class DeadlineStatus(unittest.TestCase):
    """The Passed / Today / Tomorrow / In N days badge, against a fixed "today"."""

    def badge(self, last_day, today="2026-10-13"):
        import datetime
        from unittest import mock
        from civiclens.tabs import deadlines
        with mock.patch.object(deadlines, "today", return_value=datetime.date.fromisoformat(today)):
            return deadlines.status_badge(last_day)

    def test_passed(self):
        self.assertIn(">Passed<", self.badge("2026-10-12"))

    def test_today(self):
        self.assertIn(">Today<", self.badge("2026-10-13"))

    def test_tomorrow(self):
        self.assertIn(">Tomorrow<", self.badge("2026-10-14"))

    def test_within_a_week(self):
        self.assertIn(">In 7 days<", self.badge("2026-10-20"))

    def test_more_than_a_week_has_no_badge(self):
        self.assertEqual(self.badge("2026-10-21"), "")


class ElectionCountdown(unittest.TestCase):
    def countdown(self, days):
        from unittest import mock
        from civiclens.tabs import home
        with mock.patch.object(home, "days_until_election", return_value=days):
            return home.countdown_html()

    def test_days_until_election(self):
        import datetime
        from civiclens.ui import days_until_election
        self.assertEqual(days_until_election(datetime.date(2026, 10, 13)), 21)
        self.assertEqual(days_until_election(datetime.date(2026, 11, 3)), 0)

    def test_labels(self):
        self.assertIn("days until Election Day", self.countdown(2))
        self.assertIn("day until Election Day", self.countdown(1))
        self.assertNotIn("days until", self.countdown(1))
        self.assertIn("Election Day is today", self.countdown(0))

    def test_hidden_after_election_day(self):
        self.assertEqual(self.countdown(-1), "")


class I18nHelpers(unittest.TestCase):
    def setUp(self):
        import streamlit as st
        self.st = st
        self.addCleanup(st.session_state.__setitem__, "lang", "en")

    def test_translate_falls_back_to_english(self):
        from civiclens.i18n import ES, translate
        self.assertEqual(translate("Not a real string", "es"), "Not a real string")
        self.assertEqual(translate("Passed", "es"), ES["Passed"])
        self.assertEqual(translate("Passed", "en"), "Passed")

    def test_pick_and_month_day(self):
        from civiclens.i18n import month_day, pick
        self.st.session_state["lang"] = "es"
        self.assertEqual(pick({"en": "Hi", "es": "Hola"}), "Hola")
        self.assertEqual(month_day("2026-10-09"), ("oct", 9))
        self.st.session_state["lang"] = "en"
        self.assertEqual(pick({"en": "Hi"}), "Hi")
        self.assertEqual(month_day("2026-10-09"), ("Oct", 9))

    def test_label_func_keeps_language_from_draw_time(self):
        # Streamlit can call format_func after the run, when the session can't be read
        from civiclens.i18n import ES, label_func
        self.st.session_state["lang"] = "es"
        fmt = label_func()
        self.st.session_state["lang"] = "en"
        self.assertEqual(fmt("North Carolina"), ES["North Carolina"])


class BillHelpers(unittest.TestCase):
    def test_abstract_skips_empty_entries(self):
        from civiclens.tabs.bills import bill_abstract
        self.assertEqual(bill_abstract({"abstracts": [{"abstract": "  "}, {"abstract": " Raises pay. "}]}),
                         "Raises pay.")
        self.assertEqual(bill_abstract({"abstracts": None}), "")
        self.assertEqual(bill_abstract({}), "")

    def test_primary_sponsor_preferred(self):
        from civiclens.tabs.bills import primary_sponsor
        bill = {"sponsorships": [
            {"primary": False, "name": "Co Sponsor"},
            {"primary": True, "name": "Main Sponsor",
             "person": {"party": "Republican", "current_role": {"title": "Senator"}}}]}
        self.assertEqual(primary_sponsor(bill), ("Main Sponsor", "Republican", "Senator"))

    def test_first_sponsor_when_none_primary(self):
        from civiclens.tabs.bills import primary_sponsor
        bill = {"sponsorships": [{"person": {"name": "Only Person"}}]}
        self.assertEqual(primary_sponsor(bill), ("Only Person", "", ""))
        self.assertEqual(primary_sponsor({}), ("", "", ""))


class ContactLinks(unittest.TestCase):
    def test_mailto_skips_urls_and_escapes(self):
        from civiclens.tabs.my_reps import mailto_link
        self.assertEqual(mailto_link("https://example.gov/contact"), "")
        self.assertEqual(mailto_link(""), "")
        self.assertIn("mailto:a&amp;b@nc.gov", mailto_link("a&b@nc.gov"))

    def test_contact_form(self):
        from civiclens.tabs.my_reps import contact_form_link
        self.assertEqual(contact_form_link(""), "")
        self.assertIn("href='https://x.gov/?a=1&amp;b=2'", contact_form_link("https://x.gov/?a=1&b=2"))

    def test_governor_links(self):
        from civiclens.data.governors import governor_links_html
        html = governor_links_html({"site": "https://www.governor.nc.gov/",
                                    "wikipedia": "https://en.wikipedia.org/wiki/X"})
        self.assertIn(">governor.nc.gov<", html)
        self.assertIn(">Wikipedia<", html)
        self.assertEqual(governor_links_html({}), "")
        self.assertNotIn("Wikipedia", governor_links_html({"site": "https://gov.ca.gov"}))


class RateLimit(unittest.TestCase):
    def test_blocks_after_limit_then_recovers(self):
        import types
        from unittest import mock
        from civiclens import helpers
        clock = [1000.0]
        with mock.patch.object(helpers, "st", types.SimpleNamespace(session_state={})), \
                mock.patch.object(helpers.time, "time", lambda: clock[0]):
            self.assertTrue(all(helpers.rate_limit_check("k", max_calls=5, window=60) for _ in range(5)))
            self.assertFalse(helpers.rate_limit_check("k", max_calls=5, window=60))
            clock[0] += 61
            self.assertTrue(helpers.rate_limit_check("k", max_calls=5, window=60))


class StaticData(unittest.TestCase):
    def test_states_registry(self):
        from civiclens.states import STATE_NAME_TO_ABBR, STATES
        self.assertEqual(len(STATES), 51)
        self.assertEqual(len({s["fips"] for s in STATES.values()}), 51)
        for abbr, info in STATES.items():
            self.assertRegex(info["fips"], r"^\d{2}$", abbr)
            self.assertEqual(STATE_NAME_TO_ABBR[info["name"].lower()], abbr)
        self.assertEqual(STATE_NAME_TO_ABBR["washington, d.c."], "DC")

    def test_palettes(self):
        from civiclens.theme import PALETTES
        for key, palette in PALETTES.items():
            self.assertEqual(len(palette), 7, key)
            for color in palette[1:]:
                self.assertRegex(color, r"^#[0-9A-Fa-f]{6}$", key)

    def test_official_links_are_https(self):
        from civiclens.data.civic import STATE_OFFICIAL_LINKS, get_official_resources
        from civiclens.states import STATES
        for abbr in STATES:
            for label, url in get_official_resources(abbr):
                self.assertTrue(url.startswith("https://"), f"{abbr}: {label}")
        self.assertEqual(set(STATE_OFFICIAL_LINKS), {"NC", "SC", "VA", "TN", "GA"})

    def test_generic_resources_use_lowercase_vote_gov_path(self):
        from civiclens.data.civic import get_official_resources
        urls = [url for _, url in get_official_resources("CA")]
        self.assertIn("https://vote.gov/register/ca/", urls)
        self.assertEqual(get_official_resources(""), get_official_resources("NC"))


if __name__ == "__main__":
    unittest.main()
