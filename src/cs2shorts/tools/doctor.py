"""Environment checks. One line per check: OK, or FAIL with a fix hint."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from cs2shorts.config import Settings, get_settings
from cs2shorts.store.paths import fonts_dir, web_dir


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str  # what was found when ok, or the fix hint when not


def _run(args: list[str], timeout: float = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def _is_exe(path: str) -> bool:
    return Path(path).is_file() and os.access(path, os.X_OK)


def check_ffmpeg(s: Settings) -> Check:
    if not _is_exe(s.ffmpeg_bin):
        return Check(
            "ffmpeg-full",
            False,
            f"{s.ffmpeg_bin} not found. Run: brew install ffmpeg-full (or set CS2_FFMPEG)",
        )
    try:
        filters = _run([s.ffmpeg_bin, "-hide_banner", "-filters"]).stdout
        encoders = _run([s.ffmpeg_bin, "-hide_banner", "-encoders"]).stdout
    except (OSError, subprocess.SubprocessError) as e:
        return Check("ffmpeg-full", False, f"{s.ffmpeg_bin} failed to run: {e}")
    missing = []
    if not any(line.split()[1:2] == ["ass"] for line in filters.splitlines()):
        missing.append("ass filter (libass)")
    if "h264_videotoolbox" not in encoders:
        missing.append("h264_videotoolbox encoder")
    if missing:
        return Check(
            "ffmpeg-full",
            False,
            f"missing {', '.join(missing)}. Use Homebrew ffmpeg-full: brew install ffmpeg-full",
        )
    return Check("ffmpeg-full", True, s.ffmpeg_bin)


def check_ytdlp(s: Settings) -> Check:
    exe = shutil.which(s.ytdlp_bin)
    if not exe:
        return Check("yt-dlp", False, "not found. Run: brew install yt-dlp")
    try:
        r = _run([exe, "--version"])
    except (OSError, subprocess.SubprocessError) as e:
        return Check("yt-dlp", False, f"failed to run: {e}")
    if r.returncode != 0:
        return Check("yt-dlp", False, f"exited {r.returncode}. Run: brew upgrade yt-dlp")
    return Check("yt-dlp", True, r.stdout.strip())


def check_deno(_: Settings) -> Check:
    exe = shutil.which("deno")
    if not exe:
        return Check("deno", False, "not found (yt-dlp needs it). Run: brew install deno")
    return Check("deno", True, exe)


def check_font(path: Path, hint: str) -> Check:
    if path.is_file() and path.stat().st_size > 0:
        return Check(path.name, True, str(path))
    return Check(path.name, False, f"missing {path}. {hint}")


def check_keychain(_: Settings) -> Check:
    try:
        import keyring

        # Raises NoKeyringError when no usable backend (e.g. no login Keychain).
        keyring.get_password("cs2shorts", "doctor-probe")
        backend = keyring.get_keyring()
    except Exception as e:
        return Check("keychain", False, f"{str(e).rstrip('.')}. Unlock your login Keychain")
    name = type(backend).__name__
    return Check("keychain", True, f"{type(backend).__module__}.{name}")


def check_playwright(_: Settings) -> Check:
    hint = "Run: playwright install chromium"
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            exe = p.chromium.executable_path
    except Exception as e:
        return Check("playwright chromium", False, f"{e.__class__.__name__}. {hint}")
    if not Path(exe).exists():
        return Check("playwright chromium", False, f"{exe} missing. {hint}")
    return Check("playwright chromium", True, exe)


def run_checks(s: Settings | None = None) -> list[Check]:
    s = s or get_settings()
    font_hint = "Run: python -m cs2shorts.tools.fetch_fonts"
    checks: list[Callable[[], Check]] = [
        lambda: check_ffmpeg(s),
        lambda: check_ytdlp(s),
        lambda: check_deno(s),
        lambda: check_font(fonts_dir() / "Dosis-Bold.ttf", font_hint),
        lambda: check_font(web_dir() / "public" / "fonts" / "Fredoka.ttf", font_hint),
        lambda: check_font(web_dir() / "public" / "fonts" / "Dosis-Bold.ttf", font_hint),
        lambda: check_keychain(s),
        lambda: check_playwright(s),
    ]
    out = []
    for fn in checks:
        try:
            out.append(fn())
        except Exception as e:  # a broken check must not hide the others
            out.append(Check(getattr(fn, "__name__", "check"), False, f"crashed: {e}"))
    return out


def format_check(c: Check) -> str:
    return f"{'OK  ' if c.ok else 'FAIL'}  {c.name:20} {c.detail}"


def doctor(print_fn: Callable[[str], None] = print, s: Settings | None = None) -> int:
    """Print one line per check. Returns the exit code (1 if anything failed)."""
    results = run_checks(s)
    for c in results:
        print_fn(format_check(c))
    return 0 if all(c.ok for c in results) else 1


if __name__ == "__main__":
    raise SystemExit(doctor())
