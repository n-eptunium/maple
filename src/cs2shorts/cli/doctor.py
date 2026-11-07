import typer

HELP = "Check ffmpeg-full, yt-dlp, deno, fonts, Keychain and Playwright."
app = typer.Typer()


@app.callback(invoke_without_command=True)
def doctor() -> None:
    from cs2shorts.tools.doctor import doctor as run

    raise typer.Exit(run(typer.echo))
