"""Pull player / team / map / round / action out of an HLTV highlight title. Never throws.

"s1mple - 1v3 clutch (Mirage, round 12)" -> s1mple, 1v3 clutch, Mirage, 12
"NiKo - 4 kills vs Vitality (Inferno)"   -> NiKo, 4 kills, Inferno
"ZywOo AWP ace"                          -> ZywOo (if on a roster), awp ace
"""

from __future__ import annotations

import re
from typing import Any

from cs2shorts.store.models import Match

MAPS: dict[str, str] = {
    "mirage": "Mirage",
    "inferno": "Inferno",
    "nuke": "Nuke",
    "ancient": "Ancient",
    "anubis": "Anubis",
    "dust2": "Dust2",
    "dust 2": "Dust2",
    "dust ii": "Dust2",
    "train": "Train",
    "overpass": "Overpass",
    "vertigo": "Vertigo",
    "cache": "Cache",
    "cobblestone": "Cobblestone",
}
_MAP_ALT = "|".join(sorted((re.escape(k) for k in MAPS), key=len, reverse=True))
MAP_RE = re.compile(rf"\b(?:de_)?({_MAP_ALT})\b", re.I)
ON_MAP_RE = re.compile(rf"\s+on\s+(?:de_)?({_MAP_ALT})\b", re.I)
ROUND_RE = re.compile(r"\b(?:round|rnd|rd|r)\.?\s*#?\s*(\d{1,2})\b", re.I)
PAREN_RE = re.compile(r"[(\[]([^()\[\]]*)[)\]]")
VS_RE = re.compile(r"\s+(?:vs\.?|versus|against)\s+.*$", re.I)

# Applied in order to the lowercased action.
ACTION_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bclutch\s+(\dv\d)\b"), r"\1 clutch"),
    (re.compile(r"\b(\dv\d)\b(?!\s+clutch)"), r"\1 clutch"),
    (re.compile(r"\b(?:5k|5 kills|five kills|penta(?:\s*kill)?)\b"), "ace"),
    (re.compile(r"\b(?:quad(?:ra)?\s*kill|four kills)\b"), "4 kills"),
    (re.compile(r"\b(?:triple\s*kill|three kills)\b"), "3 kills"),
    (re.compile(r"\b(\d)\s*(?:k|frags)\b"), r"\1 kills"),
]


def _empty() -> dict[str, Any]:
    return {"player": None, "team": None, "map": None, "round": None, "action": None}


def _roster_lookup(match: Match | None) -> dict[str, tuple[str, str | None]]:
    """lowercased player name -> (canonical name, team)."""
    out: dict[str, tuple[str, str | None]] = {}
    for r in getattr(match, "rosters", None) or []:
        for p in r.players:
            out.setdefault(p.name.lower(), (p.name, r.team))
    return out


def _canonical_map(s: str) -> str | None:
    m = MAP_RE.search(s)
    return MAPS[m.group(1).lower()] if m else None


def normalize_action(s: str) -> str | None:
    a = " ".join(s.lower().split())
    a = re.sub(r"\b(\d)\s*vs?\.?\s*(\d)\b", r"\1v\2", a)  # "1 vs 3" -> "1v3"
    a = VS_RE.sub("", a)
    for pat, rep in ACTION_RULES:
        a = pat.sub(rep, a)
    a = " ".join(re.sub(r"[()\[\]]", " ", a).split()).strip(" -–—:,.!")
    return a if any(c.isalnum() for c in a) else None


def _parse(title: str, match: Match | None) -> dict[str, Any]:
    out = _empty()
    t = " ".join(str(title or "").split())
    t = re.sub(r"\s+[–—]\s+", " - ", t)

    # Parenthesised bits carry the map and round.
    for group in PAREN_RE.findall(t):
        for part in group.split(","):
            if out["map"] is None and (mp := _canonical_map(part)):
                out["map"] = mp
            if out["round"] is None and (rm := ROUND_RE.search(part)):
                out["round"] = int(rm.group(1))
    rest = PAREN_RE.sub(" ", t)

    # "... on Mirage" / "... round 12" outside parentheses.
    if out["map"] is None and (om := ON_MAP_RE.search(rest)):
        out["map"] = MAPS[om.group(1).lower()]
        rest = ON_MAP_RE.sub(" ", rest, count=1)
    if out["round"] is None and (rm := ROUND_RE.search(rest)):
        out["round"] = int(rm.group(1))
        rest = rest[: rm.start()] + rest[rm.end() :]
    rest = " ".join(rest.split())

    roster = _roster_lookup(match)
    tail = rest
    if " - " in rest:
        head, _, tail = rest.partition(" - ")
        head = head.strip()
        if head:
            out["player"], out["team"] = roster.get(head.lower(), (head, None))
    elif rest:
        first, _, remainder = rest.partition(" ")
        if first.lower() in roster:
            out["player"], out["team"] = roster[first.lower()]
            tail = remainder
    out["action"] = normalize_action(tail)
    return out


def parse_title(title: str, match: Match | None = None) -> dict[str, Any]:
    try:
        return _parse(title, match)
    except Exception:
        return _empty()
