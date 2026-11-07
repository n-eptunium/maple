from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cs2shorts.hltv import FetchError, resolve
from cs2shorts.store.models import Match

router = APIRouter(prefix="/api/hltv", tags=["hltv"])


class ResolveRequest(BaseModel):
    url: str
    fresh: bool = False


def _error(status: int, error: str, hint: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": error, "hint": hint})


# Plain `def`: FastAPI runs it in a worker thread, where Playwright's sync API is allowed.
@router.post("/resolve", response_model=Match, responses={400: {}, 403: {}, 409: {}, 429: {}})
def resolve_url(req: ResolveRequest) -> Match | JSONResponse:
    try:
        return resolve(req.url, fresh=req.fresh)
    except ValueError as e:
        return _error(400, str(e), "Paste an hltv.org /matches/ or /news/ URL.")
    except FetchError as e:
        status = e.status if e.status and 400 <= e.status < 500 else 424
        return _error(status, str(e), e.hint)
