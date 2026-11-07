"""`cs2shorts` command line, assembled from the modules in this package.

Each module defines `app = typer.Typer(...)`, mounted as `cs2shorts <name>` where name is
the module's `NAME` (default: module name with "_" -> "-"). A sub-app with a single action
uses `@app.callback(invoke_without_command=True)` so `cs2shorts <name>` runs it directly.
Do not add commands here.
"""

from __future__ import annotations

import typer

from cs2shorts.discovery import iter_modules

CLI_PACKAGE = "cs2shorts.cli"


def build_app(package: str = CLI_PACKAGE) -> typer.Typer:
    root = typer.Typer(no_args_is_help=True, add_completion=False)
    for mod in iter_modules(package):
        sub = getattr(mod, "app", None)
        if not isinstance(sub, typer.Typer):
            raise TypeError(f"{mod.__name__} must define `app = typer.Typer(...)`")
        name = getattr(mod, "NAME", mod.__name__.rsplit(".", 1)[-1].replace("_", "-"))
        root.add_typer(sub, name=name, help=getattr(mod, "HELP", None))
    return root


app = build_app()
