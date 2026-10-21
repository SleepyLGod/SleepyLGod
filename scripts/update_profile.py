#!/usr/bin/env python3
"""Generate repository-hosted profile cards using only Python's standard library."""

import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PALETTES = {
    "dark": ("#0d1117", "#30363d", "#e6edf3", "#9198a1", ("#21262d", "#35234f", "#623c91", "#9665d4", "#c4a0ff")),
    "light": ("#ffffff", "#d1d9e0", "#1f2328", "#656d76", ("#ebedf0", "#ede3fa", "#c9aaed", "#9866cb", "#7442a8")),
}


def period(today):
    return today - timedelta(days=364), today


def normalize_days(days, today):
    start, end = period(today)
    selected = {}
    for day in days:
        day_date = date.fromisoformat(day["date"])
        count = day["contributionCount"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("Contribution counts must be nonnegative integers")
        if start <= day_date <= end:
            if day_date in selected:
                raise ValueError(f"Duplicate contribution date: {day_date}")
            selected[day_date] = count
    expected = [start + timedelta(days=index) for index in range(365)]
    if set(selected) != set(expected):
        raise ValueError("Expected a complete calendar of 365 days; refusing partial data")
    return [(day, selected[day]) for day in expected]


def fetch_days(username, today, token):
    if not token:
        raise ValueError("Set GH_TOKEN or GITHUB_TOKEN, or import saved public calendar HTML")
    start, _ = period(today)
    query = """query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    payload = json.dumps({"query": query, "variables": {
        "login": username, "from": f"{start}T00:00:00Z",
        "to": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }}).encode()
    request = Request("https://api.github.com/graphql", data=payload, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "User-Agent": "repository-profile-assets", "Accept": "application/vnd.github+json",
    })
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code}") from None
    if result.get("errors") or not result.get("data", {}).get("user"):
        raise ValueError("GitHub did not return a complete contribution calendar")
    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [day for week in calendar["weeks"] for day in week["contributionDays"]]


class PublicCalendarParser(HTMLParser):
    """Import an explicitly downloaded public calendar for an initial snapshot."""

    def __init__(self):
        super().__init__()
        self.dates = {}
        self.counts = {}
        self.tooltip = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-date") and attrs.get("id"):
            self.dates[attrs["id"]] = attrs["data-date"]
        if tag == "tool-tip" and attrs.get("for"):
            self.tooltip = attrs["for"]
            self.parts = []

    def handle_data(self, data):
        if self.tooltip:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tooltip:
            text = " ".join("".join(self.parts).split())
            match = re.match(r"([\d,]+) contributions? on\b", text)
            if text.startswith("No contributions on "):
                self.counts[self.tooltip] = 0
            elif match:
                self.counts[self.tooltip] = int(match[1].replace(",", ""))
            self.tooltip = None

    def days(self):
        if not self.dates or set(self.dates) - set(self.counts):
            raise ValueError("Public calendar markup is incomplete or has changed")
        return [{"date": day, "contributionCount": self.counts[key]}
                for key, day in self.dates.items()]


def import_calendars(paths):
    days = []
    for path in paths:
        parser = PublicCalendarParser()
        parser.feed(Path(path).read_text())
        days.extend(parser.days())
    return days


def statistics(days):
    counts = [count for _, count in days]
    longest = run = 0
    for count in counts:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # An unfinished day with no contributions does not end yesterday's streak.
    index = len(counts) - 1 if counts[-1] else len(counts) - 2
    current = 0
    while index >= 0 and counts[index]:
        current += 1
        index -= 1
    return (sum(counts), sum(count > 0 for count in counts), longest, current)


def svg_frame(title, height, palette):
    background, border, foreground, muted, _ = palette
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title>',
            '<desc id="desc">Publicly visible GitHub contributions over the last 365 days. Streak lengths are limited to this period.</desc>',
            f'<rect x="0.5" y="0.5" width="759" height="{height - 1}" rx="14" fill="{background}" stroke="{border}"/>',
            f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" fill="{foreground}">']


def summary_svg(username, days, theme):
    palette = PALETTES[theme]
    muted = palette[3]
    svg = svg_frame(f"{username}: contribution statistics", 158, palette)
    svg += [f'<text x="28" y="30" font-size="11" letter-spacing="2" fill="{muted}">GITHUB / LAST 365 DAYS</text>',
            f'<text x="732" y="30" text-anchor="end" font-size="11" fill="{muted}">Updated {days[-1][0]} UTC</text>']
    labels = ("Contributions", "Active days", "Longest streak", "Current streak")
    for index, (number, label) in enumerate(zip(statistics(days), labels)):
        x = 28 + index * 186
        svg += [f'<text x="{x}" y="86" font-size="34" font-weight="600" fill="{palette[4][-1]}">{number:,}</text>',
                f'<text x="{x}" y="113" font-size="12" fill="{muted}">{label}</text>']
    svg += ['</g></svg>']
    return "\n".join(svg) + "\n"


def calendar_svg(username, days, theme):
    palette = PALETTES[theme]
    muted, colors = palette[3], palette[4]
    first_monday = days[0][0] - timedelta(days=days[0][0].weekday())
    svg = svg_frame(f"{username}: contribution calendar", 186, palette)
    svg += [f'<text x="28" y="28" font-size="13" font-weight="600">A year of building</text>',
            f'<text x="732" y="28" text-anchor="end" font-size="11" fill="{muted}">{days[0][0]} – {days[-1][0]}</text>']
    for day, count in days:
        column = (day - first_monday).days // 7
        x, y = 42 + column * 13, 59 + day.weekday() * 13
        if day.day == 1:
            svg.append(f'<text x="{x}" y="49" font-size="9" fill="{muted}">{day.strftime("%b")}</text>')
        level = 0 if count == 0 else min(4, 1 + (count - 1) // 3)
        svg.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{colors[level]}"><title>{day}: {count} contributions</title></rect>')
    for weekday, label in ((0, "M"), (2, "W"), (4, "F")):
        svg.append(f'<text x="23" y="{67 + weekday * 13}" font-size="9" fill="{muted}">{label}</text>')
    svg.append(f'<text x="42" y="170" font-size="10" fill="{muted}">Public GitHub activity · daily snapshot</text>')
    svg.append(f'<text x="594" y="170" font-size="9" fill="{muted}">Less</text>')
    for index, color in enumerate(colors):
        svg.append(f'<rect x="{621 + index * 13}" y="162" width="10" height="10" rx="2" fill="{color}"/>')
    svg += [f'<text x="691" y="170" font-size="9" fill="{muted}">More</text>', '</g></svg>']
    return "\n".join(svg) + "\n"


def write_cards(output, username, days):
    # Fetch, validate and render every card before touching the last good snapshot.
    cards = {}
    for theme in PALETTES:
        cards[f"activity-{theme}.svg"] = summary_svg(username, days, theme)
        cards[f"calendar-{theme}.svg"] = calendar_svg(username, days, theme)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temp:
        for name, content in cards.items():
            (Path(temp) / name).write_text(content)
        for name in cards:
            os.replace(Path(temp) / name, output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="SleepyLGod")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "assets/profile")
    parser.add_argument("--calendar-html", type=Path, nargs="+", help="Import official public calendar HTML instead of calling the API")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", args.username):
        parser.error("Invalid GitHub username")
    today = datetime.now(timezone.utc).date()
    raw = import_calendars(args.calendar_html) if args.calendar_html else fetch_days(
        args.username, today, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    days = normalize_days(raw, today)
    write_cards(args.output, args.username, days)
    print(f"Updated four profile cards for {args.username}: {days[0][0]} to {days[-1][0]}")


if __name__ == "__main__":
    main()
