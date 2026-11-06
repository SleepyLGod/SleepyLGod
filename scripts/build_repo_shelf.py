#!/usr/bin/env python3
"""Render a manually curated repository shelf without a live card service."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "dark": ("#0d1117", "#30363d", "#c5a0f5", "#a7b0bc"),
    "light": ("#ffffff", "#d1d9e0", "#8050b5", "#59636e"),
}
CATEGORIES = {"skills": "🪶 Skills", "tools": "🧰 Toys / Tools", "research": "🔬 Research", "teaching": "🎓 Teaching"}
ASSET_BASE = "https://raw.githubusercontent.com/SleepyLGod/SleepyLGod/profile-shelf-preview-assets/assets/recommendations/"
ICONS = {
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    "table": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M10 3v18"/>',
    "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4M10 10h4v4h-4z"/>',
    "type": '<path d="M4 6V3h16v3M12 3v18m-4 0h8"/>',
    "search": '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="8" r="2"/><path d="m3 18 6-6 4 4 3-3 5 5"/>',
    "music": '<path d="M9 17V5l11-2v12M9 8l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
    "chart": '<path d="M3 3v18h18M6 15l5-5 4 3 6-8m-5 0h5v5"/>',
    "book": '<path d="M12 5C9 2 5 2 2 4v16c3-2 7-2 10 1 3-3 7-3 10-1V4c-3-2-7-2-10 1v16"/>',
}


def load_repos(path):
    repos = json.loads(path.read_text())
    if not isinstance(repos, list) or not repos:
        raise ValueError("Expected a curated repository list")
    seen = set()
    for repo in repos:
        name, description = repo["repo"], repo["description"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name) or name.casefold() in seen:
            raise ValueError("Use unique owner/repo names")
        if not isinstance(description, str) or len(description) > 45:
            raise ValueError("Keep each description to one short line")
        if repo.get("category") not in CATEGORIES or repo.get("icon") not in ICONS:
            raise ValueError("Unknown category or topic icon")
        if type(repo.get("public", True)) is not bool:
            raise ValueError("Repository public status must be a boolean")
        seen.add(name.casefold())
    return repos


def validate_stats(snapshot, repos):
    if snapshot.get("version") != 1:
        raise ValueError("Unsupported recommendation snapshot")
    observed = datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("Recommendation observation time needs a timezone")
    records = snapshot.get("repositories")
    if not isinstance(records, list):
        raise ValueError("Missing recommendation statistics")
    by_name = {}
    for record in records:
        name = record["repo"].casefold()
        if name in by_name:
            raise ValueError("Duplicate recommendation statistics")
        for field in ("stars", "forks"):
            if type(record.get(field)) is not int or record[field] < 0:
                raise ValueError("Stars and forks must be nonnegative integers")
        if not record.get("source", "").startswith("https://"):
            raise ValueError("Missing statistics source")
        by_name[name] = record
    if set(by_name) != {repo["repo"].casefold() for repo in repos if repo.get("public", True)}:
        raise ValueError("Statistics must cover every selected public repository exactly once")
    return by_name


def fetch_stats(repos, token):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "SleepyLGod-Repo-Shelf",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    records = []
    for repo in repos:
        if not repo.get("public", True):
            continue
        url = f'https://api.github.com/repos/{repo["repo"]}'
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                data = json.load(response)
        except HTTPError as error:
            raise RuntimeError(f"Repository API returned HTTP {error.code}; keeping previous cards") from None
        if data.get("private") is not False or data.get("full_name", "").casefold() != repo["repo"].casefold():
            raise ValueError("Expected the selected public repository; check for a rename")
        records.append({"repo": repo["repo"], "stars": data["stargazers_count"],
                        "forks": data["forks_count"], "source": url})
    snapshot = {"version": 1, "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "repositories": records}
    validate_stats(snapshot, repos)
    return snapshot


def render_card(repo, stats, observed, theme):
    background, border, accent, muted = PALETTES[theme]
    owner, project = repo["repo"].split("/")
    public = repo.get("public", True)
    category = CATEGORIES[repo["category"]].split(" ", 1)[1]
    if public:
        stars, forks = f'{stats["stars"]:,}', f'{stats["forks"]:,}'
        description = f'{category}. {repo["description"]} {stats["stars"]} Stars; {stats["forks"]} Forks. Observed {observed}. Source: {stats["source"]}'
        metadata = f'''<g transform="translate(44 57)" fill="none" stroke="#c99a3c" stroke-width="1.2" stroke-linejoin="round"><title>Stars</title><path d="m6 0 1.8 3.7 4.2.6-3 2.9.7 4.1L6 9.4l-3.7 1.9.7-4.1-3-2.9 4.2-.6z"/></g>
<text class="repo-stars" x="63" y="67" font-size="10.5" fill="{muted}">{stars}</text>
<g transform="translate(130 57)" fill="none" stroke="{accent}" stroke-width="1.2"><title>Forks</title><circle cx="2" cy="2" r="1.8"/><circle cx="10" cy="2" r="1.8"/><circle cx="6" cy="11" r="1.8"/><path d="M2 4v2h8V4M6 6v3"/></g>
<text class="repo-forks" x="149" y="67" font-size="10.5" fill="{muted}">{forks}</text>
<path d="M342 18h8v8m0-8-10 10" fill="none" stroke="{muted}" stroke-width="1.3"/>'''
    else:
        description = f'{category}. {repo["description"]} Not yet public.'
        metadata = f'''<g transform="translate(44 56)" fill="none" stroke="{muted}" stroke-width="1.2"><rect x="0" y="4" width="10" height="8" rx="1.5"/><path d="M2 4V2a3 3 0 0 1 6 0v2"/></g>
<text class="repo-status" x="62" y="67" font-size="10.5" fill="{muted}">Not Yet Public</text>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="368" height="80" viewBox="0 0 368 80" role="img" aria-labelledby="title desc">
<title id="title">{escape(repo["repo"])}</title>
<desc id="desc">{escape(description)}</desc>
<rect x="0.5" y="0.5" width="367" height="79" rx="8" fill="{background}" stroke="{border}"/>
<g transform="translate(12 10) scale(.9)" fill="none" stroke="{accent}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[repo["icon"]]}</g>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">
<text x="44" y="24" font-size="13"><tspan fill="{muted}">{escape(owner)}/</tspan><tspan fill="{accent}" font-weight="600">{escape(project)}</tspan></text>
<text x="44" y="45" font-size="11.5" fill="{muted}">{escape(repo["description"])}</text>
{metadata}
<text class="repo-category" x="350" y="67" font-size="10" text-anchor="end" fill="{accent}">{escape(category)}</text>
</g></svg>
'''


def render_readme(repos, asset_base):
    groups = []
    for category, label in CATEGORIES.items():
        selected = [repo for repo in repos if repo["category"] == category]
        if not selected:
            continue
        links = []
        for repo in selected:
            name = repo["repo"]
            slug = name.lower().replace("/", "--")
            public = repo.get("public", True)
            status = "Stars and Forks." if public else "Not Yet Public."
            alt = escape(f'{name}: {repo["description"]} {label}. {status}', quote=True)
            dark, light = (escape(asset_base.rstrip("/") + f"/{slug}-{theme}.svg", quote=True) for theme in ("dark", "light"))
            picture = f'<picture><source media="(prefers-color-scheme: dark)" srcset="{dark}" /><img src="{light}" width="368" alt="{alt}" /></picture>'
            links.append(f'  <a href="https://github.com/{name}">{picture}</a>' if public else '  ' + picture)
        groups.extend(links)
    return '<p align="center">\n' + '\n'.join(groups) + '\n</p>'


def write_cards(output, repos, snapshot):
    stats = validate_stats(snapshot, repos)
    cards = {}
    for repo in repos:
        slug = repo["repo"].lower().replace("/", "--")
        for theme in PALETTES:
            svg = render_card(repo, stats.get(repo["repo"].casefold()), snapshot["captured_at"], theme)
            ET.fromstring(svg)
            cards[f"{slug}-{theme}.svg"] = svg
    cards["stats.json"] = json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        for name, content in cards.items():
            (Path(temporary) / name).write_text(content)
        for name in cards:
            os.replace(Path(temporary) / name, output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="Refresh public Star/Fork counts from GitHub REST")
    mode.add_argument("--snapshot", type=Path, help="Import an observed metadata snapshot")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/recommendations")
    parser.add_argument("--no-readme", action="store_true", help="Render cache files without changing the source branch")
    parser.add_argument("--asset-base", default=ASSET_BASE)
    args = parser.parse_args()
    repos = load_repos(ROOT / "profile/recommendations.json")
    snapshot = fetch_stats(repos, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")) if args.refresh else json.loads(
        (args.snapshot or ROOT / "assets/recommendations/stats.json").read_text())
    updated = None
    if not args.no_readme:
        block = render_readme(repos, args.asset_base)
        updated, count = re.subn(r"(?<=<!-- REPO-SHELF:START -->).*?(?=<!-- REPO-SHELF:END -->)", lambda _: '\n' + block + '\n', (ROOT / "README.md").read_text(), flags=re.S)
        if count != 1:
            raise ValueError("Expected one repository shelf marker pair")
    write_cards(args.output, repos, snapshot)
    if updated is not None:
        (ROOT / "README.md").write_text(updated)
    print(f"Built {len(repos)} categorized repository links with Star/Fork snapshots")


if __name__ == "__main__":
    main()
