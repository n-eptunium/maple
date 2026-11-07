from typer.testing import CliRunner

from cs2shorts.cli import app
from cs2shorts.config import get_settings
from cs2shorts.tools.doctor import check_ffmpeg, doctor


def test_missing_ffmpeg_fails(tmp_path, monkeypatch):
    missing = tmp_path / "nope" / "ffmpeg"
    monkeypatch.setenv("CS2_FFMPEG", str(missing))
    s = get_settings()
    assert s.ffmpeg_bin == str(missing)
    assert s.ffprobe_bin == str(missing.with_name("ffprobe"))

    c = check_ffmpeg(s)
    assert not c.ok and "brew install ffmpeg-full" in c.detail

    lines: list[str] = []
    assert doctor(lines.append) == 1
    assert any(line.startswith("FAIL") and "ffmpeg-full" in line for line in lines)


def test_cli_exit_code(tmp_path, monkeypatch):
    monkeypatch.setenv("CS2_FFMPEG", str(tmp_path / "missing"))
    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "ffmpeg-full" in result.output


FAKE_FFMPEG = """#!/bin/sh
case "$2" in
  -filters) echo " ... ass               V->V       Render ASS subtitles" ;;
  -encoders) echo " V....D h264_videotoolbox    VideoToolbox H.264 Encoder" ;;
esac
"""


def test_ffmpeg_capabilities(tmp_path, monkeypatch):
    fake = tmp_path / "ffmpeg"
    fake.write_text(FAKE_FFMPEG)
    fake.chmod(0o755)
    monkeypatch.setenv("CS2_FFMPEG", str(fake))
    assert check_ffmpeg(get_settings()).ok

    fake.write_text(FAKE_FFMPEG.replace("h264_videotoolbox", "libx264"))
    c = check_ffmpeg(get_settings())
    assert not c.ok and "h264_videotoolbox" in c.detail
