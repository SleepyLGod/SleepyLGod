# Profile visuals and optional services

Every visible README image is a checked-in repository file. Viewing the profile
requires no third-party card endpoint, icon CDN, web font, or running Codex session.
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

The HTML embeds its images and styles. Comments in the README are excluded from
the preview, including their images. Screenshots under `docs/previews/` show the
reviewed desktop light/dark and mobile layouts.

## GitHub statistics

The visible **Code Atlas** is a language constellation, not a contribution
calendar. Each colored dot is one public, non-fork repository owned by this
account, including archived repositories. Colors group repositories by their
primary language; this measures repository counts, not code bytes or proficiency.
The three most common languages are named, the others share one group, and
repositories with no detected primary language have an Unclassified group.
Stars Earned sums those same repositories' stars; Primary Languages counts
distinct detected primary languages. Organization repositories are not included.

The four committed SVGs cover desktop/mobile and dark/light themes. The compact
desktop card is 760 × 224; the 360 × 324 mobile card places the orbit beside the
two metrics, with the language legend below. A committed
`assets/profile/code-atlas.json` records the complete public source data, source
URL, and observation time. The card displays its snapshot date in Hong Kong time.
The initial snapshot was imported from the official public repository list,
including all 24 results of its `type=source` filter. No estimated stats are used.

`Refresh Code Atlas` fetches the official GitHub REST API using the workflow's
built-in `GITHUB_TOKEN`. No personal access token or external deployment is needed.
After merging to `main`, it runs on relevant code changes, on manual dispatch, and
daily at 06:37 Hong Kong time (GitHub may delay scheduled runs). It commits only
the atlas snapshot and SVGs. A failed fetch, validation, or render leaves the
previous images and observation date intact. The profile always reads committed
files, never a live card endpoint. The workflow has been linted locally; an actual
Actions run still needs to execute on GitHub.

```sh
python -m unittest discover -s tests -v
python scripts/update_code_atlas.py --username SleepyLGod
python scripts/update_code_atlas.py --snapshot assets/profile/code-atlas.json
```

The second command fetches fresh data using an existing `GH_TOKEN` or
`GITHUB_TOKEN` if present. The last command rebuilds offline and preserves the
original snapshot date. The managed cloud environment blocks `api.github.com`,
so it was used only for the initial public-page import and offline rendering.

The older contribution calendar and streak cards remain commented out because
they repeat GitHub's native contribution section. Their generator, tests,
manual-only workflow, and previous snapshot are retained for future use.

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
scopes and card types it actually needs before enabling it. The current Code Atlas
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
