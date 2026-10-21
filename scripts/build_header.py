#!/usr/bin/env python3
"""Build a font-independent SVG greeting from the vendored OFL Dancing Script font.

Requires fonttools only when rebuilding; viewing the header needs no fonts or service.
"""

from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


ROOT = Path(__file__).resolve().parents[1]


def main():
    font = instantiateVariableFont(TTFont(ROOT / "assets/fonts/DancingScript.ttf"), {"wght": 600})
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    path = SVGPathPen(glyphs)
    bounds = BoundsPen(glyphs)
    advance = 0
    for character in "Hi there!":
        name = cmap[ord(character)]
        transform = (1, 0, 0, 1, advance, 0)
        glyphs[name].draw(TransformPen(path, transform))
        glyphs[name].draw(TransformPen(bounds, transform))
        advance += font["hmtx"].metrics[name][0]
    left, bottom, right, top = bounds.bounds
    scale = 68 / font["head"].unitsPerEm
    x = (760 - (right - left) * scale) / 2 - left * scale
    baseline = (108 - (top - bottom) * scale) / 2 + top * scale
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="108" viewBox="0 0 760 108" role="img" aria-labelledby="title description">
  <title id="title">Hi there!</title>
  <desc id="description">A handwritten greeting in Dancing Script. Letter outlines are included, so no external font is required.</desc>
  <defs><linearGradient id="greeting" x2="100%"><stop stop-color="#b580e3"/><stop offset="1" stop-color="#839fd0"/></linearGradient></defs>
  <g transform="translate({x:.3f} {baseline:.3f}) scale({scale:.6f} {-scale:.6f})" fill="url(#greeting)">
    <path d="{path.getCommands()}"/>
  </g>
</svg>
'''
    (ROOT / "assets/profile/header.svg").write_text(svg)
    print("Generated local handwritten greeting: Hi there!")


if __name__ == "__main__":
    main()
