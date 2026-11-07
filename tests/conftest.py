import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Keep tests away from the real ~/Movies/CS2Shorts and any local .env."""
    for k in ("CS2_FFMPEG", "CS2_FFMPEG_BIN", "CS2_FFPROBE_BIN", "CS2_DATA_DIR"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("CS2_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.chdir(tmp_path)
