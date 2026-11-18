# /// script
# requires-python = ">=3.13"
# dependencies = ["fonttools==4.68.0"]
# ///
"""Draws public/logo.svg: the Material Symbols hamburger (lunch_dining, from md2ui's icon
font, where 🍔 draws it) beside "BURGER SHOP" in Plus Jakarta Sans ExtraBold, both as
paths so the logo needs no font. uv runs it with the fontTools it declares above:

    uv run web/scripts/make_logo.py
"""
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "backend/md2ui_theme/assets"
ICON_FONT = ASSETS / "icons/material-design-icons-md2ui.ttf"
TEXT_FONT = ASSETS / "fonts/PlusJakartaSans-ExtraBold.ttf"
FOREST, MUSTARD = "#2D4E3A", "#E69F35"


def glyph_path(font: TTFont, name: str, scale: float, dx: float, baseline: float) -> str:
    gs = font.getGlyphSet()
    pen = SVGPathPen(gs)
    gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, dx, baseline)))
    return pen.getCommands()


def main(out: Path) -> None:
    icon = TTFont(ICON_FONT)
    burger = icon.getBestCmap()[0x1F354]
    upm = icon["head"].unitsPerEm
    size = 40.0
    # Fit the icon's ink to a 40 x 40 box.
    bp = BoundsPen(icon.getGlyphSet())
    icon.getGlyphSet()[burger].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    s = size / max(x1 - x0, y1 - y0)
    icon_d = glyph_path(icon, burger, s, -x0 * s + (size - (x1 - x0) * s) / 2, y1 * s + (size - (y1 - y0) * s) / 2)

    text = TTFont(TEXT_FONT)
    cmap, hmtx = text.getBestCmap(), text["hmtx"]
    tscale = 26 / text["head"].unitsPerEm
    cap = text["OS/2"].sCapHeight * tscale
    baseline = 20 + cap / 2  # caps centred on the icon
    x, parts = 52.0, []
    for ch in "BURGER SHOP":
        name = cmap[ord(ch)]
        parts.append(glyph_path(text, name, tscale, x, baseline))
        x += hmtx[name][0] * tscale + (0.4 if ch != " " else 0)
    width = round(x + 2)
    out.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 40" width="{width}" height="40" '
        f'role="img" aria-label="Burger Shop">'
        f'<rect width="40" height="40" rx="12" fill="{MUSTARD}"/>'
        f'<g transform="translate(6 6) scale(0.7)"><path fill="{FOREST}" d="{icon_d}"/></g>'
        f'<path fill="{FOREST}" d="{" ".join(parts)}"/></svg>\n'
    )
    mark = out.with_name("logo-mark.svg")
    mark.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">'
        f'<rect width="40" height="40" rx="12" fill="{MUSTARD}"/>'
        f'<g transform="translate(6 6) scale(0.7)"><path fill="{FOREST}" d="{icon_d}"/></g></svg>\n'
    )
    print(out, width, "x 40;", mark)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "web/public/logo.svg")
