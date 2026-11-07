"""HLTV match and news pages -> `Match`. Built to stay tiny: cached, rate-limited, logged."""

from cs2shorts.hltv.fetch import Challenged, Disallowed, FetchError, RateLimited, fetch_html
from cs2shorts.hltv.parse_match import parse_match
from cs2shorts.hltv.parse_news import parse_news
from cs2shorts.hltv.resolve import resolve
from cs2shorts.hltv.title_parse import parse_title

__all__ = [
    "Challenged",
    "Disallowed",
    "FetchError",
    "RateLimited",
    "fetch_html",
    "parse_match",
    "parse_news",
    "parse_title",
    "resolve",
]
