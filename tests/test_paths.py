import pytest

from cs2shorts.store import paths


def test_paths_created_under_data_dir(tmp_path, monkeypatch):
    root = tmp_path / "custom"
    monkeypatch.setenv("CS2_DATA_DIR", str(root))
    made = [
        paths.hltv_cache_dir(),
        paths.tracks_cache_dir(),
        paths.sources_dir(),
        paths.project_dir("abc-123"),
        paths.renders_dir(),
    ]
    rel = [p.relative_to(root).as_posix() for p in made]
    assert rel == ["cache/hltv", "cache/tracks", "sources", "projects/abc-123", "renders"]
    assert all(p.is_dir() for p in made)


def test_project_id_cannot_escape():
    with pytest.raises(ValueError):
        paths.project_dir("../evil")
