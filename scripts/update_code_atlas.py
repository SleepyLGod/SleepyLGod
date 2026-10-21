#!/usr/bin/env python3
"""Build a repository-hosted Code Atlas from public, non-fork GitHub repositories.

Only Python's standard library is needed. A saved JSON snapshot can also be
rendered offline without changing its observation date.
"""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
import json
import math
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "dark": {"background": "#0d1117", "border": "#30363d", "text": "#e6edf3",
             "muted": "#a7b0bc", "orbit": "#252334",
             "dots": ("#c5a0f5", "#eea5cc", "#98c5ec", "#b7bcf0", "#98a5b5")},
    "light": {"background": "#ffffff", "border": "#d1d9e0", "text": "#1f2328",
              "muted": "#59636e", "orbit": "#eee8f5",
              "dots": ("#8050b5", "#ae447c", "#2e75a9", "#6668a7", "#69778b")},
}
HONG_KONG = timezone(timedelta(hours=8))


def valid_username(username):
    if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", username):
        raise ValueError("Invalid GitHub username")
    return username


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
        raise ValueError("Unsupported Code Atlas snapshot")
    valid_username(snapshot.get("username"))
    captured = snapshot.get("captured_at")
    if not isinstance(captured, str):
        raise ValueError("Snapshot needs its original observation time")
    observed = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("Snapshot observation time needs a timezone")
    if not isinstance(snapshot.get("source"), str) or not snapshot["source"].startswith("https://"):
        raise ValueError("Snapshot needs an HTTPS source URL")
    repos = snapshot.get("repositories")
    if not isinstance(repos, list):
        raise ValueError("Expected a complete public repository list")
    names = set()
    for repo in repos:
        if not isinstance(repo, dict):
            raise ValueError("Invalid repository record")
        name = repo.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Invalid repository name")
        if name.casefold() in names:
            raise ValueError("Duplicate repository; refusing partial or inconsistent data")
        names.add(name.casefold())
        stars = repo.get("stars")
        if type(stars) is not int or stars < 0:
            raise ValueError("Star counts must be nonnegative integers")
        language = repo.get("language")
        if language is not None and (not isinstance(language, str) or not language.strip()):
            raise ValueError("Invalid primary language")
    return snapshot


def fetch_repositories(username, token):
    """Read every page; never publish a snapshot after a partial API failure."""
    valid_username(username)
    repos = []
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "SleepyLGod-Code-Atlas",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for page in range(1, 101):
        query = urlencode({"type": "owner", "sort": "full_name", "direction": "asc",
                           "per_page": 100, "page": page})
        request = Request(f"https://api.github.com/users/{username}/repos?{query}", headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                batch = json.load(response)
        except HTTPError as error:
            raise RuntimeError(f"GitHub API returned HTTP {error.code}; keeping the previous snapshot") from None
        if not isinstance(batch, list):
            raise ValueError("GitHub did not return a repository list")
        for repo in batch:
            if not isinstance(repo, dict) or type(repo.get("fork")) is not bool or type(repo.get("private")) is not bool:
                raise ValueError("Incomplete repository visibility or fork metadata")
            if repo["fork"] or repo["private"]:
                continue
            if repo.get("owner", {}).get("login", "").casefold() != username.casefold():
                raise ValueError("Unexpected repository owner")
            repos.append({"name": repo["name"], "stars": repo["stargazers_count"], "language": repo["language"]})
        if len(batch) < 100:
            return repos
    raise ValueError("Repository pagination limit reached; refusing truncated data")


def summarize(snapshot):
    repos = snapshot["repositories"]
    languages = Counter(repo["language"] for repo in repos if repo["language"] is not None)
    ordered = sorted(languages.items(), key=lambda item: (-item[1], item[0].casefold()))
    # Keep three named groups, then account for every remaining language and
    # repository without a detected language. Each repository is exactly one dot.
    groups = ordered[:3]
    if len(ordered) > 3:
        groups.append(("Other Languages", sum(count for _, count in ordered[3:])))
    unknown = sum(repo["language"] is None for repo in repos)
    if unknown:
        groups.append(("Unclassified", unknown))
    return {"repos": len(repos), "stars": sum(repo["stars"] for repo in repos),
            "languages": len(languages), "distribution": ordered, "groups": groups}


def render_card(snapshot, theme, mobile=False):
    data = summarize(snapshot)
    palette = PALETTES[theme]
    width, height = (360, 324) if mobile else (760, 224)
    observed = datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00"))
    day = observed.astimezone(HONG_KONG).date()
    language_summary = ", ".join(f"{name}: {count}" for name, count in data["distribution"])
    description = (f'{snapshot["username"]}: {data["repos"]} public, non-fork repositories, '
                   f'{data["stars"]} stars earned, {data["languages"]} primary languages. '
                   f'One dot is one repository. Language groups count repositories, not code bytes or proficiency. '
                   f'Includes archived repositories. {language_summary}. '
                   f'Snapshot {day} Hong Kong time. Source: {snapshot["source"]}')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Code Atlas · A Constellation of Code</title>',
             f'<desc id="desc">{escape(description)}</desc>',
             f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{palette["background"]}" stroke="{palette["border"]}"/>',
             f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" fill="{palette["text"]}">']

    def text(x, y, value, size=13, color=None, anchor="start", weight="400", spacing=None):
        tracking = f' letter-spacing="{spacing}"' if spacing else ""
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color or palette["text"]}" text-anchor="{anchor}" font-weight="{weight}"{tracking}>{escape(str(value))}</text>')

    text(22 if mobile else 24, 25, "A CONSTELLATION OF CODE", 11, palette["muted"], spacing="1.5")
    text(180 if mobile else 736, 309 if mobile else 25, f"Snapshot {day} · HKT", 10,
         palette["muted"], "middle" if mobile else "end")
    cx, cy, radius = (94, 114, 58) if mobile else (126, 112, 64)
    for ring in (radius - 13, radius + 13):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{ring}" fill="none" stroke="{palette["orbit"]}" stroke-dasharray="2 7"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{palette["orbit"]}"/>')
    dot_index = 0
    top_languages = {name for name, _ in data["distribution"][:3]}
    for group_index, (label, count) in enumerate(data["groups"]):
        color_index = 4 if label == "Unclassified" else 3 if label == "Other Languages" else group_index
        color = palette["dots"][color_index]
        if label == "Other Languages":
            group_repos = [repo for repo in snapshot["repositories"] if repo["language"] is not None and repo["language"] not in top_languages]
        else:
            group_repos = [repo for repo in snapshot["repositories"] if repo["language"] == (None if label == "Unclassified" else label)]
        for repo in sorted(group_repos, key=lambda repo: repo["name"].casefold()):
            angle = -math.pi / 2 + 2 * math.pi * dot_index / data["repos"]
            x, y = cx + math.cos(angle) * radius, cy + math.sin(angle) * radius
            dot_radius = min(4.8, 170 / data["repos"])
            parts.append(f'<circle class="repo-dot" cx="{x:.2f}" cy="{y:.2f}" r="{dot_radius:.2f}" fill="{color}"><title>{escape(repo["name"])} · {escape(repo["language"] or "Unclassified")}</title></circle>')
            dot_index += 1
        column, row = group_index % 2, group_index // 2
        lx, ly = (24 + column * 166, 216 + row * 23) if mobile else (268 + column * 230, 129 + row * 22)
        parts.append(f'<circle cx="{lx}" cy="{ly - 4}" r="4" fill="{color}"/>')
        text(lx + 13, ly, label, 12, palette["muted"])
        text(lx + (136 if mobile else 182), ly, count, 13, anchor="end", weight="600")
    text(cx, cy + 7, data["repos"], 40, palette["dots"][0], "middle", "600")
    text(cx, cy + 30, "Original Repos", 12, palette["muted"], "middle")
    metrics = ((data["stars"], "Stars Earned"), (data["languages"], "Primary Languages"))
    for index, (value, label) in enumerate(metrics):
        x, y = (252, 88 + index * 60) if mobile else (268 + index * 230, 74)
        text(x, y, f"{value:,}", 30, palette["dots"][0], "middle" if mobile else "start", "600")
        text(x, y + 21, label, 12, palette["muted"], "middle" if mobile else "start")
    if mobile:
        text(180, 289, "One Dot = One Repo · Color = Primary Language", 10, palette["muted"], "middle")
    else:
        text(24, 206, "One Dot = One Public Original Repo", 11, palette["muted"])
        text(736, 206, "Color = Primary Language", 11, palette["muted"], "end")
    parts.append("</g></svg>\n")
    return "\n".join(parts)


def write_atlas(output, snapshot):
    validate_snapshot(snapshot)
    files = {}
    for theme in PALETTES:
        for mobile in (False, True):
            name = f'code-atlas-{"mobile-" if mobile else ""}{theme}.svg'
            files[name] = render_card(snapshot, theme, mobile)
            ET.fromstring(files[name])
    files["code-atlas.json"] = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    # Fetch, validate and render everything before replacing any last good file.
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        for name, content in files.items():
            (Path(temporary) / name).write_text(content, encoding="utf-8")
        for name in files:
            os.replace(Path(temporary) / name, output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="SleepyLGod")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/profile")
    parser.add_argument("--snapshot", type=Path, help="Rebuild an existing JSON snapshot offline, preserving its original date")
    args = parser.parse_args()
    valid_username(args.username)
    if args.snapshot:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        validate_snapshot(snapshot)
        if snapshot["username"].casefold() != args.username.casefold():
            raise ValueError("Snapshot belongs to another GitHub user")
    else:
        repos = fetch_repositories(args.username, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
        snapshot = {"version": 1, "username": args.username,
                    "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "source": f"https://api.github.com/users/{args.username}/repos",
                    "repositories": sorted(repos, key=lambda repo: repo["name"].casefold())}
    write_atlas(args.output, snapshot)
    stats = summarize(snapshot)
    print(f'Updated Code Atlas: {stats["repos"]} public original repos, {stats["stars"]} stars, {stats["languages"]} primary languages')


if __name__ == "__main__":
    main()
