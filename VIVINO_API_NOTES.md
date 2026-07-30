# Vivino API exploration

Internal notes on whether the Vivino ratings/prices in `index.html` (currently
entered by hand, see `METHODOLOGY.md`) could be pulled programmatically
instead. Short answer: **no good way to do this exists — keep manual entry.**

## What's on github.com/Vivino

The official Vivino GitHub org (~40 repos) has no public API client, SDK, or
API documentation. Everything there is internal engineering infrastructure
for their own apps:

- `rankdb` (Go) — internal ranked-list server, not wine data
- `vivino-shared-spm` / `vivino-shared-spm-v2` (Swift) — shared modules for their iOS app
- `kotlin_multiplatform*` — internal Android/iOS proof-of-concept work
- `go-autocomplete-trie` (Go) — fuzzy-match/autocomplete data structure, likely used for their own wine-search-as-you-type, not exposed as a service
- A few forked third-party dependencies (not Vivino products)

There is no `vivino-api`, `vivino-sdk`, or anything linking to a developer
portal anywhere in the org.

## Official API status

- Vivino does not currently offer a public developer API. This is well
  corroborated, though the exact history (whether/when an earlier public API
  program existed and was shut down) couldn't be pinned to a primary source.
- They previously ran an **affiliate/referral program**, but that's a
  commerce link program, not a data feed, and is reportedly closed as of 2023.
- No path found for getting official, sanctioned API access for a small
  hobby project.

## Unofficial options (not recommended)

All third-party clients are reverse-engineered scrapers against undocumented
endpoints, and all are small and thinly maintained:

| Project | Notes |
|---|---|
| `aptash/vivino-api` (Node) | 3 commits total, minimal activity |
| `jonathanstathakis/vivino_api` (Python) | 3 commits, incomplete per author's own notes |
| `gugarosa/viviner` (Python) | **Archived since July 2024** |
| `Piltxi/Vivino-Crawler` (Python) | Small, low profile, no license |
| Apify marketplace scrapers | Paid scraping-as-a-service — same underlying ToS exposure, just outsourced |

None has meaningful community size or a stable public interface. Endpoints
can change without notice, which is presumably why several of these are
already dead.

## Legal/risk considerations

- Vivino's terms reportedly prohibit automated access ("scripts, browser
  plugins, spiders, robots, and scrapers") — could not load
  `vivino.com/legal/terms-of-service` directly to verify wording firsthand
  (403), but this is corroborated across multiple independent sources.
- Practical risks: undocumented endpoints break without notice (see the
  archived/abandoned projects above), IP blocking / CAPTCHA challenges on
  automated traffic, and general ToS exposure even for light personal use.

## Recommendation

For this site's actual scale — ~10–20 wines, updated occasionally, not
real-time or bulk — **don't build an automated integration.** The risk
(fragile scraper, ToS violation, possible IP block) isn't worth the
time saved over copy-pasting a rating by hand a few times a year.

If manual upkeep ever gets annoying, the lowest-risk middle ground is a
**local, hand-run, infrequent** script (not CI, not scheduled) that opens
each wine's already-known Vivino URL and parses the visible rating — same
as a human browsing the page, just automating the copy-paste. Even then,
keep it to occasional manual runs, not a build step or cron job.
