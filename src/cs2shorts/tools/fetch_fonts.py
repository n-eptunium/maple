"""Download Dosis + Fredoka, write a static Dosis-Bold.ttf, copy both fonts to the web app.

Idempotent: files that already exist are not downloaded or rebuilt again.
Run: python -m cs2shorts.tools.fetch_fonts
"""

from __future__ import annotations

import shutil
from pathlib import Path

import httpx
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from cs2shorts.store.paths import fonts_dir, web_dir

GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"
DOSIS_VF_URL = f"{GF}/dosis/Dosis%5Bwght%5D.ttf"
DOSIS_OFL_URL = f"{GF}/dosis/OFL.txt"
FREDOKA_VF_URL = f"{GF}/fredoka/Fredoka%5Bwdth,wght%5D.ttf"
FREDOKA_OFL_URL = f"{GF}/fredoka/OFL.txt"


def download(url: str, dest: Path, client: httpx.Client) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = client.get(url, follow_redirects=True, timeout=60)
    r.raise_for_status()
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(r.content)
    tmp.replace(dest)
    return dest


def is_static(path: Path) -> bool:
    return "fvar" not in TTFont(path)


def make_static(vf_path: Path, out: Path, wght: int = 700) -> Path:
    if out.exists() and is_static(out):
        return out
    font = TTFont(vf_path)
    try:
        static = instantiateVariableFont(font, {"wght": wght}, updateFontNames=True)
    except Exception:  # name update needs a STAT table; fall back to plain pinning
        static = instantiateVariableFont(TTFont(vf_path), {"wght": wght})
    static["OS/2"].usWeightClass = wght
    static.save(out)
    return out


def copy_if_changed(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.read_bytes() != src.read_bytes():
        shutil.copyfile(src, dest)
    return dest


def fetch_fonts(fonts: Path | None = None, web_fonts: Path | None = None) -> dict[str, Path]:
    fonts = fonts or fonts_dir()
    web_fonts = web_fonts or (web_dir() / "public" / "fonts")
    with httpx.Client() as client:
        dosis_vf = download(DOSIS_VF_URL, fonts / "Dosis[wght].ttf", client)
        fredoka_vf = download(FREDOKA_VF_URL, fonts / "Fredoka[wdth,wght].ttf", client)
        dosis_ofl = download(DOSIS_OFL_URL, fonts / "OFL-Dosis.txt", client)
        fredoka_ofl = download(FREDOKA_OFL_URL, fonts / "OFL-Fredoka.txt", client)

    combined = (
        "Dosis\n=====\n\n"
        + dosis_ofl.read_text()
        + "\n\nFredoka\n=======\n\n"
        + fredoka_ofl.read_text()
    )
    ofl = fonts / "OFL.txt"
    if not ofl.exists() or ofl.read_text() != combined:
        ofl.write_text(combined)

    dosis_bold = make_static(dosis_vf, fonts / "Dosis-Bold.ttf", 700)
    return {
        "dosis_bold": dosis_bold,
        # Same file the renderer burns in, so the editor preview matches the video.
        "dosis_web": copy_if_changed(dosis_bold, web_fonts / "Dosis-Bold.ttf"),
        "fredoka_web": copy_if_changed(fredoka_vf, web_fonts / "Fredoka.ttf"),
        "fredoka_ofl_web": copy_if_changed(fredoka_ofl, web_fonts / "OFL.txt"),
        "ofl": ofl,
    }


def main() -> None:
    for name, path in fetch_fonts().items():
        print(f"{name:16} {path}")


if __name__ == "__main__":
    main()
