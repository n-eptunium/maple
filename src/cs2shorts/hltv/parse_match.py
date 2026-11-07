"""Parse an HLTV match page into a `Match`. Every selector failure becomes a warning."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from cs2shorts.store.models import Highlight, MapScore, Match, Roster, RosterPlayer, Team

# All selectors in one place: when HLTV changes its markup, fix them here.
SEL: dict[str, str] = {
    "event": ".timeAndEvent .event a",
    "date": ".timeAndEvent .date",
    "date_attr": "data-unix",
    "team1": ".team1-gradient .teamName",
    "team2": ".team2-gradient .teamName",
    "team1_link": ".team1-gradient a[href*='/team/']",
    "team2_link": ".team2-gradient a[href*='/team/']",
    "map": ".mapholder",
    "map_name": ".mapname",
    "map_score": ".results-team-score",
    "highlight": ".highlight",
    "highlight_attr": "data-highlight-embed",
    "lineup_team": ".box-headline a[href*='/team/'], .box-headline .text-ellipsis",
    "player": "div.players .flagAlign[data-player-id]",
    "player_attr": "data-player-id",
}

TEAM_ID_RE = re.compile(r"/team/(\d+)(?:/|$)")
MATCH_ID_RE = re.compile(r"/matches/(\d+)(?:/|$)")


def text_of(el: Tag | None) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el is not None else ""


def make_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _attempt[T](warnings: list[str], what: str, fn: Callable[[], T], default: T) -> T:
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{what}: {e.__class__.__name__}: {e}")
        return default


def match_id_from_url(url: str) -> int | None:
    m = MATCH_ID_RE.search(urlparse(url).path)
    return int(m.group(1)) if m else None


def team_id_from_href(href: str | None) -> int | None:
    m = TEAM_ID_RE.search(href or "")
    return int(m.group(1)) if m else None


# --- embeds ---------------------------------------------------------------------------


def source_of(url: str) -> Literal["twitch", "youtube", "other"]:
    host = (urlparse(url).hostname or "").lower()
    if host == "twitch.tv" or host.endswith(".twitch.tv"):
        return "twitch"
    if host in ("youtu.be", "youtube.com", "youtube-nocookie.com") or host.endswith(
        (".youtube.com", ".youtube-nocookie.com")
    ):
        return "youtube"
    return "other"


def normalize_embed(url: str) -> str:
    """Absolute URL; Twitch clip embeds become plain clip URLs (`clips.twitch.tv/<slug>`)."""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if host == "clips.twitch.tv" and p.path.rstrip("/") == "/embed":
        slug = (parse_qs(p.query).get("clip") or [""])[0]
        if slug:
            return f"https://clips.twitch.tv/{slug}"
    if host == "clips.twitch.tv":
        return f"https://clips.twitch.tv{p.path.rstrip('/')}"
    return url


def highlight_id(embed_url: str) -> str:
    return hashlib.sha1(embed_url.encode()).hexdigest()[:12]


def make_highlight(title: str, raw_url: str) -> Highlight:
    url = normalize_embed(raw_url)
    return Highlight(
        id=highlight_id(url),
        title=title,
        embed_url=url,
        source=source_of(url),
        player=None,
        team=None,
        map=None,
        round=None,
        action=None,
    )


# --- sections -------------------------------------------------------------------------


def _event(soup: BeautifulSoup) -> str:
    el = soup.select_one(SEL["event"])
    name = text_of(el) or (str(el.get("title") or "") if el else "")
    if not name:
        raise LookupError(f"no element for {SEL['event']!r}")
    return name


def _date(soup: BeautifulSoup) -> str:
    el = soup.select_one(SEL["date"])
    if el is None:
        raise LookupError(f"no element for {SEL['date']!r}")
    raw = str(el.get(SEL["date_attr"]) or "")
    ts = float(raw)
    if ts > 1e11:  # HLTV uses milliseconds
        ts /= 1000
    return datetime.fromtimestamp(ts, UTC).date().isoformat()


def _team(soup: BeautifulSoup, n: int) -> Team:
    name = text_of(soup.select_one(SEL[f"team{n}"]))
    if not name:
        raise LookupError(f"no element for {SEL[f'team{n}']!r}")
    link = soup.select_one(SEL[f"team{n}_link"])
    return Team(name=name, hltv_id=team_id_from_href(str(link.get("href")) if link else None))


def _score(el: Tag | None) -> int | None:
    t = text_of(el)
    return int(t) if t.isdigit() else None


def _maps(soup: BeautifulSoup, warnings: list[str]) -> list[MapScore]:
    holders = soup.select(SEL["map"])
    if not holders:
        raise LookupError(f"no element for {SEL['map']!r}")
    out = []
    for i, h in enumerate(holders, 1):
        name = text_of(h.select_one(SEL["map_name"]))
        if not name:
            warnings.append(f"map {i}: no {SEL['map_name']!r}")
            continue
        scores = h.select(SEL["map_score"])
        a = _score(scores[0]) if len(scores) > 0 else None
        b = _score(scores[1]) if len(scores) > 1 else None
        out.append(MapScore(name=name, score_a=a, score_b=b))
    return out


def _rosters(soup: BeautifulSoup) -> list[Roster]:
    """One roster per `div.players` block (HLTV renders one per team, in team order)."""
    block_sel, player_sel = SEL["player"].split(" ", 1)
    rosters = []
    for block in soup.select(block_sel):
        lineup = block.find_parent(class_="lineup")
        team_el = lineup.select_one(SEL["lineup_team"]) if isinstance(lineup, Tag) else None
        seen: dict[str, RosterPlayer] = {}
        for p in block.select(player_sel):
            name = text_of(p)
            pid = str(p.get(SEL["player_attr"]) or "")
            if name and (pid or name.lower()) not in seen:
                seen[pid or name.lower()] = RosterPlayer(
                    name=name, hltv_id=int(pid) if pid.isdigit() else None
                )
        if seen:
            rosters.append(Roster(team=text_of(team_el) or None, players=list(seen.values())))
    if not rosters:
        raise LookupError(f"no element for {SEL['player']!r}")
    return rosters


def _highlights(soup: BeautifulSoup, base_url: str, warnings: list[str]) -> list[Highlight]:
    out: dict[str, Highlight] = {}
    els = soup.select(SEL["highlight"])
    for i, el in enumerate(els, 1):
        raw = str(el.get(SEL["highlight_attr"]) or "")
        if not raw:
            warnings.append(f"highlight {i}: no {SEL['highlight_attr']} attribute")
            continue
        h = make_highlight(text_of(el), urljoin(base_url, raw) if raw.startswith("/") else raw)
        out.setdefault(h.id, h)
    return list(out.values())


def _align_rosters(rosters: list[Roster], teams: list[Team]) -> list[Roster]:
    """Give rosters without a team name the team in the same position."""
    for i, r in enumerate(rosters):
        if r.team is None and i < len(teams):
            r.team = teams[i].name
    return rosters


# --- public ---------------------------------------------------------------------------


def parse_match(html: str, url: str) -> Match:
    from cs2shorts.hltv.title_parse import parse_title

    warnings: list[str] = []
    soup = make_soup(html or "")
    hid = match_id_from_url(url)
    if hid is None:
        warnings.append(f"no match id in URL {url}")
    event = _attempt(warnings, "event", lambda: _event(soup), "")
    date = _attempt(warnings, "date", lambda: _date(soup), "")
    teams = [
        t
        for t in (
            _attempt(warnings, "team1", lambda: _team(soup, 1), None),
            _attempt(warnings, "team2", lambda: _team(soup, 2), None),
        )
        if t is not None
    ]
    maps: list[MapScore] = _attempt(warnings, "maps", lambda: _maps(soup, warnings), [])
    rosters: list[Roster] = _attempt(warnings, "rosters", lambda: _rosters(soup), [])
    rosters = _align_rosters(rosters, teams)
    highlights: list[Highlight] = _attempt(
        warnings, "highlights", lambda: _highlights(soup, url, warnings), []
    )
    if not highlights:
        warnings.append(f"no highlights ({SEL['highlight']!r})")

    match = Match(
        hltv_id=hid or 0,
        url=url,
        event=event,
        date=date,
        teams=teams,
        maps=maps,
        highlights=highlights,
        rosters=rosters,
        warnings=warnings,
    )
    for h in match.highlights:
        for k, v in parse_title(h.title, match).items():
            setattr(h, k, v)
    return match
