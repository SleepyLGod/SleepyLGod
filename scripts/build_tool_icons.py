#!/usr/bin/env python3
"""Cache the original readme-components logo presentation without its web service.

The HTML layout and CSS are adapted from harish-sethuraman/readme-components,
commit 923a60dead6c960276d3cf78d7100c82f9d9dfbe, under its MIT license.
The original spin animation is four seconds per revolution.
"""

from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "assets/icons/animated"
    template = (output / "style.css").read_text()
    manifest = json.loads((output / "icons.json").read_text())
    for icon in manifest:
        logo = (ROOT / "assets/icons/monochrome" / (icon["slug"] + ".svg")).read_text()
        ET.fromstring(logo)
        style = template.replace("#9847B9", "#" + icon["color"])
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="70" height="60" viewBox="0 0 70 60" role="img">
  <title>{escape(icon["title"])}</title>
  <style>{style}</style>
  <foreignObject height="60" width="70">
    <div class="gradient-btn btn-color" xmlns="http://www.w3.org/1999/xhtml">
      <div class="svg">{logo}</div>
    </div>
  </foreignObject>
</svg>
'''
        ET.fromstring(svg)
        (output / (icon["slug"] + ".svg")).write_text(svg)
    print(f"Generated {len(manifest)} local icons with the original 4-second spin")


if __name__ == "__main__":
    main()
