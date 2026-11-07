"""Find plugin modules in a package so stages add files instead of editing shared ones."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Iterator
from types import ModuleType


def iter_modules(package: str) -> Iterator[ModuleType]:
    """Import every non-private submodule of `package`, sorted by name."""
    pkg = importlib.import_module(package)
    names = sorted(m.name for m in pkgutil.iter_modules(pkg.__path__) if not m.name.startswith("_"))
    for name in names:
        yield importlib.import_module(f"{package}.{name}")
