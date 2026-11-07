import typer

HELP = "Download Dosis and Fredoka and build the static caption font."
app = typer.Typer()


@app.callback(invoke_without_command=True)
def fetch_fonts() -> None:
    from cs2shorts.tools.fetch_fonts import main

    main()
