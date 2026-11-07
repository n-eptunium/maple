"""Core data models. Times are integer milliseconds.

Source-media times (trim, speed, captions, reframe keys) are in source time.
`Effect.at_ms` and `Music.hit_ms` are in output time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class MediaInfo(BaseModel):
    path: str
    duration_ms: int
    width: int
    height: int
    fps: float
    has_audio: bool
    sample_rate: int


# --- captions ---------------------------------------------------------------


class Word(BaseModel):
    text: str
    start_ms: int
    end_ms: int
    conf: float = 1.0
    is_name: bool = False
    emphasis: bool = False


class Caption(BaseModel):
    id: str
    start_ms: int
    end_ms: int
    words: list[Word]
    text_override: str | None = None


class CaptionBox(BaseModel):
    x: float = 0.5
    y: float = 0.72
    w: float = 0.8


class CaptionTrack(BaseModel):
    source: Literal["asr", "manual", "hltv"] = "manual"
    style_id: str = "classic"
    box: CaptionBox = Field(default_factory=CaptionBox)
    items: list[Caption] = Field(default_factory=list)


class Glow(BaseModel):
    color: str = "#000000"
    outline_px: int = 8
    blur_px: int = 12


class Shadow(BaseModel):
    dx: int = 0
    dy: int = 0


class AnimIn(BaseModel):
    type: str = "pop"
    from_scale: float = 0.95
    duration_ms: int = 67
    ease: float = 0.6


class AnimOut(BaseModel):
    type: str = "none"


class CaptionStyle(BaseModel):
    id: str
    name: str
    font_family: str = "Dosis"
    font_file: str = "Dosis-Bold.ttf"
    font_px: int = 116
    letter_spacing_px: int = 2
    lowercase: bool = True
    keep_names: bool = False
    fill: str = "#FFFFFF"
    glow: Glow = Field(default_factory=Glow)
    shadow: Shadow = Field(default_factory=Shadow)
    max_words: int = 4
    max_lines: int = 2
    max_chars_per_line: int = 16
    anim_in: AnimIn = Field(default_factory=AnimIn)
    anim_out: AnimOut = Field(default_factory=AnimOut)
    emphasis_fill: str = "#FF2A2A"
    hold_gap_ms: int = 600
    tail_ms: int = 300
    min_duration_ms: int = 400


# --- HLTV -------------------------------------------------------------------


class Highlight(BaseModel):
    id: str
    title: str
    embed_url: str
    source: Literal["twitch", "youtube", "other"]
    player: str | None
    team: str | None
    map: str | None
    round: int | None
    action: str | None


class Team(BaseModel):
    name: str
    hltv_id: int | None


class MapScore(BaseModel):
    name: str
    score_a: int | None
    score_b: int | None


class Match(BaseModel):
    hltv_id: int
    url: str
    event: str
    date: str
    teams: list[Team]
    maps: list[MapScore]
    highlights: list[Highlight]


# --- music ------------------------------------------------------------------


class Licence(BaseModel):
    type: str
    source_url: str | None
    proof: str | None
    platforms: list[str]
    attribution: str | None
    verified: str | None


class Track(BaseModel):
    id: str
    path: str
    title: str
    artist: str | None
    duration_ms: int
    bpm: float
    beats_ms: list[int]
    drop_ms: int
    drop_candidates_ms: list[int]
    licence: Licence
    analyzed_at: str


# --- edit -------------------------------------------------------------------


class SpeedSegment(BaseModel):
    src_start_ms: int
    src_end_ms: int
    rate: float


class ReframeKey(BaseModel):
    t_ms: int
    cx: float


class Effect(BaseModel):
    type: Literal["zoom_punch", "shake", "flash", "slowmo"]
    at_ms: int
    params: dict[str, Any]


class Trim(BaseModel):
    in_ms: int
    out_ms: int


class Reframe(BaseModel):
    mode: Literal["center", "keys", "auto"] = "center"
    keys: list[ReframeKey] = Field(default_factory=list)
    zoom: float = 1.0


class Music(BaseModel):
    track_id: str
    hit_ms: int
    offset_ms: int
    gain_db: float = -6
    caster_gain_db: float = 0
    duck_db: float = 0


class YouTubePost(BaseModel):
    privacy: str = "private"
    video_id: str | None = None
    status: str | None = None


class TikTokPost(BaseModel):
    mode: str = "inbox_draft"
    publish_id: str | None = None
    status: str | None = None


class Post(BaseModel):
    title: str = ""
    description: str = ""
    hashtags: list[str] = Field(default_factory=list)
    youtube: YouTubePost = Field(default_factory=YouTubePost)
    tiktok: TikTokPost = Field(default_factory=TikTokPost)


class RenderRecord(BaseModel):
    path: str
    created: str
    duration_ms: int
    size_bytes: int
    sha256: str


class Project(BaseModel):
    id: str
    name: str
    created: str
    match: Match | None
    highlight_id: str | None
    source: MediaInfo | None
    trim: Trim
    reframe: Reframe
    speed: list[SpeedSegment] = Field(default_factory=list)
    music: Music | None
    effects: list[Effect] = Field(default_factory=list)
    captions: CaptionTrack
    post: Post
    renders: list[RenderRecord] = Field(default_factory=list)


# --- schema export ----------------------------------------------------------

EXPORTED_MODELS: dict[str, type[BaseModel]] = {
    "MediaInfo": MediaInfo,
    "Word": Word,
    "Caption": Caption,
    "CaptionTrack": CaptionTrack,
    "CaptionStyle": CaptionStyle,
    "Highlight": Highlight,
    "Match": Match,
    "Track": Track,
    "SpeedSegment": SpeedSegment,
    "ReframeKey": ReframeKey,
    "Effect": Effect,
    "Project": Project,
}


def schema_texts() -> dict[str, str]:
    """File name -> JSON text for every exported model (deterministic)."""
    return {
        f"{name}.json": json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        for name, model in EXPORTED_MODELS.items()
    }


def export_schemas(out_dir: Path | None = None) -> list[Path]:
    from cs2shorts.store.paths import schemas_dir

    out = out_dir or schemas_dir()
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for fname, text in schema_texts().items():
        p = out / fname
        p.write_text(text)
        written.append(p)
    return written


if __name__ == "__main__":
    for p in export_schemas():
        print(p)
