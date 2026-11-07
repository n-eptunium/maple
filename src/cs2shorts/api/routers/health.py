from fastapi import APIRouter

from cs2shorts import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "version": __version__}
