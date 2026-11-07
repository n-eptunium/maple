"""Parse an HLTV news post: its embedded clips, headline and first linked match."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from cs2shorts.hltv.parse_match import make_highlight, make_soup, parse_match, text_of
from cs2shorts.hltv.title_parse import parse_title
from cs2shorts.store.models import Highlight, Match

log = logging.getLogger("cs2shorts.hltv")

SEL: dict[str, str] = {
    "headline": "h1.headline, .article h1, h1",
    "body": ".newstext-con, .newsitem, article",
    "twitch": "iframe[src*='clips.twitch.tv'], a[href*='clips.twitch.tv']",
    "youtube": (
        "iframe[src*='youtube.com/embed'], iframe[src*='youtube-nocookie.com/embed'], "
        "a[href*='youtube.com/watch'], a[href*='youtu.be/']"
    ),
    "match_link": "a[href^='/matches/'], a[href^='https://www.hltv.org/matches/']",
}

MATCH_PATH_RE = re.compile(r"^/matches/\d+/")


def _clips(scope: Tag | BeautifulSoup, headline: str, base: str) -> list[Highlight]:
    out: dict[str, Highlight] = {}
    for el in scope.select(f"{SEL['twitch']}, {SEL['youtube']}"):
        raw = str(el.get("src") or el.get("href") or "")
        if not raw:
            continue
        h = make_highlight(headline, urljoin(base, raw))
        if h.source == "other":
            continue
        out.setdefault(h.id, h)
    return list(out.values())


def _first_match_url(soup: BeautifulSoup, body: Tag | None, base: str) -> str | None:
    # The article body first: the sidebar lists unrelated live matches.
    for scope in (body, soup):
        if scope is None:
            continue
        for a in scope.select(SEL["match_link"]):
            url = urljoin(base, str(a.get("href") or ""))
            if MATCH_PATH_RE.match(urlparse(url).path):
                return url.split("#")[0]
    return None


def parse_news(html: str, url: str, *, fetch: Callable[[str], str] | None = None) -> Match | None:
    """Clips from the post, attached to its first linked match (fetched with `fetch`).

    Without a match link, returns a Match with `hltv_id=0` holding just the clips.
    Returns None if the post has neither clips nor a match link.
    """
    soup = make_soup(html or "")
    warnings: list[str] = []
    headline = text_of(soup.select_one(SEL["headline"]))
    if not headline:
        warnings.append(f"news: no headline ({SEL['headline']!r})")
    body = soup.select_one(SEL["body"])
    if body is None:
        warnings.append(f"news: no article body ({SEL['body']!r}), searched the whole page")
    clips = _clips(body or soup, headline, url)
    match_url = _first_match_url(soup, body, url)

    if match_url is None:
        if not clips:
            return None
        match = Match(
            hltv_id=0,
            url=url,
            event="",
            date="",
            teams=[],
            maps=[],
            highlights=[],
            warnings=[*warnings, "news: no linked match"],
        )
    else:
        if fetch is None:
            from cs2shorts.hltv.fetch import fetch_html

            fetch = fetch_html
        match = parse_match(fetch(match_url), match_url)
        match.warnings.extend(warnings)

    known = {h.id for h in match.highlights}
    for h in clips:
        if h.id in known:
            continue
        for k, v in parse_title(h.title, match).items():
            setattr(h, k, v)
        match.highlights.append(h)
    log.debug("news %s: %d clips, match=%s", url, len(clips), match_url)
    return match
