"""Unit tests for the judge key in ``scripts/parsers/danceconvention.py`` (no files, no network)."""

import pytest

from parsers.danceconvention import DanceConventionParser


@pytest.fixture
def parser():
    return DanceConventionParser()


def test_judge_key_plain_names(parser):
    text = "J3 Zoe Klomp\nMPV Mia Primavera\nMKS Mackenzie Sharp"
    assert parser._extract_judge_key(text) == {
        "J3": "Zoe Klomp",
        "MPV": "Mia Primavera",
        "MKS": "Mackenzie Sharp",
    }


@pytest.mark.parametrize(
    "line, initials, name",
    [
        ("SCJ Shanon Coxall-Jones", "SCJ", "Shanon Coxall-Jones"),  # hyphen (Swingvasion III)
        ("OB Sean O'Brien", "OB", "Sean O'Brien"),
        ("OB Sean O’Brien", "OB", "Sean O’Brien"),
        ("КП Павел Катунин", "КП", "Павел Катунин"),
        ('RS Raine "rake" Salo', "RS", 'Raine "rake" Salo'),  # quoted nickname (Riga Summer Swing)
        ("ASIA Singapore/Malaysia Pod", "ASIA", "Singapore/Malaysia Pod"),  # pod label (After Party)
    ],
)
def test_judge_key_punctuation_and_other_scripts(parser, line, initials, name):
    assert parser._extract_judge_key(line) == {initials: name}


def test_judge_key_ignores_non_name_lines(parser):
    text = (
        "Score legend: placement from 1 to 12\nNovice Jack & Jill - Finals\n166 Lewis Poulsen 6 1\n"
        "# Name J3 MPV 1-1 1-2 Result Remarks\nTop 5 - Finals"
    )
    assert parser._extract_judge_key(text) == {}
