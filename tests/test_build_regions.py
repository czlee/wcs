"""Unit tests for the Phase 4 / Task 4A region builder.

Cover the pure, well-specified logic (no network): name normalisation, the fuzzy
matcher's acceptance rule, ISO-code canonicalisation, and the registry/JSON-LD parsers.
``build_regions`` is importable thanks to the ``sys.path`` trick in ``tests/conftest.py``.
"""

import build_regions as br


# ---------------------------------------------------------------------------
# norm()
# ---------------------------------------------------------------------------

def test_norm_strips_year_and_filler():
    assert br.norm("Budafest 2025") == "budafest"
    assert br.norm("UK West Coast Swing Championships 2025") == "uk"


def test_norm_strips_glued_registry_suffix():
    # The registry glues "Trial Event"/"Registry Event" onto the name.
    assert br.norm("Swingover 2027Trial Event") == br.norm("Swingover")
    assert br.norm("Baltic SwingRegistry Event") == br.norm("Baltic Swing")


def test_norm_folds_diacritics_and_parentheticals():
    assert br.norm("WCS Festival Düsseldorf") == "dusseldorf"
    assert br.norm("Terra Livre Dance Festival 2025 (Summer Edition)") == "terra livre"


# ---------------------------------------------------------------------------
# fuzzy matcher
# ---------------------------------------------------------------------------

def _index(*names):
    rows = [{"raw_name": n, "city": None, "state_raw": None, "country_raw": "Poland"}
            for n in names]
    return br.build_registry_index(rows)


def test_fuzzy_accepts_subtitle_variant():
    counts = {"scandinavian": 1, "snow": 1}
    assert br.fuzzy_accept(br.norm("Scandinavian Open 2025"),
                           br.norm('Scandinavian Open WCS "SNOW"'), counts)


def test_fuzzy_accepts_typo_by_similarity():
    counts = {"northeast": 1, "classic": 1}
    assert br.fuzzy_accept(br.norm("Northeast Swing Clasic"),
                           br.norm("Northeast Swing Classic"), counts)


def test_fuzzy_rejects_generic_single_token():
    # "cash" is short and could collide across unrelated events -> not confident.
    counts = {"cash": 1, "bash": 1}
    assert not br.fuzzy_accept(br.norm("Cash&Swing 2025"),
                               br.norm("CASH Bash"), counts)


def test_fuzzy_accepts_long_unique_single_token():
    counts = {"flowstate": 1, "zouk": 1}
    assert br.fuzzy_accept(br.norm("Flowstate 2025"),
                           br.norm("Flowstate | West Coast Swing & Zouk Festival"), counts)


def test_fuzzy_rejects_long_token_if_not_unique():
    counts = {"flowstate": 2, "zouk": 1}  # appears in >1 registry name
    assert not br.fuzzy_accept(br.norm("Flowstate 2025"),
                               br.norm("Flowstate Zouk Thing"), counts)


def test_match_event_country_conflict_is_no_match():
    rows = [
        {"raw_name": "Ambiguous Fest", "city": None, "state_raw": None, "country_raw": "Poland"},
        {"raw_name": "Ambiguous Fest", "city": None, "state_raw": None, "country_raw": "Germany"},
    ]
    index = br.build_registry_index(rows)
    counts = br.registry_token_counts(index)
    assert br.match_event("Ambiguous Fest", index, counts) == (None, None, None)


def test_match_event_exact():
    index = _index("Baltic Swing")
    counts = br.registry_token_counts(index)
    row, kind, matched = br.match_event("Baltic Swing 2025", index, counts)
    assert kind == "wsdc-registry-exact"
    assert matched == "Baltic Swing"


# ---------------------------------------------------------------------------
# ISO canonicalisation
# ---------------------------------------------------------------------------

def test_canonicalize_country_aliases():
    assert br.canonicalize_country("United States of America") == "US"
    assert br.canonicalize_country("USA") == "US"
    assert br.canonicalize_country("UK") == "GB"
    assert br.canonicalize_country("South Korea") == "KR"
    assert br.canonicalize_country("Russia") == "RU"


def test_canonicalize_country_via_pycountry():
    assert br.canonicalize_country("Hungary") == "HU"
    assert br.canonicalize_country("New Zealand") == "NZ"


def test_canonicalize_country_unknown_is_none():
    assert br.canonicalize_country("Atlantis") is None
    assert br.canonicalize_country("") is None


def test_canonicalize_us_state_name_and_abbrev():
    assert br.canonicalize_us_state("California") == "US-CA"
    assert br.canonicalize_us_state("CA") == "US-CA"
    assert br.canonicalize_us_state("GA") == "US-GA"
    assert br.canonicalize_us_state("DC") == "US-DC"


def test_canonicalize_us_state_unknown_is_none():
    assert br.canonicalize_us_state("Hawaii/Maui") is None
    assert br.canonicalize_us_state("") is None


# ---------------------------------------------------------------------------
# location string + registry table parsing
# ---------------------------------------------------------------------------

def test_parse_location_string_non_us():
    assert br.parse_location_string("Gdańsk, Pomorskie, Poland") == ("Gdańsk", None, "Poland")


def test_parse_location_string_us_has_state():
    assert br.parse_location_string("Atlanta, GA, USA") == ("Atlanta", "GA", "USA")


def test_parse_location_string_us_four_parts():
    # DC-area rows: "Washington, DC, VA, USA" -> country last, state second-to-last.
    assert br.parse_location_string("Washington, DC, VA, USA") == ("Washington", "VA", "USA")


def test_parse_registry_table():
    html = """
    <table>
      <tr><th>Date</th><th>Event Name</th><th>Event Location</th><th>Country</th></tr>
      <tr><td>Jun 11, 2026</td><td>Baltic Swing<span>Registry Event</span></td>
          <td>Gdańsk, Pomorskie, Poland</td><td></td></tr>
      <tr><td>Jun 25, 2026</td><td>Atlanta Swing Classic Trial Event</td>
          <td>Atlanta, GA, USA</td><td></td></tr>
    </table>
    """
    rows = br.parse_registry_table(html)
    by_name = {r["raw_name"]: r for r in rows}
    assert by_name["Baltic Swing"]["country_raw"] == "Poland"
    assert by_name["Atlanta Swing Classic"]["state_raw"] == "GA"


def test_extract_scoring_dance_location():
    raw = ('...<script type="application/ld+json">{"@type":"DanceEvent",'
           '"location":{"@type":"Place","name":"Burlingame",'
           '"country":"United States of America"},"startDate":"2025-10-16"}</script>...')
    assert br.extract_scoring_dance_location(raw) == ("Burlingame", "United States of America")


def test_extract_scoring_dance_location_absent():
    assert br.extract_scoring_dance_location("<html>no jsonld here</html>") == (None, None)
