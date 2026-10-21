# Repository-hosted profile assets

The README loads all images from this repository. Viewing the profile does not
call a typing-animation service, badge server, statistics-card deployment, or icon CDN.
Ordinary links to a homepage, documentation, LinkedIn, and Spotify still open those sites.

## What updates automatically

`.github/workflows/calendar.yml` runs daily at approximately **06:17 Hong Kong
time**, on manual dispatch, and when the generator changes on `main`.
GitHub may delay schedules and may disable scheduled workflows in inactive public repositories.

The workflow uses the built-in `GITHUB_TOKEN` to read publicly visible contribution
data from GitHub's GraphQL API and commit four SVG files under `assets/profile/`.
No personal access token, `METRICS_TOKEN`, separate server, or third-party card
deployment is required. The workflow needs repository permission to write contents.

The cards cover the last **365 UTC dates**. A contribution follows GitHub's calendar
definition; it is not a commit count. Streaks are calculated within that window.
A zero-count day still in progress does not break yesterday's current streak.
Private contribution visibility is limited by the token and GitHub's public calendar settings.
Each snapshot displays its date. Failed fetches or invalid/partial calendars leave
the previous checked-in cards available.

## Generate or check locally

Python 3.12 and its standard library are sufficient:

```sh
python -m unittest discover -s tests -v
python scripts/update_profile.py --username SleepyLGod
```

To build an animated, standalone preview using an installed Pandoc:

```sh
python scripts/render_preview.py --output /tmp/sleepylgod-profile.html
```

Open the resulting HTML file in a browser. Its images and styles are embedded;
it needs no server, cloud session, or external widget service to display.

The second command uses an existing `GH_TOKEN` or `GITHUB_TOKEN` binding. Never put
a token in the README or command arguments. The cloud environment currently blocks
`api.github.com`; that cloud-specific restriction is separate from GitHub Actions.

The initial checked-in snapshot was generated from the exact daily counts in
GitHub's official public calendar HTML. To reproduce that import without API credentials:

```sh
curl --fail --location --output /tmp/calendar-previous.html \
  'https://github.com/users/SleepyLGod/contributions?from=2025-01-01&to=2025-12-31'
curl --fail --location --output /tmp/calendar-current.html \
  'https://github.com/users/SleepyLGod/contributions?from=2026-01-01&to=2026-12-31'
python scripts/update_profile.py --username SleepyLGod \
  --calendar-html /tmp/calendar-previous.html /tmp/calendar-current.html
```

Use the current and previous calendar years when refreshing in a later year.
The importer rejects missing dates and unrecognized counts rather than fabricating data.
Automatic Actions updates use the supported API rather than the HTML importer.

## Static assets and optional services

- The animated SVG header and existing lo-fi GIF are local files. SVG animation
  does not execute JavaScript. Reduced-motion preferences are respected by the header.
- Tool icons are vendored at pinned versions; see `assets/icons/README.md` for sources.
- Live Spotify listening activity requires Spotify OAuth credentials. The README
  uses an official Spotify profile link until such an integration is explicitly configured.
- A true visitor counter requires a request-counting service. A static repository
  snapshot cannot count page visits, so the unreliable external counter was removed.
- Codex cloud sessions are used for editing and previewing. The public profile is
  served by GitHub and continues displaying checked-in assets when the cloud session ends.

To publish this design on the profile, merge the README, assets, generator, tests,
and workflow into the default branch of `SleepyLGod/SleepyLGod`. Open **Actions →
Refresh profile assets → Run workflow** to check the first live update.
