from fastapi.testclient import TestClient

from cs2shorts import __version__
from cs2shorts.api.app import create_app


def test_health_and_spa(tmp_path):
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "a.js").write_text("x")
    client = TestClient(create_app(dist=tmp_path))
    for url in ("/health", "/api/health"):
        assert client.get(url).json() == {"ok": True, "version": __version__}
    assert client.get("/").text == "<html>app</html>"
    assert client.get("/playground").text == "<html>app</html>"
    assert client.get("/a.js").text == "x"
    assert client.get("/api/nope").status_code == 404


def test_cors():
    client = TestClient(create_app())
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
