"""Unit tests for the code that calls outside services: governors (Wikidata), geocoding,
congress rosters, TIGERweb boundaries, OpenStates, Google Civic, the Rep Map layer, and
the AI calls. Every request is mocked, so no network or API keys are needed.

Run from the project root:
    python -m unittest discover -s tests -v
"""
import unittest
from unittest import mock

import support  # noqa: F401  (fake API keys; must come before civiclens imports)
from support import FAKE_GEMINI_KEY, response

from civiclens.data import ai, civic, congress, geocode, governors, openstates, tiger  # noqa: E402


def binding(state, name, start="", **extra):
    """One row of a Wikidata SPARQL result."""
    row = {"placeLabel": {"value": state}, "govLabel": {"value": name}}
    if start:
        row["start"] = {"value": f"{start}T00:00:00Z"}
    for key, value in extra.items():
        row[key] = {"value": value}
    return row


class Governors(unittest.TestCase):
    ROWS = [
        binding("North Carolina", "Old Governor", "2017-01-01", partyLabel="Democratic Party"),
        binding("North Carolina", "Josh Stein", "2025-01-01", partyLabel="Democratic Party",
                possite="https://governor.nc.gov/"),
        binding("North Carolina", "Governor Elect", "2099-01-01"),
        binding("North Carolina", "No Start Date"),
        binding("District of Columbia", "Muriel Bowser", "2015-01-02"),
        binding("California", "Gavin Newsom", "2019-01-07"),
        # Two people with the same start date, each with different optional fields
        binding("Ohio", "Person B", "2019-01-14", img="http://commons.wikimedia.org/B.jpg"),
        binding("Ohio", "Person A", "2019-01-14", partyLabel="Republican Party"),
    ]

    def setUp(self):
        governors._fetch_governors_cached.clear()

    def fetch(self, rows=None, status=200):
        payload = {"results": {"bindings": self.ROWS if rows is None else rows}}
        with mock.patch.object(governors.requests, "get", return_value=response(status, payload)):
            return governors._fetch_governors_cached()

    def test_most_recent_start_wins(self):
        nc = self.fetch()["NC"]
        self.assertEqual(nc["name"], "Josh Stein")
        self.assertEqual(nc["party"], "Democratic")
        self.assertEqual(nc["site"], "https://governor.nc.gov/")

    def test_dc_is_a_mayor(self):
        self.assertEqual(self.fetch()["DC"]["office"], "Mayor")
        self.assertEqual(self.fetch()["NC"]["office"], "Governor")

    def test_california_site_fallback(self):
        self.assertEqual(self.fetch()["CA"]["site"], "https://www.gov.ca.gov/")

    def test_tie_keeps_one_person(self):
        oh = self.fetch()["OH"]
        self.assertEqual(oh["name"], "Person A")
        self.assertEqual(oh["party"], "Republican")
        self.assertEqual(oh["photo"], "")  # Person B's photo must not be mixed in

    def test_failure_raises_and_is_not_cached(self):
        with self.assertRaises(governors.GovernorFetchError):
            self.fetch(status=500)
        with self.assertRaises(governors.GovernorFetchError):
            self.fetch(rows=[])
        self.assertIn("NC", self.fetch())

    def test_get_governor_messages(self):
        with mock.patch.object(governors, "_fetch_governors_cached", return_value={"NC": {"name": "X"}}):
            self.assertEqual(governors.get_governor("nc"), ({"name": "X"}, ""))
            self.assertEqual(governors.get_governor("DC"), (None, "no current mayor listed for DC"))
            self.assertEqual(governors.get_governor("TX"), (None, "no current governor listed for TX"))
            self.assertEqual(governors.get_governor(""), (None, ""))
        with mock.patch.object(governors, "_fetch_governors_cached",
                               side_effect=governors.GovernorFetchError("HTTP 502")):
            self.assertEqual(governors.get_governor("NC"), (None, "HTTP 502"))


class Geocode(unittest.TestCase):
    def locate(self, results=None, error=None):
        get = mock.Mock(side_effect=error) if error else mock.Mock(return_value=response(200, results))
        geocode.geocode.clear()  # every call here uses the same address
        with mock.patch.object(geocode.requests, "get", get):
            return geocode.geocode("an address")

    def result(self, **address):
        return [{"lat": "35.78", "lon": "-78.64", "address": address}]

    def test_iso_code(self):
        self.assertEqual(self.locate(self.result(**{"ISO3166-2-lvl4": "US-NC", "state": "Ohio"})),
                         (35.78, -78.64, "NC"))

    def test_state_name_fallback(self):
        self.assertEqual(self.locate(self.result(state="Virginia"))[2], "VA")
        self.assertEqual(self.locate(self.result(state="Washington, D.C."))[2], "DC")

    def test_territory_has_no_state(self):
        self.assertIsNone(self.locate(self.result(**{"ISO3166-2-lvl4": "US-PR", "state": "Puerto Rico"}))[2])

    def test_no_result_or_error(self):
        self.assertEqual(self.locate([]), (None, None, None))
        self.assertEqual(self.locate(error=ConnectionError("down")), (None, None, None))


class Congress(unittest.TestCase):
    MEMBERS = [
        {"id": {"bioguide": "R1"}, "name": {"first": "Wy", "last": "Rep"},
         "terms": [{"type": "rep", "state": "WY", "district": 0, "party": "Republican"}]},
        {"id": {"bioguide": "R2"}, "name": {"first": "Nc", "last": "Rep"},
         "terms": [{"type": "sen", "state": "NC"}, {"type": "rep", "state": "NC", "district": 4,
                                                    "party": "Democrat"}]},
        {"id": {"bioguide": "S1"}, "name": {"official_full": "Junior Senator"},
         "terms": [{"type": "sen", "state": "NC", "party": "Republican", "state_rank": "junior"}]},
        {"id": {"bioguide": "S2"}, "name": {"official_full": "Senior Senator"},
         "terms": [{"type": "sen", "state": "NC", "party": "Independent", "state_rank": "senior",
                    "contact_form": "https://senate.gov/contact"}]},
    ]

    def setUp(self):
        congress.get_federal_house_members.clear()
        congress.get_federal_senators.clear()
        patcher = mock.patch.object(congress, "_fetch_congress_legislators", return_value=self.MEMBERS)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_house_uses_latest_term_and_party_names(self):
        nc = congress.get_federal_house_members("nc")
        self.assertEqual([m["name"] for m in nc], ["Nc Rep"])
        self.assertEqual(nc[0]["party"], "Democratic")
        self.assertEqual(nc[0]["current_role"]["district"], "NC-4")

    def test_at_large_seat_matches_the_map(self):
        from civiclens.helpers import build_rep_lookup, get_chamber_label
        wy = congress.get_federal_house_members("WY")
        self.assertIn(tiger.extract_district_key({"CD119": "00"}, "CD119"), build_rep_lookup(wy))
        self.assertEqual(get_chamber_label(wy[0]), "U.S. House At-Large")

    def test_senators_senior_first(self):
        senators = congress.get_federal_senators("NC")
        self.assertEqual([s["name"] for s in senators], ["Senior Senator", "Junior Senator"])
        self.assertEqual(senators[0]["email"], "https://senate.gov/contact")
        self.assertEqual(senators[0]["current_role"]["district"], "North Carolina")

    def test_dc_has_no_senators(self):
        self.assertEqual(congress.get_federal_senators("DC"), [])


class TigerBoundaries(unittest.TestCase):
    FEATURES = {"features": [{"properties": {"CD119": "01"}}]}

    def setUp(self):
        tiger._fetch_tiger_geojson_cached.clear()

    def test_tries_next_query_when_first_is_empty(self):
        get = mock.Mock(side_effect=[response(200, {"features": []}), response(200, self.FEATURES)])
        with mock.patch.object(tiger.requests, "get", get):
            self.assertEqual(tiger.fetch_tiger_geojson(0, "37", "NC"), (self.FEATURES, ""))
        self.assertEqual([c.kwargs["params"]["where"] for c in get.call_args_list], ["STATE='37'", "STATE=37"])

    def test_failure_is_reported_and_not_cached(self):
        with mock.patch.object(tiger.requests, "get", return_value=response(500)):
            self.assertEqual(tiger.fetch_tiger_geojson(1, "37", "NC"), ({}, "HTTP 500"))
        with mock.patch.object(tiger.requests, "get", return_value=response(200, self.FEATURES)):
            self.assertEqual(tiger.fetch_tiger_geojson(1, "37", "NC"), (self.FEATURES, ""))


class OpenStatesRoster(unittest.TestCase):
    def setUp(self):
        openstates.get_state_reps_by_chamber.clear()

    def test_pages_until_a_short_page(self):
        pages = [response(200, {"results": [{}] * 50}), response(200, {"results": [{}] * 20})]
        with mock.patch.object(openstates.requests, "get", side_effect=pages) as get:
            reps, err = openstates.get_state_reps_by_chamber("NC", "upper")
        self.assertEqual((len(reps), err, get.call_count), (70, "", 2))
        self.assertEqual(get.call_args.kwargs["params"]["jurisdiction"], "nc")

    def test_partial_results_with_error(self):
        pages = [response(200, {"results": [{}] * 50}), response(429, text="Too Many Requests")]
        with mock.patch.object(openstates.requests, "get", side_effect=pages):
            reps, err = openstates.get_state_reps_by_chamber("NC", "lower")
        self.assertEqual(len(reps), 50)
        self.assertEqual(err, "HTTP 429: Too Many Requests")


class ActiveElection(unittest.TestCase):
    def setUp(self):
        civic.get_active_election_id.clear()

    def test_skips_googles_test_elections(self):
        payload = {"elections": [{"id": "9000"}, {"id": "9100"}, {"id": "2000"}]}
        with mock.patch.object(civic.requests, "get", return_value=response(200, payload)):
            self.assertEqual(civic.get_active_election_id(), "9100")

    def test_defaults_on_error(self):
        with mock.patch.object(civic.requests, "get", side_effect=ConnectionError("down")):
            self.assertEqual(civic.get_active_election_id(), "2000")


class DistrictLayer(unittest.TestCase):
    """Rep Map: each district shape is colored by its representative's party."""

    @staticmethod
    def shape(district):
        return {"type": "Feature", "properties": {"CD119": district},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}}

    def layer(self, district, lookup):
        from civiclens.tabs.rep_map import build_district_layer
        fg = build_district_layer({"features": [self.shape(district)]}, lookup, "Layer", "CD119")
        geo = list(fg._children.values())[0]
        tooltip = next(c for c in geo._children.values() if type(c).__name__ == "Tooltip")
        return geo.style_function(self.shape(district))["fillColor"], tooltip.text

    def test_matched_district_colored_and_escaped(self):
        rep = {"name": "A <b>Rep</b>", "party": "Republican",
               "current_role": {"district": "1"}, "jurisdiction": {"classification": "state"}}
        color, tooltip = self.layer("01", {"1": rep})
        self.assertEqual(color, "#c0392b")
        self.assertIn("A &lt;b&gt;Rep&lt;/b&gt;", tooltip)

    def test_unmatched_district_is_gray(self):
        color, tooltip = self.layer("02", {})
        self.assertEqual(color, "#888888")
        self.assertIn("No data", tooltip)

    def test_empty_geojson(self):
        from civiclens.tabs.rep_map import build_district_layer
        self.assertEqual(len(build_district_layer({}, {}, "Layer")._children), 0)


class BillSummaryPrompt(unittest.TestCase):
    def test_abstract_is_used_and_capped(self):
        prompt = ai._bill_summary_prompt("Title", "Filed", "Virginia", "en", "x" * 5000)
        self.assertIn("Use ONLY the official summary below", prompt)
        self.assertIn("x" * 4000, prompt)
        self.assertNotIn("x" * 4001, prompt)

    def test_title_only_without_abstract(self):
        prompt = ai._bill_summary_prompt("Senate Rules", "Filed", "North Carolina", "en", "")
        self.assertIn("Only this North Carolina bill's title is available", prompt)
        self.assertIn("Do not guess", prompt)
        self.assertNotIn("Official summary:", prompt)

    def test_spanish(self):
        self.assertIn("plain Spanish", ai._bill_summary_prompt("T", "A", "Texas", "es", ""))
        self.assertIn("plain English", ai._bill_summary_prompt("T", "A", "Texas", "en", ""))


class BillSummaryFallback(unittest.TestCase):
    """Bill summaries fall back from Gemini to Groq, and a failed call isn't cached."""

    def setUp(self):
        ai._gemini_bill_summary.clear()
        ai._groq_bill_summary.clear()

    def summary(self, title):
        return ai.get_bill_summary("b", title, "Filed", "Virginia", "en", "Official text.")

    def test_groq_answers_when_gemini_is_rate_limited(self):
        def post(url, **kwargs):
            if "generativelanguage" in url:
                return response(429, {"error": {}})
            return response(200, {"choices": [{"message": {"content": "From Groq."}}]})
        with mock.patch.object(ai.requests, "post", side_effect=post):
            self.assertEqual(self.summary("Fallback bill"), "From Groq.")

    def test_failure_is_not_cached_and_hides_the_key(self):
        error = ConnectionError(f"url /v1beta?key={FAKE_GEMINI_KEY}")
        with mock.patch.object(ai.requests, "post", side_effect=error):
            first = self.summary("Retry bill")
        self.assertTrue(first.startswith("⚠️"))
        self.assertNotIn(FAKE_GEMINI_KEY, first)
        ok = response(200, {"candidates": [{"content": {"parts": [{"text": "Works now."}]}}]})
        with mock.patch.object(ai.requests, "post", return_value=ok):
            self.assertEqual(self.summary("Retry bill"), "Works now.")

    def test_no_keys(self):
        with mock.patch.object(ai, "GEMINI_KEY", ""), mock.patch.object(ai, "GROQ_KEY", ""):
            self.assertIn("No AI API key", self.summary("No keys"))


class CandidateResearch(unittest.TestCase):
    GEMINI_OK = {"candidates": [{"content": {"parts": [{"text": "```html\n<div>Card</div>\n```"}]}}]}

    def setUp(self):
        ai._gemini_candidate_info.clear()
        ai._candidate_info_fallback_cached.clear()

    def test_retries_once_when_overloaded(self):
        posts = [response(503), response(200, self.GEMINI_OK)]
        with mock.patch.object(ai.requests, "post", side_effect=posts), \
                mock.patch.object(ai.time, "sleep") as sleep:
            self.assertEqual(ai.get_candidate_info("U.S. Senate", "North Carolina"), "<div>Card</div>")
        sleep.assert_called_once()

    def test_other_errors_hand_off_to_the_backup(self):
        with mock.patch.object(ai.requests, "post", return_value=response(429)):
            self.assertIsNone(ai.get_candidate_info("U.S. Senate", "Ohio"))

    def test_backup_needs_both_keys(self):
        with mock.patch.object(ai, "TAVILY_KEY", ""):
            self.assertIn("no fallback keys", ai.candidate_info_fallback("U.S. Senate", "Ohio"))

    def test_backup_search_failure_is_not_cached(self):
        with mock.patch.object(ai.requests, "post", side_effect=ConnectionError("down")):
            self.assertIn("Search unavailable", ai.candidate_info_fallback("Governor", "Texas"))

        def post(url, **kwargs):
            if "tavily" in url:
                return response(200, {"answer": "Results", "results": []})
            return response(200, {"choices": [{"message": {"content": "<div>Groq card</div>"}}]})
        with mock.patch.object(ai.requests, "post", side_effect=post):
            html = ai.candidate_info_fallback("Governor", "Texas")
        self.assertIn("AI-generated from web search", html)
        self.assertTrue(html.endswith("<div>Groq card</div>"))


if __name__ == "__main__":
    unittest.main()
