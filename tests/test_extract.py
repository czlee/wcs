"""Unit tests for the keyword rules in ``scripts/extract.py`` (no files, no network).

``division_level`` and ``dance_format`` are keyword-matched from division names, and the
rules have been adjusted several times as we found divisions landing in the wrong place
(Masters Novice, Master's Choice). These tables pin the current decisions down so the
next tweak can't silently move sheets between levels.
"""

import pytest

import extract as ex


@pytest.mark.parametrize(
    "name, level",
    [
        # Skill ladder
        ("Newcomer Jack & Jill", "Newcomer"),
        ("Novice Jack&Jill final", "Novice"),
        ("WSDC Novice Jack-N-Jill", "Novice"),
        ("Intermediate Strictly", "Intermediate"),
        ("Champions Strictly", "Champions"),
        ("All-American Jack and Jill", "All-American"),
        # Combined rungs resolve to the higher one
        ("Advanced/All-Star J&J", "All-Star"),
        ("All-Stars Champions Jack & Jill", "Champions"),
        # Category / age divisions
        ("Masters Jack&Jill final", "Masters"),
        ("Strictly Swing Masters (50+) Finals", "Masters"),
        ("Sophisticated Jack&Jill", "Sophisticated"),
        ("Junior Jack&Jill", "Junior"),
        ("Invitational Strictly", "Invitational"),
        ("Open Strictly", "Open"),
        # Masters Open is just Masters; Masters Novice is not comparable, so no level
        ("Jack & Jill Masters Open Finals", "Masters"),
        ("Jack & Jill Masters Novice Finals", None),
        ("Masters-Novice Jack&Jill", None),
        ("Masters Newcomer Jack&Jill", None),
        # Master's Choice (one partner 50+) is a different division from Masters
        ("Master's Choice Strictly Finals", None),
        ("Masters Choice final", None),
        ("Strictly Masters Choice final", None),
        # Pro-Am carries the amateur's skill level
        ("ProAm Novice Leader", "Novice"),
        # Nothing to go on
        ("JackPot", None),
        ("Rising Star Routines", None),
        ("Unknown thing", None),
    ],
)
def test_normalise_level(name, level):
    assert ex.normalise_level(name) == level


@pytest.mark.parametrize(
    "name, fmt",
    [
        ("Novice Jack&Jill final", "Jack & Jill"),
        ("WSDC Novice Jack-N-Jill", "Jack & Jill"),
        ("Intermediate Strictly", "Strictly"),
        ("Strictly Swing Masters (50+) Finals", "Strictly"),
        ("All-American Jack and Jill", "Jack & Jill"),
        # Master's Choice is always Strictly, even when the name doesn't say so
        ("Master's Choice Strictly Finals", "Strictly"),
        ("Masters Choice final", "Strictly"),
        # Variants kept apart from the plain formats
        ("Switch Jack&Jill", "Switch Jack & Jill"),
        ("Switchly", "Switch Strictly"),
        ("Rising Star Routines", "Rising Star"),
        ("Classic Routine", "Classic"),
        ("Showcase", "Showcase"),
        ("ProAm Novice Leader", "Pro-Am Unknown (Leader)"),
        ("Pro/Am Novice+", "Pro-Am Unknown"),
        ("Unknown thing", None),
    ],
)
def test_normalise_format(name, fmt):
    assert ex.normalise_format(name) == fmt


@pytest.mark.parametrize(
    "name",
    ["KemZouk Festival 2026", "ZvukiZouka", "Tequila Blues Weekend 2026", "Volga Flow Festival"],
)
def test_extract_excludes_the_same_events_as_download(name):
    # extract.py keeps its own copy of the non-WCS patterns; they must agree with download.py.
    import download as dl

    assert ex.NON_WCS_STYLE_RE.search(name)
    assert ex.NON_WCS_STYLE_RE.pattern == dl.NON_WCS_STYLE_RE.pattern
    assert ex.NON_WCS_DIVISION_RE.pattern == dl.NON_WCS_DIVISION_RE.pattern


def test_blues_division_is_excluded_but_blues_event_name_is_not():
    assert ex.NON_WCS_DIVISION_RE.search("Blues JnJ newcomer")
    assert not ex.NON_WCS_STYLE_RE.search("Cash&Blues")
