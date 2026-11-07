"""Runtime settings, read from CS2_* environment variables (and .env)."""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CS2_", env_file=".env", extra="ignore")

    # CS2_FFMPEG is the documented override; CS2_FFMPEG_BIN also works.
    ffmpeg_bin: str = Field(
        default=DEFAULT_FFMPEG,
        validation_alias=AliasChoices("CS2_FFMPEG", "CS2_FFMPEG_BIN", "ffmpeg_bin"),
    )
    # Empty means "ffprobe next to ffmpeg_bin".
    ffprobe_bin: str = ""
    ytdlp_bin: str = "yt-dlp"
    data_dir: Path = Path("~/Movies/CS2Shorts")
    phonk_dir: Path = Path("~/Music/Phonk")
    port: int = 8765

    @field_validator("data_dir", "phonk_dir")
    @classmethod
    def _expand(cls, v: Path) -> Path:
        return Path(v).expanduser()

    @model_validator(mode="after")
    def _default_ffprobe(self) -> Settings:
        if not self.ffprobe_bin:
            self.ffprobe_bin = str(Path(self.ffmpeg_bin).with_name("ffprobe"))
        return self


def get_settings() -> Settings:
    """Fresh settings every call so env changes (and tests) are honoured."""
    return Settings()
