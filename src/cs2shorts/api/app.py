"""FastAPI app. Routers are discovered from cs2shorts.api.routers; do not add routes here."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from cs2shorts import __version__
from cs2shorts.discovery import iter_modules
from cs2shorts.store.paths import web_dist_dir

ROUTERS_PACKAGE = "cs2shorts.api.routers"


def discover_routers(package: str = ROUTERS_PACKAGE) -> list[APIRouter]:
    routers = []
    for mod in iter_modules(package):
        router = getattr(mod, "router", None)
        if not isinstance(router, APIRouter):
            raise TypeError(f"{mod.__name__} must define `router = APIRouter(...)`")
        routers.append(router)
    return routers


def create_app(dist: Path | None = None) -> FastAPI:
    app = FastAPI(title="CS2 Shorts", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in discover_routers():
        app.include_router(router)

    # Built web UI, registered last so API routes win.
    dist = dist or web_dist_dir()
    index = dist / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/") or not index.is_file():
            raise HTTPException(status_code=404)
        root = dist.resolve()
        target = (root / path).resolve()
        if path and target.is_file() and target.is_relative_to(root):
            return FileResponse(target)
        return FileResponse(index)  # SPA fallback, e.g. /playground

    return app


app = create_app()
