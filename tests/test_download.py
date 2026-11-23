"""Unit tests for the pure logic in ``scripts/download.py`` (no network).

Covers the parts that have gone wrong before:

* danceconvention.net's events-archive page is a Nuxt payload in which any field of an
  event can be a literal or a hoisted variable (``eventId:aA`` vs ``eventId:300721130``);
  only literals used to be recognised, so 2026 yielded no events at all.
* the finals-round matcher must cope with underscored round names (``Novice_JJ_Finals``),
  where ``\\b`` doesn't see a word boundary.
* the non-WCS filters (``zouk`` anywhere in a name, ``Blues`` only in division names).
"""

import logging
from datetime import date

import pytest

import download as dl


# ---------------------------------------------------------------------------
# A miniature archive page in the shape the real ones have: an IIFE whose
# parameters are hoisted values, followed by the arguments that fill them in.
# ---------------------------------------------------------------------------
def make_page(entries: str, params: str, args: str) -> str:
    return (
        "<html><script>window.__NUXT__=(function(" + params + "){return {data:["
        + entries + "]}}(" + args + "))</script></html>"
    )


LITERAL = (
    'eventId:300721130,name:"Waffle Fest",startDate:"10\\u002F4\\u002F25",'
    'endDate:"10\\u002F5\\u002F25",eventPage:"\\u002Feventdirector\\u002Fen\\u002F'
    'eventpage\\u002F300721130-waffle-fest"'
)
HOISTED = "eventId:aA,name:aB,startDate:aC,endDate:aD,eventPage:aE"
HOISTED_ARGS = (
    '301399041,"Moscow &amp;#39;26 Gala","11/6/26","11/8/26",'
    '"/eventdirector/en/eventpage/301399041-moscow-gala"'
)
PARAMS = "a,b,aA,aB,aC,aD,aE"
ARGS = "false,true," + HOISTED_ARGS


class TestParseArchiveEvents:
    def test_literal_entry(self):
        page = make_page("{" + LITERAL + "}", PARAMS, ARGS)
        events = dl.parse_archive_events(page)
        assert events == {
            "300721130": ("Waffle Fest", "waffle-fest", date(2025, 10, 4), date(2025, 10, 5))
        }

    def test_hoisted_entry(self):
        # Regression: every field a variable. The old code found 0 events on such pages.
        page = make_page("{" + HOISTED + "}", PARAMS, ARGS)
        events = dl.parse_archive_events(page)
        assert list(events) == ["301399041"]
        name, slug, start, end = events["301399041"]
        assert slug == "moscow-gala"
        assert (start, end) == (date(2026, 11, 6), date(2026, 11, 8))

    def test_names_unescaped_even_when_escaped_twice(self):
        page = make_page("{" + HOISTED + "}", PARAMS, ARGS)
        assert dl.parse_archive_events(page)["301399041"][0] == "Moscow '26 Gala"

    def test_literal_and_hoisted_on_the_same_page(self):
        page = make_page("{" + LITERAL + "},{" + HOISTED + "}", PARAMS, ARGS)
        assert set(dl.parse_archive_events(page)) == {"300721130", "301399041"}

    def test_duplicate_event_ids_are_kept_once(self):
        # The real 2026 page lists each event three times.
        page = make_page("{" + HOISTED + "},{" + HOISTED + "},{" + HOISTED + "}", PARAMS, ARGS)
        assert list(dl.parse_archive_events(page)) == ["301399041"]

    def test_entry_without_a_parseable_date_is_skipped(self, caplog):
        args = ARGS.replace('"11/6/26"', '"soon"')
        page = make_page("{" + HOISTED + "}", PARAMS, args)
        with caplog.at_level(logging.WARNING):
            assert dl.parse_archive_events(page) == {}
        assert "could not parse date" in caplog.text

    def test_end_date_defaults_to_start(self):
        entry = 'eventId:7,name:"One Day",startDate:"1/2/26",eventPage:"/eventdirector/en/eventpage/7-one-day"'
        events = dl.parse_archive_events(make_page("{" + entry + "}", "a", "false"))
        assert events["7"][2] == events["7"][3] == date(2026, 1, 2)

    def test_event_page_must_belong_to_the_same_event(self):
        args = ARGS.replace("301399041-moscow-gala", "999-other-event")
        page = make_page("{" + HOISTED + "}", PARAMS, args)
        assert dl.parse_archive_events(page) == {}

    def test_page_with_no_events_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            assert dl.parse_archive_events("<html>nothing here</html>", label="2099") == {}
        assert "archive 2099: no event entries found" in caplog.text

    def test_page_where_nothing_parses_warns_about_format_change(self, caplog):
        page = make_page("{eventId:aA,name:aB}", PARAMS, ARGS)  # no dates, no event page
        with caplog.at_level(logging.WARNING):
            assert dl.parse_archive_events(page, label="2099") == {}
        assert "page format has probably changed" in caplog.text


# ---------------------------------------------------------------------------
# Finals-round matching
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "round_name",
    [
        "Final", "Finals", "final", "Novice_JJ_Finals", "Novice_JJ_Final",
        "Grand Final", "Jack & Jill Finals", "Финал",
    ],
)
def test_is_finals_round_accepts(round_name):
    assert dl.is_finals_round(round_name)


@pytest.mark.parametrize(
    "round_name",
    [
        "Semi_Finals", "Semi-Final", "Semi Finals", "Quarter Final", "Quarterfinals",
        "Heat_Final", "Prelims", "Prelim", "SSS_Prelim", "Novice_JJ_Semis",
        "Round 1", "Полуфинал", "Четвертьфинал", "Отбор",
    ],
)
def test_is_finals_round_rejects(round_name):
    assert not dl.is_finals_round(round_name)


# ---------------------------------------------------------------------------
# Non-WCS filters
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "name",
    [
        "KemZouk Festival 2026", "ZvukiZouka", "Russian Zouk Congress", "Salsa Congress",
        "Country SwingTime '24", "Hustle Fest", "BRAZUKA SPRING CUP 2026",
        "Australian Ceroc Dance Championships", "Sea Breeze Modern Jive Weekend",
        "Tequila Blues Weekend 2026", "Volga Flow Festival 2026",
    ],
)
def test_non_wcs_event_names(name):
    assert dl.NON_WCS_STYLE_RE.search(name)


@pytest.mark.parametrize(
    "name",
    ["Swing Dance Championships", "Cash&Blues", "The NZ WCS Open 2026", "Swingvasion IV (2026)"],
)
def test_wcs_event_names_are_kept(name):
    assert not dl.NON_WCS_STYLE_RE.search(name)


def test_blues_excludes_divisions_but_not_event_names():
    # "Cash&Blues" is a WCS festival, so Blues must not exclude event names...
    assert not dl.NON_WCS_STYLE_RE.search("Cash&Blues")
    # ...but a Blues division is a side competition.
    assert dl.NON_WCS_DIVISION_RE.search("Blues JnJ newcomer+novice")
    assert not dl.NON_WCS_DIVISION_RE.search("Novice Jack & Jill")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text, expected",
    [("6/21/25", date(2025, 6, 21)), ("12/5/2024", date(2024, 12, 5)), ("soon", None), ("", None)],
)
def test_parse_mdy(text, expected):
    assert dl._parse_mdy(text) == expected


def test_nuxt_var_map_resolves_literals_numbers_and_unicode_escapes():
    page = make_page("{x:1}", "a,b,c", 'false,301399041,"\\u002Fpath"')
    start = page.find("window.__NUXT__=(function(")
    assert dl._nuxt_var_map(page[start:]) == {"a": "false", "b": "301399041", "c": "/path"}
