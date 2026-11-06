# Selected projects preview

This branch previews the user's explicit 13-project list. The live profile on
`main` is unchanged. The previous four suggested external repositories have been
replaced with Skills (2), Toys / Tools (6), Research (4), and Teaching (1), in the
user's requested order.

## Presentation

The contribution/Star summary is now one borderless line, 30 pixels high, below
the identity and research interests and before the contact links. Counts and
labels share the same baseline; there is no large number panel or footnote.
Desktop output is 520 pixels wide; the mobile variant is 360 pixels wide.

The project section has four visible group headings and 80-pixel cards. Public
cards retain a topic icon, repository name, one-line introduction, exact Stars
and Forks, and a native HTML link. Narrow screens wrap the cards to one column.
Descriptions were checked against the 12 public GitHub pages. The ETH arbitrage
project is described as experimental, matching its public repository description.

## Not-yet-public research

The user supplied the `vllm-sd` description: **Agentic scheduling on top of vLLM.**
Its config explicitly has `public: false`. It is shown as Not Yet Public with a
lock icon, without an anchor, external-link arrow, Star count, or Fork count.
The metadata updater skips it before constructing or requesting any API URL.
Only the user's supplied name and description are rendered; no private repository
was accessed. Tests verify that the closed entry makes no network request, gets
no invented zero counts, and cannot accidentally enter the public stats snapshot.

## Configuration and refresh

Edit `profile/recommendations.json`, then run `python scripts/build_repo_shelf.py`.
Each entry selects a category and vector topic icon. `public` defaults to true;
non-public entries require an explicit boolean false. All 13 cards have local
light and dark SVGs; `assets/recommendations/stats.json` contains only the 12
public repositories' observed counts and source URLs.

`--refresh` reads public metadata using GitHub REST. All selected public records
must validate before any output is replaced. Public repositories unexpectedly
becoming private, disappearing, or moving stop publication and preserve the last
good images. Entries intentionally marked non-public are never queried and do
not block a refresh. Ordinary offline rebuilds retain the observation time.

GitHub Actions refreshes both the recent-activity strip and project counters,
then publishes all images and both JSON snapshots in one ordinary Git commit.
The built-in `GITHUB_TOKEN` is enough. No extra card service, font CDN, or always-on
cloud computer is used.

- Preview source: `codex/profile-repo-shelf-20261106`.
- Preview image branch: `profile-shelf-preview-assets`.
- Production image branch: `profile-assets`.
- Preview triggers: relevant config/source pushes and manual dispatch.
- After deployment to `main`: daily at 06:37 Hong Kong time, plus those triggers.

GitHub may delay jobs or cache image responses. The last successful publication
continues to display if a refresh fails. The offline preview builder embeds
reviewed local copies of the same-repository image URLs.

Before a production merge, regenerate project image URLs with
`--asset-base https://raw.githubusercontent.com/SleepyLGod/SleepyLGod/profile-assets/assets/recommendations/`
and change the strip's four image URLs to the production resource branch.
Preview publications do not modify the current live profile.

## Data scope

The strip counts contributions in the last 30 UTC calendar days (including the
current day) and Stars earned by public, non-fork account-owned repositories.
Those totals are separate from per-card counters, which cover the exact public
repository URLs the user selected, including their selected fork and organization
repository. Precise observation dates and source URLs are kept in JSON and SVG
accessible descriptions, with no visible date/footer clutter.
