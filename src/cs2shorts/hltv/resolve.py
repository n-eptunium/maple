"""`resolve(url)`: an HLTV match or news URL -> Match."""

from __future__ import annotations

from functools import partial
from urllib.parse import urlparse

from cs2shorts.hltv.fetch import HLTV_HOSTS, fetch_html
from cs2shorts.hltv.parse_match import parse_match
from cs2shorts.hltv.parse_news import parse_news
from cs2shorts.store.models import Match


def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith(("hltv.org/", "www.hltv.org/")):
        url = "https://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or (p.hostname or "").lower() not in HLTV_HOSTS:
        raise ValueError(f"not an hltv.org URL: {url!r}")
    return f"https://www.hltv.org{p.path}"


def resolve(url: str, *, fresh: bool = False) -> Match:
    url = normalize_url(url)
    max_age_h = 0 if fresh else 24
    path = urlparse(url).path
    if path.startswith("/matches/"):
        return parse_match(fetch_html(url, max_age_h=max_age_h), url)
    if path.startswith("/news/"):
        fetch = partial(fetch_html, max_age_h=max_age_h)
        match = parse_news(fetch(url), url, fetch=fetch)
        if match is None:
            raise ValueError(f"no clips and no linked match in {url}")
        return match
    raise ValueError(f"unsupported HLTV URL (need /matches/ or /news/): {url}")
