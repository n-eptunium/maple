from pathlib import Path

import pytest

from cs2shorts.hltv.parse_match import normalize_embed, parse_match, source_of
from cs2shorts.hltv.parse_news import parse_news

FIX = Path(__file__).parent / "fixtures" / "hltv"
SYN = FIX / "synthetic"
MATCH_URL = "https://www.hltv.org/matches/2400008/the-mongolz-vs-natus-vincere-iem-beijing-2026"


# --- synthetic pages (always run) -------------------------------------------------------


@pytest.fixture
def syn_match():
    return parse_match((SYN / "match.html").read_text(), MATCH_URL)


def test_synthetic_match_header(syn_match):
    m = syn_match
    assert m.hltv_id == 2400008
    assert m.event == "Synthetic Cup 2026"
    assert m.date == "2025-11-02"
    assert [(t.name, t.hltv_id) for t in m.teams] == [
        ("The MongolZ", 6248),
        ("Natus Vincere", 4608),
    ]
    assert [(x.name, x.score_a, x.score_b) for x in m.maps] == [
        ("Mirage", 13, 9),
        ("Inferno", 11, 13),
        ("Ancient", None, None),
    ]


def test_synthetic_match_rosters(syn_match):
    assert [r.team for r in syn_match.rosters] == ["The MongolZ", "Natus Vincere"]
    assert [p.name for p in syn_match.rosters[0].players] == [
        "bLitz",
        "Techno4K",
        "910",
        "mzinho",
        "Senzu",
    ]
    assert syn_match.rosters[1].players[0].hltv_id == 19230


def test_synthetic_match_highlights(syn_match):
    hs = syn_match.highlights
    assert len(hs) == 3  # the smartphone duplicate collapses into the first
    assert hs[0].embed_url == "https://clips.twitch.tv/SyntheticClipOne-abc123"
    assert hs[0].source == "twitch" and len(hs[0].id) == 12
    assert (hs[0].player, hs[0].team, hs[0].action, hs[0].map, hs[0].round) == (
        "mzinho",
        "The MongolZ",
        "1v3 clutch",
        "Mirage",
        12,
    )
    assert (hs[1].player, hs[1].team, hs[1].action, hs[1].map) == (
        "w0nderful",
        "Natus Vincere",
        "4 kills",
        "Inferno",
    )
    assert hs[2].source == "youtube" and hs[2].embed_url.startswith("https://www.youtube.com/")
    assert (hs[2].player, hs[2].action) == ("910", "awp ace")
    assert any("no data-highlight-embed" in w for w in syn_match.warnings)


def test_garbage_degrades_to_warnings():
    m = parse_match("<html><p>nothing here</p></html>", "https://www.hltv.org/news/1/x")
    assert m.hltv_id == 0 and m.event == "" and m.teams == [] and m.highlights == []
    assert len(m.warnings) >= 5
    assert parse_match("", MATCH_URL).hltv_id == 2400008


def test_synthetic_news_attaches_clips_to_linked_match():
    fetched = []

    def fetch(url):
        fetched.append(url)
        return (SYN / "match.html").read_text()

    m = parse_news((SYN / "news.html").read_text(), "https://www.hltv.org/news/1/x", fetch=fetch)
    assert fetched == [MATCH_URL]  # the article link, not the sidebar one
    assert m is not None and m.event == "Synthetic Cup 2026"
    urls = [h.embed_url for h in m.highlights]
    assert urls[:3] == [h.embed_url for h in parse_match(fetch(MATCH_URL), MATCH_URL).highlights]
    assert urls[3:] == [
        "https://clips.twitch.tv/SyntheticNewsClip-xyz789",
        "https://youtu.be/zyxwVUTsrqp",
    ]
    news_clip = m.highlights[3]
    assert news_clip.title == "Senzu - 4k to close out Mirage"
    assert (news_clip.player, news_clip.team, news_clip.action, news_clip.map) == (
        "Senzu",
        "The MongolZ",
        "4 kills to close out mirage",
        None,
    )


def test_news_without_anything_is_none():
    assert parse_news("<h1 class='headline'>x</h1>", "https://www.hltv.org/news/1/x") is None


@pytest.mark.parametrize(
    "raw,want",
    [
        (
            "https://clips.twitch.tv/embed?clip=Abc-Def_1&parent=www.hltv.org",
            "https://clips.twitch.tv/Abc-Def_1",
        ),
        ("//clips.twitch.tv/embed?clip=X&autoplay=true", "https://clips.twitch.tv/X"),
        ("https://clips.twitch.tv/Slug", "https://clips.twitch.tv/Slug"),
        ("https://www.youtube.com/embed/abc", "https://www.youtube.com/embed/abc"),
    ],
)
def test_normalize_embed(raw, want):
    assert normalize_embed(raw) == want


def test_source_of():
    assert source_of("https://www.twitch.tv/x/clip/y") == "twitch"
    assert source_of("https://youtu.be/x") == "youtube"
    assert source_of("https://streamable.com/x") == "other"


# --- real pages (run once saved; see fixtures/hltv/README.md) -----------------------------
# Expected values are written by hand from the saved page. None = not filled in yet.

REAL = {
    "match_mongolz_navi.html": {
        "url": MATCH_URL,
        "event": "IEM Beijing 2026",
        "teams": ["The MongolZ", "Natus Vincere"],
        "maps": None,  # number of .mapholder entries
        "highlights": None,  # number of highlights
        "titles": {},  # {index: (player, action, map, round)}
    },
    "match_second.html": {
        "url": None,
        "event": None,
        "teams": None,
        "maps": None,
        "highlights": None,
        "titles": {},
    },
}
NEWS_REAL = {"file": "news_clip.html", "url": None, "min_clips": 1}


def _real(name):
    p = FIX / name
    exp = REAL[name]
    if not p.is_file() or exp["url"] is None:
        pytest.skip(f"save {p} with --save-fixture, fill REAL[{name!r}] (fixtures/hltv/README.md)")
    return parse_match(p.read_text(encoding="utf-8"), exp["url"]), exp


@pytest.mark.parametrize("name", list(REAL))
def test_real_match(name):
    m, exp = _real(name)
    checked = 0
    for key, actual in (
        ("event", m.event),
        ("teams", [t.name for t in m.teams]),
        ("maps", len(m.maps)),
        ("highlights", len(m.highlights)),
    ):
        if exp[key] is not None:
            assert actual == exp[key], key
            checked += 1
    for i, want in exp["titles"].items():
        h = m.highlights[i]
        assert (h.player, h.action, h.map, h.round) == want, h.title
    assert all(h.embed_url.startswith("https://") for h in m.highlights)
    assert all("embed?" not in h.embed_url for h in m.highlights if h.source == "twitch")
    if exp["maps"] is None or exp["highlights"] is None:
        pytest.skip(
            f"{name}: parsed {len(m.maps)} maps, {len(m.highlights)} highlights; "
            "write the expected counts into REAL"
        )


def test_real_news():
    p = FIX / NEWS_REAL["file"]
    if not p.is_file() or NEWS_REAL["url"] is None:
        pytest.skip(f"save {p} with --save-fixture and set NEWS_REAL['url']")
    m = parse_news(p.read_text(encoding="utf-8"), NEWS_REAL["url"], fetch=lambda u: "")
    assert m is not None
    assert sum(h.source == "twitch" for h in m.highlights) >= NEWS_REAL["min_clips"]
