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
The script builds local light/dark SVGs and updates the marked README section.
Each card is its own native HTML link, so every repository remains clickable on
GitHub. There is no card server, image CDN, package install, or access token.

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
its counts are observed, not placeholders. The GraphQL path is covered by
mocked tests; a hosted Actions run must verify it when this design is deployed.

For this preview, README images reference the branch-local files. Before a
production merge, publish the new renderer's output to `profile-assets` and
restore the four existing same-repository resource-branch URLs. This keeps the
current live profile and its updater intact while the sample is reviewed.
