import json

import pytest

from cs2shorts.hltv import fetch as f

URL = "https://www.hltv.org/matches/2400008/the-mongolz-vs-natus-vincere-iem-beijing-2026"
URL2 = "https://www.hltv.org/matches/2400009/other"
PAGE = "<html><div class='teamName'>The MongolZ</div></html>"
CF_BODY = "<html><title>Just a moment...</title>Enable JavaScript and cookies to continue</html>"


class Resp:
    def __init__(self, status, text, cookies=None):
        self.status_code = status
        self.text = text
        self.cookies = cookies or {}


class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


@pytest.fixture
def clock(monkeypatch):
    c = Clock()
    monkeypatch.setattr(f, "_now", c.now)
    monkeypatch.setattr(f, "_sleep", c.sleep)
    return c


@pytest.fixture
def curl(monkeypatch):
    """Fake curl_cffi.requests.get: robots.txt allows all, pages return PAGE."""
    calls = []
    pages = {f.ROBOTS_URL: Resp(200, "User-agent: *\nDisallow: /search\n")}

    def get(url, **kw):
        calls.append((url, kw))
        return pages.get(url, Resp(200, PAGE, {"__cf_bm": "abc"}))

    monkeypatch.setattr(f.cffi_requests, "get", get)
    get.calls = calls
    get.pages = pages
    return get


@pytest.fixture
def browser(monkeypatch):
    calls = []
    result = {"body": PAGE}

    def run(url, *, headless, raw):
        calls.append((url, headless))
        return 200, result["body"]

    monkeypatch.setattr(f, "_run_browser", run)
    run.calls = calls
    run.result = result
    return run


def page_calls(curl):
    return [u for u, _ in curl.calls if u != f.ROBOTS_URL]


def test_cache_hit_makes_no_request(clock, monkeypatch):
    f._write_cache(URL, PAGE, 200, "curl")

    def boom(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(f.cffi_requests, "get", boom)
    monkeypatch.setattr(f, "_run_browser", boom)
    clock.t += 23 * 3600
    assert f.fetch_html(URL) == PAGE


def test_first_fetch_then_cached(clock, curl, caplog):
    caplog.set_level("INFO", logger="cs2shorts.hltv")
    assert f.fetch_html(URL) == PAGE
    url, kw = curl.calls[-1]
    assert url == URL and kw["impersonate"] == "chrome" and kw["timeout"] == 20
    assert kw["headers"]["User-Agent"] == f.USER_AGENT and "Accept-Language" in kw["headers"]
    assert "method=curl" in caplog.text

    meta = json.loads(f.cache_paths(URL)[1].read_text())
    assert meta["status"] == 200 and meta["method"] == "curl" and meta["fetched_at"]
    assert json.loads((f.hltv_cache_dir() / "cookies.json").read_text()) == {"__cf_bm": "abc"}

    n = len(curl.calls)
    clock.t += 3600
    assert f.fetch_html(URL) == PAGE
    assert len(curl.calls) == n
    assert (f.hltv_cache_dir() / "fetch.log").read_text().count("\tcurl\t") == 2  # robots + page


def test_expired_cache_refetches(clock, curl):
    f.fetch_html(URL)
    clock.t += 25 * 3600
    f.fetch_html(URL)
    assert page_calls(curl) == [URL, URL]


def test_requests_are_spaced_5s(clock, curl):
    f.fetch_html(URL)
    f.fetch_html(URL2)
    assert clock.slept and all(s <= 5 for s in clock.slept)
    assert float((f.hltv_cache_dir() / ".last").read_text()) == clock.t


def test_hourly_cap_raises(clock, curl):
    times = [clock.t - 60 * i for i in range(30)]
    (f.hltv_cache_dir() / ".requests").write_text("".join(f"{t}\n" for t in times))
    with pytest.raises(f.RateLimited) as e:
        f.fetch_html(URL)
    assert e.value.status == 429 and e.value.hint
    assert curl.calls == []


def test_old_requests_leave_the_window(clock, curl):
    times = [clock.t - 3600 - i for i in range(30)]
    (f.hltv_cache_dir() / ".requests").write_text("".join(f"{t}\n" for t in times))
    assert f.fetch_html(URL) == PAGE


def test_robots_disallow_raises_without_fetching(clock, curl):
    curl.pages[f.ROBOTS_URL] = Resp(200, "User-agent: *\nDisallow: /matches/\n")
    with pytest.raises(f.Disallowed):
        f.fetch_html(URL)
    assert page_calls(curl) == []


def test_robots_fetched_once_a_day(clock, curl):
    f.fetch_html(URL)
    f.fetch_html(URL2)
    assert [u for u, _ in curl.calls].count(f.ROBOTS_URL) == 1
    clock.t += 25 * 3600
    f.fetch_html("https://www.hltv.org/matches/3/x")
    assert [u for u, _ in curl.calls].count(f.ROBOTS_URL) == 2


def test_non_hltv_url_rejected(clock, curl):
    with pytest.raises(ValueError):
        f.fetch_html("https://example.com/matches/1/x")


def test_http_error_not_cached(clock, curl):
    curl.pages[URL] = Resp(404, "not found")
    with pytest.raises(f.FetchError) as e:
        f.fetch_html(URL)
    assert e.value.status == 404
    assert not f.cache_paths(URL)[0].exists()


@pytest.mark.parametrize(
    "resp",
    [
        Resp(200, CF_BODY),
        Resp(403, "denied"),
        Resp(503, "x"),
        Resp(200, "<a href='/cdn-cgi/challenge-platform/h/b/cf-chl'>"),
    ],
)
def test_cloudflare_falls_back_to_playwright(clock, curl, browser, resp):
    curl.pages[URL] = resp
    assert f.fetch_html(URL) == PAGE
    assert browser.calls == [(URL, False)]  # headed the first time
    assert json.loads(f.cache_paths(URL)[1].read_text())["method"] == "playwright"
    assert f.preferred_method() == "playwright"
    assert (f.profile_dir() / ".cf-passed").exists()


def test_playwright_preferred_and_headless_after_first_pass(clock, curl, browser):
    curl.pages[URL] = Resp(200, CF_BODY)
    f.fetch_html(URL)
    n_curl = len(curl.calls)
    f.fetch_html(URL2)
    assert browser.calls[-1] == (URL2, True)
    assert len(curl.calls) == n_curl  # curl skipped: playwright is preferred


def test_playwright_still_challenged(clock, curl, browser):
    curl.pages[URL] = Resp(403, CF_BODY)
    (f.profile_dir() / ".cf-passed").write_text("x")
    browser.result["body"] = CF_BODY
    with pytest.raises(f.Challenged):
        f.fetch_html(URL)
    assert browser.calls == [(URL, True)]
    assert not (f.profile_dir() / ".cf-passed").exists()  # next run opens a window
    assert len(page_calls(curl)) == 1  # two attempts total, no more retries
