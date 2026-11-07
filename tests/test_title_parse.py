import pytest

from cs2shorts.hltv.title_parse import parse_title
from cs2shorts.store.models import Match, Roster, RosterPlayer

MATCH = Match(
    hltv_id=1,
    url="u",
    event="e",
    date="d",
    teams=[],
    maps=[],
    highlights=[],
    rosters=[
        Roster(team="Vitality", players=[RosterPlayer(name="ZywOo"), RosterPlayer(name="apEX")]),
        Roster(team="The MongolZ", players=[RosterPlayer(name="910"), RosterPlayer(name="bLitz")]),
    ],
)

CASES = [
    # title, (player, team, map, round, action)
    ("s1mple - 1v3 clutch (Mirage, round 12)", ("s1mple", None, "Mirage", 12, "1v3 clutch")),
    ("NiKo - 4 kills vs Vitality (Inferno)", ("NiKo", None, "Inferno", None, "4 kills")),
    ("ZywOo AWP ace", ("ZywOo", "Vitality", None, None, "awp ace")),
    ("zywoo - ninja defuse (Nuke, R. 24)", ("ZywOo", "Vitality", "Nuke", 24, "ninja defuse")),
    ("bLitz – 4k (Ancient, round 3)", ("bLitz", "The MongolZ", "Ancient", 3, "4 kills")),
    ("m0NESY - clutch 1vs2 on Dust 2", ("m0NESY", None, "Dust2", None, "1v2 clutch")),
    ("jL - quad kill (de_anubis, rd 7)", ("jL", None, "Anubis", 7, "4 kills")),
    ("apEX - 1v4 clutch (round 30, Overpass)", ("apEX", "Vitality", "Overpass", 30, "1v4 clutch")),
    ("910 ACE (Vertigo)", ("910", "The MongolZ", "Vertigo", None, "ace")),
    ("w0nderful - deagle 3k (Mirage)", ("w0nderful", None, "Mirage", None, "deagle 3 kills")),
    ("Random clip title", (None, None, None, None, "random clip title")),
    ("", (None, None, None, None, None)),
    ("((( - )", (None, None, None, None, None)),
]


@pytest.mark.parametrize("title,want", CASES, ids=[c[0] or "<empty>" for c in CASES])
def test_parse_title(title, want):
    got = parse_title(title, MATCH)
    assert (got["player"], got["team"], got["map"], got["round"], got["action"]) == want


def test_first_token_needs_a_roster():
    got = parse_title("ZywOo AWP ace", None)
    assert got["player"] is None and got["action"] == "zywoo awp ace"


def test_never_throws():
    for weird in (None, 123, "[", " - - - ", "x" * 10000):
        assert set(parse_title(weird, MATCH)) == {"player", "team", "map", "round", "action"}  # type: ignore[arg-type]
