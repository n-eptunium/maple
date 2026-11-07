import importlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from cs2shorts.api.app import create_app
from cs2shorts.cli import app as cli_app
from cs2shorts.hltv import fetch as f
from cs2shorts.hltv.resolve import normalize_url

r = importlib.import_module("cs2shorts.hltv.resolve")

SYN = Path(__file__).parent / "fixtures" / "hltv" / "synthetic"
URL = "https://www.hltv.org/matches/2400008/the-mongolz-vs-natus-vincere-iem-beijing-2026"


def seed():
    f._write_cache(URL, (SYN / "match.html").read_text(), 200, "curl")


def test_normalize_url():
    assert normalize_url("hltv.org/matches/1/x?a=b#c") == "https://www.hltv.org/matches/1/x"


def test_api_resolve_from_cache():
    seed()
    res = TestClient(create_app()).post("/api/hltv/resolve", json={"url": URL})
    assert res.status_code == 200
    body = res.json()
    assert body["event"] == "Synthetic Cup 2026" and len(body["highlights"]) == 3


def test_api_errors():
    c = TestClient(create_app())
    res = c.post("/api/hltv/resolve", json={"url": "https://example.com/"})
    assert res.status_code == 400 and set(res.json()) == {"error", "hint"}
    res = c.post("/api/hltv/resolve", json={"url": "https://www.hltv.org/stats"})
    assert res.status_code == 400


def test_api_rate_limited(monkeypatch):
    def limited(url, fresh=False):
        raise f.RateLimited("too many", hint="wait", status=429)

    monkeypatch.setattr("cs2shorts.api.routers.hltv.resolve", limited)
    res = TestClient(create_app()).post("/api/hltv/resolve", json={"url": URL})
    assert res.status_code == 429 and res.json() == {"error": "too many", "hint": "wait"}


def test_cli_text_json_and_save_fixture(tmp_path):
    seed()
    runner = CliRunner()
    out = runner.invoke(cli_app, ["hltv", URL])
    assert out.exit_code == 0, out.output
    for s in (
        "Synthetic Cup 2026",
        "The MongolZ vs Natus Vincere",
        "Mirage",
        "13 - 9",
        "https://clips.twitch.tv/SyntheticClipOne-abc123",
        "player=mzinho",
        "action=1v3 clutch",
    ):
        assert s in out.stdout
    fixture = str(tmp_path / "x.html")
    out = runner.invoke(cli_app, ["hltv", URL, "--json", "--save-fixture", fixture])
    assert json.loads(out.stdout)["hltv_id"] == 2400008
    assert (tmp_path / "x.html").read_text() == (SYN / "match.html").read_text()


def test_resolve_dispatch(monkeypatch):
    monkeypatch.setattr(
        r,
        "fetch_html",
        lambda url, max_age_h=24: (
            (SYN / "news.html").read_text() if "/news/" in url else (SYN / "match.html").read_text()
        ),
    )
    m = r.resolve("https://www.hltv.org/news/42000/x")
    assert m.hltv_id == 2400008 and len(m.highlights) == 5
