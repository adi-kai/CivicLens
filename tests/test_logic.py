"""Unit tests for the pure logic: district matching, labels, party names, races, and HTML
safety. No network or API keys needed.

Run from the project root:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        self.assertEqual(get_chamber_label(house), "U.S. House — District NC-14")


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


if __name__ == "__main__":
    unittest.main()
