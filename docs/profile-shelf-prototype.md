# Selected projects preview

This branch contains the user's selected 13-project presentation, ready for
review against `main`. The current live profile has not been changed. The previous four suggested external repositories have been
replaced with Research (4), Toys / Tools (6), Teaching (1), and Skills (2). Research starts
with agent-memory, then aibrix, eos-predictor, and the not-yet-public vllm-sd.
Tools are sorted by descending Stars from the snapshot whenever the README is
rebuilt; ties preserve their configured order. Teaching follows, then Skills.
The image-only refresh keeps the source README's published order intact.

## Presentation

The contribution/Star summary is now one borderless line, 30 pixels high, below
the identity and research interests and before the contact links. Counts and
labels share the same baseline; there is no large number panel or footnote.
Desktop output is 520 pixels wide; the mobile variant is 360 pixels wide.

The project section uses one grid of 80-pixel cards, with category labels in
the lower-right corner instead of separate category headings. Public
cards retain a topic icon, repository name, one-line introduction, exact Stars
and Forks, and a native HTML link. Narrow screens wrap the cards to one column.
Descriptions were checked against the 12 public GitHub pages. The ETH arbitrage
project is described as experimental, matching its public repository description.

Primary language is intentionally omitted. The introduction and category explain
the purpose of these skills, tools, and research projects more directly than a
single language label, and keep the compact cards readable.

## Not-yet-public research

The user supplied the `vllm-sd` description: **Scheduling under agentic workload**
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

The README now references production `profile-assets` URLs. Project cards and
the new `profile-summary-*.svg` files are seeded there before review. The new
summary filenames leave the existing live `code-atlas-*.svg` cards untouched
until the README is merged. The workflow publishes future summaries under these
new names, while the source generator keeps its existing offline filenames.
Preview CI publications still use their own resource branch.

## Data scope

The strip counts contributions in the last 30 UTC calendar days (including the
current day) and Stars earned by public, non-fork account-owned repositories.
Those totals are separate from per-card counters, which cover the exact public
repository URLs the user selected, including their selected fork and organization
repository. Precise observation dates and source URLs are kept in JSON and SVG
accessible descriptions, with no visible date/footer clutter.

## Verified hosted refresh

[Run 42247297103](https://github.com/SleepyLGod/SleepyLGod/actions/runs/42247297103)
completed successfully for source commit `90a2fad`, running all 29 tests and
publishing the 13-project presentation. Its REST snapshot contains exactly the
12 public repositories; the closed entry is rendered from user-supplied config
without a metadata request or counts. The private-entry exclusion is also tested
with a network spy. The public GitHub preview has no closed-repository URL.
All image variants and the 30-pixel strip were checked in desktop light/dark
and narrow/mobile layouts. The live `main` profile was not changed.
