# CS2 Shorts

Turns Counter-Strike 2 pro match highlights from HLTV into 9:16 edits with burned-in
captions and posts them to YouTube Shorts and TikTok. macOS on Apple Silicon only.

## Setup

```bash
brew install python@3.12 uv node ffmpeg-full yt-dlp deno
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
playwright install chromium
python -m cs2shorts.tools.fetch_fonts
cs2shorts doctor
(cd web && npm install && npm run build)
cs2shorts serve            # http://127.0.0.1:8765/ (Playground at /playground)
```

For UI work, run `cs2shorts serve --no-open` and `cd web && npm run dev`. Vite runs on
:5173 and proxies `/api` to :8765.

Settings use `CS2_` env vars (see `.env.example`). `CS2_FFMPEG` overrides the ffmpeg path.

## Layout and extension rules

Later stages add files. They do not edit shared ones.

| Add a… | Create | Contract |
|---|---|---|
| API module | `src/cs2shorts/api/routers/<module>.py` | defines `router = APIRouter(prefix="/api/<module>")` |
| CLI command group | `src/cs2shorts/cli/<module>.py` | defines `app = typer.Typer()`, mounted as `cs2shorts <module>` (`_` becomes `-`; override with `NAME`, help text with `HELP`) |

Both are auto-discovered (`cs2shorts.discovery`). Files starting with `_` are skipped.
A file without `router` / `app` fails at startup. A single-action command uses
`@app.callback(invoke_without_command=True)`, like `cli/doctor.py`.
Keep the logic in plain functions elsewhere (e.g. `tools/`, `store/`) so the CLI and the API
call the same code. Do not edit `api/app.py` or `cli/__init__.py`.

All data models live in `src/cs2shorts/store/models.py`. After changing one, run
`cs2shorts export-schemas` and commit `schemas/`. A test checks they match.

## Checks

```bash
pytest && ruff check src tests && mypy src
cd web && npm run typecheck && npm run lint && npm test
```
