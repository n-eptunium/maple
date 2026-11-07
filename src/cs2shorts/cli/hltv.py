from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path
from typing import Annotated

import typer

HELP = "Resolve an HLTV match or news URL into its highlights."
# Options may follow the URL (`cs2shorts hltv <url> --json`).
app = typer.Typer(context_settings={"allow_interspersed_args": True})


def _fmt(v: object) -> str:
    return "-" if v is None else str(v)


@app.callback(invoke_without_command=True)
def hltv(
    url: Annotated[str, typer.Argument(help="https://www.hltv.org/matches/... or /news/...")],
    as_json: Annotated[bool, typer.Option("--json", help="Print the Match as JSON.")] = False,
    fresh: Annotated[
        bool, typer.Option("--fresh", help="Ignore the 24 h cache (one request).")
    ] = False,
    save_fixture: Annotated[
        Path | None,
        typer.Option("--save-fixture", help="Also copy the page HTML here (regression tests)."),
    ] = None,
) -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    from cs2shorts.hltv import FetchError, fetch_html, resolve
    from cs2shorts.hltv.fetch import cache_paths
    from cs2shorts.hltv.resolve import normalize_url

    try:
        match = resolve(url, fresh=fresh)
        if save_fixture is not None:
            page = normalize_url(url)
            fetch_html(page)  # cached by resolve(): no extra request
            save_fixture.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cache_paths(page)[0], save_fixture)
            typer.echo(f"saved {save_fixture}", err=True)
    except ValueError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(2) from e
    except FetchError as e:
        typer.echo(f"error: {e}\nhint: {e.hint}", err=True)
        raise typer.Exit(1) from e

    if as_json:
        typer.echo(match.model_dump_json(indent=2))
        return

    typer.echo(f"{match.event or '(unknown event)'}  {match.date}")
    typer.echo(" vs ".join(t.name for t in match.teams) or "(teams not found)")
    if match.maps:
        typer.echo("Maps:")
        for m in match.maps:
            typer.echo(f"  {m.name:<10} {_fmt(m.score_a):>2} - {_fmt(m.score_b)}")
    typer.echo(f"Highlights ({len(match.highlights)}):")
    for i, h in enumerate(match.highlights, 1):
        typer.echo(f"  {i:>2}. {h.title}")
        typer.echo(f"      {h.embed_url}  [{h.source}]")
        typer.echo(
            f"      player={_fmt(h.player)} team={_fmt(h.team)} action={_fmt(h.action)} "
            f"map={_fmt(h.map)} round={_fmt(h.round)}"
        )
    for w in match.warnings:
        typer.echo(f"warning: {w}", err=True)
