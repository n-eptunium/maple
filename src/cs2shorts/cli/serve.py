import threading
import webbrowser

import typer

from cs2shorts.config import get_settings

HELP = "Run the local API and web UI."
app = typer.Typer()


@app.callback(invoke_without_command=True)
def serve(
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open the browser."),
    port: int | None = typer.Option(None, help="Port (default CS2_PORT or 8765)."),
) -> None:
    import uvicorn

    port = port or get_settings().port
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=(f"http://127.0.0.1:{port}/",)).start()
    uvicorn.run("cs2shorts.api.app:app", host="127.0.0.1", port=port)
