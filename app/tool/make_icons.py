# /// script
# requires-python = ">=3.13"
# dependencies = ["fonttools==4.68.0", "skia-python==144.1"]
# ///
"""Draws the app icon's source images into assets/icon/, then
`dart run flutter_launcher_icons` makes every platform size from them:

  icon.png             1024², full bleed: the mustard field with the forest burger (iOS
                       rounds its own corners, so nothing here is transparent)
  icon-foreground.png  1024², transparent, the burger inside Android's adaptive safe zone
                       (the mustard background is pubspec's adaptive_icon_background)
  icon-monochrome.png  the same burger alone, for Android's themed icons

The burger is the glyph md2ui's icon font draws for 🍔 (Material Symbols lunch_dining),
the same one in the header's logo (web/scripts/make_logo.py). uv runs it with the skia and
fontTools it declares above:

    uv run app/tool/make_icons.py
"""
from pathlib import Path

import skia
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

APP = Path(__file__).resolve().parents[1]
FONT = APP.parent / "backend/md2ui_theme/assets/icons/material-design-icons-md2ui.ttf"
OUT = APP / "assets/icon"
SIZE = 1024
MUSTARD, FOREST, BLACK = 0xFFE69F35, 0xFF2D4E3A, 0xFF000000


class SkiaPen(BasePen):
    """Draws a glyph's outline into a skia.Path, flipping y (fonts grow up, images down)."""

    def __init__(self, glyphs, scale: float, dx: float, dy: float):
        super().__init__(glyphs)
        self.path, self.s, self.dx, self.dy = skia.Path(), scale, dx, dy

    def _p(self, pt):
        return self.dx + pt[0] * self.s, self.dy - pt[1] * self.s

    def _moveTo(self, pt):
        self.path.moveTo(*self._p(pt))

    def _lineTo(self, pt):
        self.path.lineTo(*self._p(pt))

    def _curveToOne(self, p1, p2, p3):
        self.path.cubicTo(*self._p(p1), *self._p(p2), *self._p(p3))

    def _qCurveToOne(self, p1, p2):
        self.path.quadTo(*self._p(p1), *self._p(p2))

    def _closePath(self):
        self.path.close()


def burger(share: float) -> skia.Path:
    """The burger glyph, centred, its larger side `share` of the canvas."""
    font = TTFont(FONT)
    glyphs = font.getGlyphSet()
    name = font.getBestCmap()[0x1F354]
    bounds = BoundsPen(glyphs)
    glyphs[name].draw(bounds)
    x0, y0, x1, y1 = bounds.bounds
    s = SIZE * share / max(x1 - x0, y1 - y0)
    dx = (SIZE - (x1 - x0) * s) / 2 - x0 * s
    dy = (SIZE + (y1 - y0) * s) / 2 + y0 * s
    pen = SkiaPen(glyphs, s, dx, dy)
    glyphs[name].draw(pen)
    return pen.path


def save(name: str, background: int | None, colour: int, share: float) -> None:
    surface = skia.Surface(SIZE, SIZE)
    canvas = surface.getCanvas()
    canvas.clear(background if background is not None else skia.ColorTRANSPARENT)
    canvas.drawPath(burger(share), skia.Paint(AntiAlias=True, Color=colour))
    surface.makeImageSnapshot().save(str(OUT / name), skia.kPNG)
    print(OUT / name)


OUT.mkdir(parents=True, exist_ok=True)
save("icon.png", MUSTARD, FOREST, 0.56)
# Android shows the middle 66% of an adaptive icon, and masks it to a circle at most:
# the burger stays well inside that.
save("icon-foreground.png", None, FOREST, 0.40)
save("icon-monochrome.png", None, BLACK, 0.40)
