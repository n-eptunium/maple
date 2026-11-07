"""Polite HLTV page fetcher: disk cache, robots.txt, a strict rate limit, two methods.

HLTV's terms restrict automated parsing. This module is built for one person making a few
requests a day: every page is cached for 24 h, live requests are at least 5 s apart and capped
at 30 per hour, and every live request is logged at INFO (and appended to `fetch.log`).

Layout inside `cache/hltv/`:
  <sha1(url)>.html / .meta.json   cached page + {fetched_at, status, method, url}
  robots.txt / robots.meta.json   robots.txt, refreshed once a day
  .last                           unix time of the last live request
  .requests                       unix times of live requests in the last hour
  .method                         the method that last worked ("curl" or "playwright")
  cookies.json                    curl cookie jar
  profile/                        Playwright persistent Chromium profile
  profile/.cf-passed              marker: the user solved the challenge once, run headless
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.robotparser
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from curl_cffi import requests as cffi_requests

from cs2shorts.store.paths import hltv_cache_dir

log = logging.getLogger("cs2shorts.hltv")

Method = Literal["curl", "playwright"]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
ACCEPT_LANGUAGE = "en-US,en;q=0.9"
ROBOTS_URL = "https://www.hltv.org/robots.txt"
HLTV_HOSTS = {"hltv.org", "www.hltv.org"}

MIN_INTERVAL_S = 5.0
MAX_PER_HOUR = 30
ROBOTS_MAX_AGE_H = 24
CURL_TIMEOUT_S = 20
HEADED_CHALLENGE_TIMEOUT_S = 180
PAGE_TIMEOUT_MS = 45_000

CHALLENGE_MARKERS = ("Enable JavaScript and cookies to continue", "cf-chl")


class FetchError(Exception):
    """Base error. `hint` tells the user what to do next."""

    def __init__(self, message: str, hint: str = "", status: int | None = None) -> None:
        super().__init__(message)
        self.hint = hint
        self.status = status


class RateLimited(FetchError):
    pass


class Disallowed(FetchError):
    pass


class Challenged(FetchError):
    pass


# Indirection so tests can freeze time without sleeping.
_now: Callable[[], float] = time.time
_sleep: Callable[[float], None] = time.sleep


def _cache_dir() -> Path:
    return hltv_cache_dir()


def cache_key(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()


def cache_paths(url: str) -> tuple[Path, Path]:
    d = _cache_dir()
    k = cache_key(url)
    return d / f"{k}.html", d / f"{k}.meta.json"


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds")


def _parse_iso(s: str) -> float:
    return datetime.fromisoformat(s).timestamp()


def _read_json(p: Path) -> dict:
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def is_challenge(status: int, body: str) -> bool:
    return status in (403, 503) or any(m in body for m in CHALLENGE_MARKERS)


def _is_hltv(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in HLTV_HOSTS


# --- cache --------------------------------------------------------------------


def read_cache(url: str, max_age_h: float) -> str | None:
    html_p, meta_p = cache_paths(url)
    if max_age_h <= 0 or not html_p.is_file():
        return None
    meta = _read_json(meta_p)
    try:
        age_s = _now() - _parse_iso(meta["fetched_at"])
    except (KeyError, TypeError, ValueError):
        return None
    if age_s > max_age_h * 3600:
        return None
    log.info("hltv cache hit (%.1f h old): %s", age_s / 3600, url)
    return html_p.read_text(encoding="utf-8")


def _write_cache(url: str, html: str, status: int, method: Method) -> None:
    html_p, meta_p = cache_paths(url)
    html_p.write_text(html, encoding="utf-8")
    meta = {"url": url, "fetched_at": _iso(_now()), "status": status, "method": method}
    meta_p.write_text(json.dumps(meta, indent=2) + "\n")


# --- rate limit -----------------------------------------------------------------


def _reserve_live_request(url: str) -> None:
    """Block until 5 s since the last live request; raise if the hourly cap is reached."""
    d = _cache_dir()
    req_p = d / ".requests"
    last_p = d / ".last"
    now = _now()
    try:
        recent = [float(x) for x in req_p.read_text().split()]
    except (OSError, ValueError):
        recent = []
    recent = [t for t in recent if now - t < 3600]
    if len(recent) >= MAX_PER_HOUR:
        wait_min = int((3600 - (now - min(recent))) // 60) + 1
        raise RateLimited(
            f"{len(recent)} live HLTV requests in the last hour (limit {MAX_PER_HOUR})",
            hint=f"Wait about {wait_min} min, or use the cached pages.",
            status=429,
        )
    try:
        last = float(last_p.read_text().strip())
    except (OSError, ValueError):
        last = 0.0
    wait = MIN_INTERVAL_S - (now - last)
    if wait > 0:
        log.debug("hltv rate limit: sleeping %.1f s", wait)
        _sleep(wait)
        now = _now()
    recent.append(now)
    last_p.write_text(f"{now}\n")
    req_p.write_text("".join(f"{t}\n" for t in recent))


def _log_live(url: str, method: Method, status: int) -> None:
    log.info("hltv LIVE fetch method=%s status=%s %s", method, status, url)
    with (_cache_dir() / "fetch.log").open("a") as f:
        f.write(f"{_iso(_now())}\t{method}\t{status}\t{url}\n")


# --- method 1: curl_cffi ----------------------------------------------------------


def _cookie_path() -> Path:
    return _cache_dir() / "cookies.json"


def _curl_get(url: str) -> tuple[int, str]:
    jar_p = _cookie_path()
    cookies: dict[str, str] = {
        str(k): str(v) for k, v in _read_json(jar_p).items() if isinstance(v, str)
    }
    r = cffi_requests.get(
        url,
        impersonate="chrome",
        timeout=CURL_TIMEOUT_S,
        headers={"User-Agent": USER_AGENT, "Accept-Language": ACCEPT_LANGUAGE},
        cookies=cookies,
    )
    try:
        cookies.update({str(k): str(v) for k, v in dict(r.cookies).items()})
        jar_p.write_text(json.dumps(cookies, indent=2, sort_keys=True) + "\n")
    except Exception:  # a broken jar must never break a fetch
        log.debug("could not persist cookies", exc_info=True)
    return int(r.status_code), r.text


# --- method 2: Playwright -----------------------------------------------------------


def profile_dir() -> Path:
    p = _cache_dir() / "profile"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _passed_marker() -> Path:
    return profile_dir() / ".cf-passed"


def _run_browser(url: str, *, headless: bool, raw: bool) -> tuple[int, str]:
    """Open `url` in persistent Chromium. Headed runs wait for the user to pass Cloudflare."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(profile_dir()),
            headless=headless,
            user_agent=USER_AGENT,
            locale="en-US",
            extra_http_headers={"Accept-Language": ACCEPT_LANGUAGE},
            viewport={"width": 1280, "height": 900},
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            resp = page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            status = resp.status if resp else 0
            if not headless:
                log.warning("hltv: complete the Cloudflare check in the browser window")
                deadline = _now() + HEADED_CHALLENGE_TIMEOUT_S
                while is_challenge(0, page.content()) and _now() < deadline:
                    page.wait_for_timeout(1000)
                status = 200 if not is_challenge(0, page.content()) else status
            try:
                page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT_MS)
            except Exception:  # ads/trackers can keep the network busy; content is there
                log.debug("networkidle timed out for %s", url)
            if raw and resp is not None and not is_challenge(0, page.content()):
                body = page.inner_text("body")  # robots.txt arrives wrapped in <pre>
            else:
                body = page.content()
            if is_challenge(0, body):
                status = 403
            elif status in (403, 503):
                status = 200  # the challenge resolved after the first response
            return status, body
        finally:
            ctx.close()


def _playwright_get(url: str, *, raw: bool = False) -> tuple[int, str]:
    marker = _passed_marker()
    headless = marker.exists()
    if not headless:
        log.warning("hltv: opening a Chromium window once so you can pass Cloudflare")
    status, body = _run_browser(url, headless=headless, raw=raw)
    if is_challenge(status, body):
        marker.unlink(missing_ok=True)  # next run opens a window again
        raise Challenged(
            f"Cloudflare still challenges {url} in Playwright",
            hint="Run the command again; a browser window opens so you can pass the check.",
            status=409,
        )
    if not headless:
        marker.write_text(_iso(_now()) + "\n")
    return status, body


# --- live fetch -------------------------------------------------------------------------


def preferred_method() -> Method:
    p = _cache_dir() / ".method"
    m = p.read_text().strip() if p.is_file() else ""
    return "playwright" if m == "playwright" else "curl"


def _set_preferred(method: Method) -> None:
    (_cache_dir() / ".method").write_text(method + "\n")


def _live_get(url: str, *, raw: bool = False) -> tuple[int, str, Method]:
    """At most two live requests: the preferred method, then Playwright if challenged."""
    first = preferred_method()
    if first == "curl":
        _reserve_live_request(url)
        try:
            status, body = _curl_get(url)
        except Exception as e:
            raise FetchError(
                f"request failed: {e.__class__.__name__}: {e}",
                hint="Check your network connection.",
            ) from e
        _log_live(url, "curl", status)
        if not is_challenge(status, body):
            return status, body, "curl"
        log.info("hltv: Cloudflare challenge on curl, falling back to Playwright")
    _reserve_live_request(url)
    status, body = _playwright_get(url, raw=raw)
    _log_live(url, "playwright", status)
    return status, body, "playwright"


# --- robots.txt ---------------------------------------------------------------------------


def _robots() -> urllib.robotparser.RobotFileParser:
    d = _cache_dir()
    txt_p, meta_p = d / "robots.txt", d / "robots.meta.json"
    meta = _read_json(meta_p)
    fresh = False
    try:
        fresh = _now() - _parse_iso(meta["fetched_at"]) < ROBOTS_MAX_AGE_H * 3600
    except (KeyError, TypeError, ValueError):
        pass
    if not (fresh and txt_p.is_file()):
        status, body, method = _live_get(ROBOTS_URL, raw=True)
        txt_p.write_text(body if status < 400 else "", encoding="utf-8")
        meta = {"fetched_at": _iso(_now()), "status": status, "method": method}
        meta_p.write_text(json.dumps(meta, indent=2) + "\n")
    rp = urllib.robotparser.RobotFileParser(ROBOTS_URL)
    status = int(meta.get("status", 200))
    if status in (401, 403):
        rp.disallow_all = True  # type: ignore[attr-defined]
    elif status >= 400:
        rp.allow_all = True  # type: ignore[attr-defined]
    else:
        rp.parse(txt_p.read_text(encoding="utf-8").splitlines())
    return rp


def check_robots(url: str) -> None:
    if not _robots().can_fetch(USER_AGENT, url):
        raise Disallowed(
            f"robots.txt disallows {urlparse(url).path}",
            hint="HLTV does not allow this path for crawlers; open it in your browser instead.",
            status=403,
        )


# --- public -------------------------------------------------------------------------------


def fetch_html(url: str, *, max_age_h: float = 24) -> str:
    """Return the page HTML, from the disk cache if younger than `max_age_h` hours."""
    cached = read_cache(url, max_age_h)
    if cached is not None:
        return cached
    if not _is_hltv(url):
        raise ValueError(f"not an hltv.org URL: {url}")
    check_robots(url)
    status, body, method = _live_get(url)
    if status >= 400:
        raise FetchError(
            f"HLTV answered {status} for {url}",
            hint="Check the URL in your browser." if status == 404 else "Try again later.",
            status=status,
        )
    _write_cache(url, body, status, method)
    _set_preferred(method)
    return body
