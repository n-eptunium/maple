"""One router per module. Each file defines `router: fastapi.APIRouter` with its own paths
(normally prefix="/api/<module>"). app.py includes every file here automatically."""
