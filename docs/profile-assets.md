# Profile visuals and optional services

Every visible README image is checked into this repository. The live automatically
refreshed statistics live on the `profile-assets` branch; this design preview
uses branch-local snapshots. Other images use `main` in production. Viewing the profile requires no third-party card endpoint, icon CDN, web
font, or running Codex session.
The identity and research interests appear first; awards, founder details,
Selected Projects, and activity cards are preserved in HTML comments.

## Header, icons, and previews

The greeting says **Hi There!** and contains no personal name. Dancing Script
letter outlines are stored in the SVG, so visitors need no font installation.
The original cursive PhD line is retained as text. The font and its SIL Open Font
License are under `assets/fonts/`.

To rebuild the greeting with an installed `fonttools` package:

```sh
python scripts/build_header.py
```

The complete toolbox uses the original readme-components presentation: black
rounded badges, purple logos, and a four-second linear spin. Its original layout
and CSS are cached locally with their MIT license. No Vercel endpoint is used.
Reduced-motion preferences disable the animation. The local lo-fi GIF is unchanged.

To rebuild all cached badges using only Python's standard library:

```sh
python scripts/build_tool_icons.py
```

See `assets/icons/README.md` for sources, the pinned upstream commit, and licenses.

To build a standalone, animated preview with an installed Pandoc:

```sh
python scripts/render_preview.py --output /tmp/sleepylgod-profile.html
```

The HTML embeds its images and styles. Code Atlas's same-repository URLs are
mapped to the reviewed local snapshot for offline previews. Other external image
URLs are rejected. Comments in the README are excluded from
the preview, including their images. Screenshots under `docs/previews/` show the
reviewed desktop light/dark and mobile layouts.

## Profile statistics and repository shelf (preview)

This design branch uses a 64-pixel strip with two values: contributions in the
last 30 UTC calendar days (including today), and Stars earned by public,
non-fork repositories, including archived repositories. It has no visible
language groups, orbit, snapshot date, or footnote. Exact dates and scope are
preserved in the SVG description and version-2 JSON snapshot.

The current prototype snapshot was imported from complete official public
repository and contribution-calendar pages. Live refresh uses GitHub REST for
repositories and GitHub GraphQL for contributions with the workflow's built-in
`GITHUB_TOKEN`. Both sources are validated before writing any image; API errors
or missing dates leave the last successful snapshot untouched.

```sh
python -m unittest discover -s tests -v
python scripts/update_code_atlas.py --username SleepyLGod
python scripts/update_code_atlas.py --snapshot assets/profile/code-atlas.json
python scripts/build_repo_shelf.py
```

The offline rebuild keeps the original observation date. Snapshot version 2
requires a complete 30-day activity window rather than inventing a contribution
count from a version-1 repository-only snapshot. The managed cloud environment
blocks `api.github.com`; the hosted refresh path is covered by mocked tests and
must be exercised on GitHub when this design is deployed.

The shelf uses local light/dark linked cards generated from
`profile/recommendations.json`. Names and one-line descriptions are the only
visible card content. Every repository is its own native HTML link. See
[the prototype notes](profile-shelf-prototype.md) for researched examples, source
checks, selection rationale, and deployment instructions.

This preview references branch-local statistics to avoid changing the current
live profile. The production publication workflow still writes to the dedicated
`profile-assets` branch daily at 06:37 Hong Kong time. Restore the existing raw
resource-branch URLs after publishing the new output when deploying this design.
The old contribution calendar and streak cards remain commented out, with their
manual-only generator and tests retained.

### Reusing an upstream renderer

Running another project's renderer under your own control is possible. Prefer
**a pinned renderer in GitHub Actions → SVG files committed to this repository**.
Readers then see the last successful file even when the next refresh fails.
An always-on server adds deployment and availability work and is unnecessary for
periodically refreshed profile statistics.

The original [github-readme-stats README](https://github.com/anuraghazra/github-readme-stats#readme)
currently says the repository is no longer maintained, recommends successor
projects, and explicitly calls the shared public endpoint best-effort. It also
documents an [Actions-based generation workflow](https://github.com/anuraghazra/github-readme-stats#github-actions).
Choose a maintained successor, review and pin its version, and check which token
scopes and card types it actually needs before enabling it. The current snapshot
uses a small standard-library renderer in this repository.

Self-hosting reduces dependence on somebody else's deployment. GitHub API policy,
rate limits, token expiration, and upstream maintenance can still affect refreshes.
A dated cached image remains available, but its data can become stale.

## Spotify

The visible profile currently links to the official Spotify profile. It does not
load a shared Spotify widget or display fabricated listening data.

The upstream [spotify-github-profile README](https://github.com/kittinan/spotify-github-profile#readme)
documents a move from the old Vercel endpoint to a separately hosted endpoint.
Its full service includes OAuth and token storage, so copying its public image URL
does not create an independently hosted integration.

For this single-user profile, the recommended future integration is an authorized
**recently played snapshot**, generated by Actions and committed as a local SVG.
It should display the snapshot date, cache cover art if used, and retain the last
successful image on a failed refresh. It should not claim to be live playback.
Actions scheduling is periodic and may be delayed.

That integration still needs a Spotify application and OAuth authorization. No
Spotify client or refresh-token binding is present in the current cloud environment.
If enabled later, store the following in the GitHub repository's Actions secrets,
never in chat, README text, or version-controlled files:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REFRESH_TOKEN`

A Spotify updater has not been installed or authenticated. The current profile
needs none of those secrets to render correctly.
