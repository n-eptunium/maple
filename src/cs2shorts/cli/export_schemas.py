import typer

HELP = "Write the JSON schemas of the data models into schemas/."
app = typer.Typer()


@app.callback(invoke_without_command=True)
def export_schemas() -> None:
    from cs2shorts.store.models import export_schemas as run

    for p in run():
        typer.echo(str(p))
