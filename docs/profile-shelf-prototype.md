# Repo Shelf prototype

This branch is a design preview. The live profile on `main` is unchanged.
The shelf uses manually chosen repositories rather than the account's pinned
projects or an automatically changing list of recent Stars. It is not limited
by GitHub's native pin count and can link to anyone's public repository.

## References checked on 2026-11-06

- [DenverCoder1's profile](https://github.com/DenverCoder1/DenverCoder1#-top-projects-ive-contributed-to)
  uses linked cards for repositories owned by other accounts. The `owner/repo`
  link, rather than the account's pins, determines which project appears.
- [lowlighter/metrics Stars plugin](https://github.com/lowlighter/metrics/tree/master/source/plugins/stars)
  generates a recently starred list in an SVG. This prototype uses a curated
  list so a new Star does not silently change what the profile recommends.
- [GitHub Readme Stats pin cards](https://github.com/anuraghazra/github-readme-stats#github-extra-pins)
  also accept arbitrary owners and repositories. Its README describes the
  public endpoint as best-effort and points to successors. No such endpoint is
  used here.

## Candidate selection

All four candidates were visible in
[SleepyLGod's public Stars](https://github.com/SleepyLGod?tab=stars) when checked.
Descriptions were checked against each project's public GitHub page. Being
starred is the selection evidence, not a claim about production use or a formal
endorsement. The user asked Codex to choose a sample.

| Candidate | Why it fits this sample |
| --- | --- |
| [feldera/feldera](https://github.com/feldera/feldera) | Incremental data processing and SQL. |
| [pola-rs/polars](https://github.com/pola-rs/polars) | DataFrame processing and query execution. |
| [deepseek-ai/DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) | GPU kernels for LLM infrastructure. |
| [Case3y/sleet-mono](https://github.com/Case3y/sleet-mono) | A lighter personal-interest choice: a programming typeface. |

Edit `profile/recommendations.json`, then run `python scripts/build_repo_shelf.py`.
Each entry has a category (`data`, `ai`, or `dev`) and topic icon. Cards are ordered
by category and show a small category label, a vector topic icon, exact Stars,
exact Forks (including zero), and the repository's one-line introduction. The
compact two-column layout remains, wrapping to one column on narrow screens.
Each 94-pixel card is its own native HTML link to the public repository.

`assets/recommendations/stats.json` records counts, source URLs, and the original
observation time. `--refresh` reads all selected public repositories from GitHub
REST, validates every response, and renders all light/dark cards before replacing
any cached file. Missing, private, or renamed repositories fail the refresh;
partial data never overwrites the last successful snapshot. Ordinary offline
rebuilds preserve the observation time and need no token.

## Automatic refresh

The existing workflow now refreshes both the personal contribution/Star strip
and all recommended repositories' Stars/Forks. It generates in temporary folders
and publishes all images and both JSON snapshots in a single ordinary Git commit.
The built-in `GITHUB_TOKEN` is enough; no additional secret or card service is
used. Public page imports supplied the initial recommendation counts; hosted
refreshes use the structured GitHub API instead of parsing rounded display text.

- Preview source: `codex/profile-repo-shelf-20261106`.
- Preview image branch: `profile-shelf-preview-assets`, initialized before use.
- Production image branch: `profile-assets`, separate from the preview.
- Triggers: relevant source/config pushes and manual workflow dispatch.
- After deployment to `main`, the existing daily schedule refreshes everything at
  06:37 Hong Kong time. GitHub can delay scheduled jobs and image caches.

The preview README already references the live preview image branch. The local
preview builder embeds reviewed local copies of these images and keeps previews
self-contained. On a production merge, regenerate the shelf using
`--asset-base https://raw.githubusercontent.com/SleepyLGod/SleepyLGod/profile-assets/assets/recommendations/`
and change the strip's four image URLs to the same production resource branch.
The two publication targets keep preview updates from modifying the live profile.

## Two-metric snapshot

The prototype replaces the language constellation with a 64-pixel strip:
**contributions in the last 30 UTC calendar days**, including today, and **Stars
earned by public, non-fork repositories** (including archived repositories).
There is no visible heading, language legend, date, or footnote. Exact dates,
source URLs, and repository scope remain in the SVG's accessible description
and the JSON snapshot. Today's contribution count can still change.

Snapshot version 2 requires all 30 days. Production refresh reads the repository
list from GitHub REST and the contribution calendar from GitHub GraphQL. Both
must succeed before any previous image is replaced. The preview was populated
from complete official public repository and contribution-calendar pages;
its counts are observed, not placeholders. GitHub Actions verifies the REST and GraphQL fetches together; failure of either
source preserves the prior publication.

## Verified hosted refresh

[Run 42243033770](https://github.com/SleepyLGod/SleepyLGod/actions/runs/42243033770)
completed successfully for source commit `8ef77a9`. It fetched recent activity
through GitHub GraphQL, public repository data through REST, and each of the
four recommendations' exact Stars/Forks. It published the complete image set
and both snapshots to `profile-shelf-preview-assets` as a bot commit. The live
profile's `main` and production `profile-assets` were not changed.
