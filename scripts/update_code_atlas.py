#!/usr/bin/env python3
"""Build repository-hosted recent contribution and Star snapshots.

Only Python's standard library is needed. A saved JSON snapshot can also be
rendered offline without changing its observation date.
"""

import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
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
    if not isinstance(snapshot, dict) or snapshot.get("version") != 2:
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
    normalize_recent_days(snapshot.get("recent_days"), observed)
    if not isinstance(snapshot.get("recent_source"), str) or not snapshot["recent_source"].startswith("https://"):
        raise ValueError("Snapshot needs a recent activity source")
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


def normalize_recent_days(raw, observed):
    end = observed.astimezone(timezone.utc).date()
    expected = [(end - timedelta(days=29 - index)).isoformat() for index in range(30)]
    if not isinstance(raw, list):
        raise ValueError("Expected 30 complete days of recent contributions")
    selected = {}
    for day in raw:
        day_date = date.fromisoformat(day["date"]).isoformat()
        count = day["contributionCount"]
        if type(count) is not int or count < 0:
            raise ValueError("Contribution counts must be nonnegative integers")
        if day_date in expected:
            if day_date in selected:
                raise ValueError("Duplicate recent contribution date")
            selected[day_date] = count
    if set(selected) != set(expected):
        raise ValueError("Expected 30 complete days of recent contributions")
    return [{"date": day, "contributionCount": selected[day]} for day in expected]


def fetch_recent_days(username, observed, token):
    if not token:
        raise ValueError("Recent contribution refresh needs GH_TOKEN or GITHUB_TOKEN")
    first = observed.astimezone(timezone.utc).date() - timedelta(days=29)
    query = """query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) { contributionsCollection(from: $from, to: $to) {
        contributionCalendar { weeks { contributionDays { date contributionCount } } }
      } }
    }"""
    payload = json.dumps({"query": query, "variables": {"login": username,
        "from": f"{first}T00:00:00Z", "to": observed.isoformat()}}).encode()
    request = Request("https://api.github.com/graphql", data=payload, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "User-Agent": "SleepyLGod-Profile-Snapshot", "Accept": "application/vnd.github+json"})
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub activity API returned HTTP {error.code}; keeping the previous snapshot") from None
    if result.get("errors") or not (result.get("data") or {}).get("user"):
        raise ValueError("GitHub did not return a complete recent activity calendar")
    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    return normalize_recent_days(days, observed)


def summarize(snapshot):
    repos = snapshot["repositories"]
    return {"repos": len(repos), "stars": sum(repo["stars"] for repo in repos)}


def render_card(snapshot, theme, mobile=False):
    data = summarize(snapshot)
    palette = PALETTES[theme]
    width, height = (360, 64) if mobile else (760, 64)
    observed = datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00"))
    days = normalize_recent_days(snapshot["recent_days"], observed)
    contributions = sum(day["contributionCount"] for day in days)
    description = (f'{snapshot["username"]}: {contributions} contributions from {days[0]["date"]} '
                   f'through {days[-1]["date"]} UTC; {data["stars"]} stars earned by '
                   f'{data["repos"]} public, non-fork repositories, including archived repositories. '
                   f'Snapshot {observed.astimezone(HONG_KONG).date()} Hong Kong time. '
                   f'Sources: {snapshot["source"]}; {snapshot["recent_source"]}')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Recent Contributions and Stars</title>',
             f'<desc id="desc">{escape(description)}</desc>',
             f'<rect x="0.5" y="0.5" width="{width - 1}" height="63" rx="10" fill="{palette["background"]}" stroke="{palette["border"]}"/>',
             f'<path d="M{width // 2} 16v32" stroke="{palette["border"]}"/>',
             f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">']
    for index, (value, label) in enumerate(((contributions, "Contributions · 30 Days"), (data["stars"], "Stars"))):
        x = 90 + index * 180 if mobile else 132 + index * 380
        y, label_x, label_y = (29, x, 50) if mobile else (42, x + 16, 39)
        anchor = "middle" if mobile else "end"
        parts.append(f'<text x="{x}" y="{y}" font-size="{24 if mobile else 28}" text-anchor="{anchor}" font-weight="600" fill="{palette["dots"][0]}">{value:,}</text>')
        parts.append(f'<text x="{label_x}" y="{label_y}" font-size="{10.5 if mobile else 12}" text-anchor="{anchor if mobile else "start"}" fill="{palette["muted"]}">{label}</text>')
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
        observed = datetime.now(timezone.utc)
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        repos = fetch_repositories(args.username, token)
        recent_days = fetch_recent_days(args.username, observed, token)
        snapshot = {"version": 2, "username": args.username,
                    "captured_at": observed.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "recent_days": recent_days, "recent_source": "https://api.github.com/graphql",
                    "source": f"https://api.github.com/users/{args.username}/repos",
                    "repositories": sorted(repos, key=lambda repo: repo["name"].casefold())}
    write_atlas(args.output, snapshot)
    stats = summarize(snapshot)
    contributions = sum(day["contributionCount"] for day in snapshot["recent_days"])
    print(f'Updated profile snapshot: {contributions} contributions in 30 days, {stats["stars"]} stars')


if __name__ == "__main__":
    main()
