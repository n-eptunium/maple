"""Filesystem layout. Every function returns an existing directory."""

from __future__ import annotations

import re
from pathlib import Path

from cs2shorts.config import get_settings

REPO_ROOT = Path(__file__).resolve().parents[3]


def _mk(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_dir(base: Path | None = None) -> Path:
    return _mk(base if base is not None else get_settings().data_dir)


def hltv_cache_dir(base: Path | None = None) -> Path:
    return _mk(data_dir(base) / "cache" / "hltv")


def tracks_cache_dir(base: Path | None = None) -> Path:
    return _mk(data_dir(base) / "cache" / "tracks")


def sources_dir(base: Path | None = None) -> Path:
    return _mk(data_dir(base) / "sources")


_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def project_dir(project_id: str, base: Path | None = None) -> Path:
    if not _ID_RE.match(project_id):
        raise ValueError(f"invalid project id: {project_id!r}")
    return _mk(data_dir(base) / "projects" / project_id)


def renders_dir(base: Path | None = None) -> Path:
    return _mk(data_dir(base) / "renders")


# Repo-relative locations (not created).
def fonts_dir() -> Path:
    return REPO_ROOT / "assets" / "fonts"


def schemas_dir() -> Path:
    return REPO_ROOT / "schemas"


def web_dir() -> Path:
    return REPO_ROOT / "web"


def web_dist_dir() -> Path:
    return web_dir() / "dist"
