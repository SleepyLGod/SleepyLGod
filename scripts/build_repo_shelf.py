#!/usr/bin/env python3
"""Render a manually curated repository shelf without a live card service."""

from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "dark": ("#0d1117", "#30363d", "#c5a0f5", "#a7b0bc"),
    "light": ("#ffffff", "#d1d9e0", "#8050b5", "#59636e"),
}


def main():
    repos = json.loads((ROOT / "profile/recommendations.json").read_text())
    output = ROOT / "assets/recommendations"
    cards = {}
    links = []
    seen = set()
    for repo in repos:
        name, description = repo["repo"], repo["description"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name) or name.casefold() in seen:
            raise ValueError("Use unique owner/repo names")
        if not isinstance(description, str) or len(description) > 45:
            raise ValueError("Keep each description to one short line")
        seen.add(name.casefold())
        owner, project = name.split("/")
        slug = name.lower().replace("/", "--")
        for theme, (background, border, accent, muted) in PALETTES.items():
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="368" height="76" viewBox="0 0 368 76" role="img" aria-labelledby="title desc">
<title id="title">{escape(name)}</title>
<desc id="desc">{escape(description)}</desc>
<rect x="0.5" y="0.5" width="367" height="75" rx="10" fill="{background}" stroke="{border}"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">
<text x="17" y="29" font-size="15"><tspan fill="{muted}">{escape(owner)}/</tspan><tspan fill="{accent}" font-weight="600">{escape(project)}</tspan></text>
<text x="17" y="54" font-size="12" fill="{muted}">{escape(description)}</text>
<path d="M342 27h8v8m0-8-10 10" fill="none" stroke="{muted}" stroke-width="1.3"/>
</g></svg>
'''
            ET.fromstring(svg)
            cards[f"{slug}-{theme}.svg"] = svg
        alt = escape(f"{name}: {description}", quote=True)
        links.append(f'''  <a href="https://github.com/{name}"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/recommendations/{slug}-dark.svg" /><img src="./assets/recommendations/{slug}-light.svg" width="368" alt="{alt}" /></picture></a>''')
    block = '<p align="center">\n' + '\n'.join(links) + '\n</p>'
    readme = ROOT / "README.md"
    updated, count = re.subn(r"(?<=<!-- REPO-SHELF:START -->).*?(?=<!-- REPO-SHELF:END -->)", '\n' + block + '\n', readme.read_text(), flags=re.S)
    if count != 1:
        raise ValueError("Expected one repository shelf marker pair")
    output.mkdir(parents=True, exist_ok=True)
    for name, content in cards.items():
        (output / name).write_text(content)
    readme.write_text(updated)
    print(f"Built {len(repos)} repository links with local light/dark cards")


if __name__ == "__main__":
    main()
