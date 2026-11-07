import sys

import pytest
import typer
from fastapi import APIRouter
from typer.testing import CliRunner

from cs2shorts.api.app import discover_routers
from cs2shorts.cli import app, build_app


@pytest.fixture
def plugin_pkg(tmp_path, monkeypatch):
    pkg = tmp_path / "fakeplug"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    monkeypatch.syspath_prepend(str(tmp_path))
    yield pkg
    for name in [n for n in sys.modules if n.startswith("fakeplug")]:
        del sys.modules[name]


def test_routers_discovered(plugin_pkg):
    (plugin_pkg / "zeta.py").write_text(
        "from fastapi import APIRouter\nrouter = APIRouter(prefix='/api/zeta')\n"
    )
    (plugin_pkg / "_private.py").write_text("x = 1\n")
    routers = discover_routers("fakeplug")
    assert [r.prefix for r in routers] == ["/api/zeta"]
    assert all(isinstance(r, APIRouter) for r in routers)


def test_router_module_without_router_fails(plugin_pkg):
    (plugin_pkg / "bad.py").write_text("x = 1\n")
    with pytest.raises(TypeError, match="router"):
        discover_routers("fakeplug")


def test_cli_subapps_discovered(plugin_pkg):
    (plugin_pkg / "hello_world.py").write_text(
        "import typer\napp = typer.Typer()\n"
        "@app.callback(invoke_without_command=True)\n"
        "def run():\n    typer.echo('hi')\n"
    )
    root = build_app("fakeplug")
    assert isinstance(root, typer.Typer)
    result = CliRunner().invoke(root, ["hello-world"])
    assert result.exit_code == 0 and "hi" in result.output


def test_builtin_commands_mounted():
    out = CliRunner().invoke(app, ["--help"]).output
    for cmd in ("doctor", "serve", "fetch-fonts", "export-schemas"):
        assert cmd in out
