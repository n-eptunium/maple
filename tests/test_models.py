import pytest
from pydantic import BaseModel

from cs2shorts.store import models as m
from cs2shorts.store.paths import schemas_dir

WORD = m.Word(text="ZywOo", start_ms=100, end_ms=400, is_name=True)
CAPTION = m.Caption(id="c1", start_ms=100, end_ms=900, words=[WORD])
HIGHLIGHT = m.Highlight(
    id="h1",
    title="ace",
    embed_url="https://clips.twitch.tv/embed?clip=x",
    source="twitch",
    player="ZywOo",
    team="Vitality",
    map="Mirage",
    round=12,
    action="ace",
)
MATCH = m.Match(
    hltv_id=2370000,
    url="https://www.hltv.org/matches/2370000/x",
    event="Major",
    date="2026-06-01",
    teams=[m.Team(name="Vitality", hltv_id=9565), m.Team(name="X", hltv_id=None)],
    maps=[m.MapScore(name="Mirage", score_a=13, score_b=9)],
    highlights=[HIGHLIGHT],
)
MEDIA = m.MediaInfo(
    path="/x.mp4",
    duration_ms=30000,
    width=1920,
    height=1080,
    fps=60.0,
    has_audio=True,
    sample_rate=48000,
)
TRACK = m.Track(
    id="t1",
    path="/p.mp3",
    title="drift",
    artist=None,
    duration_ms=120000,
    bpm=140.0,
    beats_ms=[0, 428],
    drop_ms=30000,
    drop_candidates_ms=[30000, 60000],
    licence=m.Licence(
        type="cc-by",
        source_url=None,
        proof=None,
        platforms=["youtube"],
        attribution="x",
        verified=None,
    ),
    analyzed_at="2026-11-07T00:00:00Z",
)
PROJECT = m.Project(
    id="p1",
    name="ace",
    created="2026-11-07T00:00:00Z",
    match=MATCH,
    highlight_id="h1",
    source=MEDIA,
    trim=m.Trim(in_ms=0, out_ms=15000),
    reframe=m.Reframe(mode="keys", keys=[m.ReframeKey(t_ms=0, cx=0.4)], zoom=1.1),
    speed=[m.SpeedSegment(src_start_ms=1000, src_end_ms=2000, rate=0.5)],
    music=m.Music(track_id="t1", hit_ms=3000, offset_ms=0),
    effects=[m.Effect(type="zoom_punch", at_ms=3000, params={"scale": 1.2})],
    captions=m.CaptionTrack(source="asr", items=[CAPTION]),
    post=m.Post(title="ace", hashtags=["cs2"]),
    renders=[
        m.RenderRecord(
            path="/r.mp4", created="now", duration_ms=15000, size_bytes=1, sha256="0" * 64
        )
    ],
)

SAMPLES: list[BaseModel] = [
    MEDIA,
    WORD,
    CAPTION,
    m.CaptionTrack(),
    m.CaptionStyle(id="classic", name="Classic"),
    HIGHLIGHT,
    MATCH,
    TRACK,
    m.SpeedSegment(src_start_ms=0, src_end_ms=1, rate=2.0),
    m.ReframeKey(t_ms=0, cx=0.5),
    m.Effect(type="flash", at_ms=0, params={}),
    PROJECT,
    m.Project(
        id="p2",
        name="empty",
        created="now",
        match=None,
        highlight_id=None,
        source=None,
        trim=m.Trim(in_ms=0, out_ms=0),
        reframe=m.Reframe(),
        music=None,
        captions=m.CaptionTrack(),
        post=m.Post(),
    ),
]


def test_every_exported_model_has_a_sample():
    assert {type(s).__name__ for s in SAMPLES} == set(m.EXPORTED_MODELS)


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: type(s).__name__)
def test_json_round_trip(sample):
    again = type(sample).model_validate_json(sample.model_dump_json())
    assert again == sample


def test_caption_style_defaults():
    s = m.CaptionStyle(id="classic", name="Classic")
    assert (s.font_file, s.font_px, s.glow.outline_px, s.anim_in.duration_ms) == (
        "Dosis-Bold.ttf",
        116,
        8,
        67,
    )


def test_committed_schemas_match_models():
    committed = {p.name: p.read_text() for p in schemas_dir().glob("*.json")}
    assert committed == m.schema_texts(), "run: cs2shorts export-schemas"
