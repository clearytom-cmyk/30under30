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

### Deeper look at each one

Read the actual source (not just repo metadata) for all four:

- **`aptash/vivino-api`** (Node) — drives headless Chrome via Puppeteer and
  scrapes CSS classes off Vivino's rendered search page (no direct JSON API
  call for wine data, beyond a `PUT /api/ship_to/` to localize
  pricing/currency). Returns rating + review count from name search only, no
  wine ID or vintage lookup. One-off CLI script, not an importable library.
  Last commit Nov 2020 — the most fragile of the four to a frontend redesign.
- **`jonathanstathakis/vivino_api`** (Python) — calls the real
  `api/explore/explore` endpoint with the most complete documented filter
  params of the four. But it **never extracts a rating field** into its
  output despite filtering by `ratings_min`/`ratings_max`, has a real bug
  (`get_request()` reads a module-level global `params` instead of
  `self.params`), and importing the module executes a live network call and
  drops into an interactive `IPython.embed()` shell — unsafe to import as-is.
  Freshest commit of the four (Feb 2025), which is at least a signal the
  endpoint was still responding recently.
- **`gugarosa/viviner`** (Python) — cleanest file structure of the four
  (separate `utils/constants.py`, `utils/requester.py`, argparse CLIs), and
  hits three real endpoints (`explore/explore`, `wines/{id}/tastes`,
  `wines/{id}/reviews`) for the most complete data pull. But it sends a
  **literal blank `User-Agent` header** on every request, which the other
  repos' own code comments suggest is exactly what gets requests blocked.
  **Archived by its maintainer since July 2024.**
- **`Piltxi/Vivino-Crawler`** ("WineTz", Python) — calls `explore/explore`
  plus a per-wine `wines/{id}/reviews` endpoint, and is the **only one of the
  four that explicitly extracts `vintage.statistics.ratings_average` and
  `ratings_count`** — exactly the fields this site needs. Uses a real spoofed
  User-Agent, has genuine error handling (`raise_for_status()`, typed
  exceptions, graceful partial-save on Ctrl+C). Structured as a CLI tool
  across a few files rather than a library, but the core functions
  (`wineCrawler()`/`getWine()`) look straightforward to lift out. Last
  commit Jan 2024; very low visibility (2 stars, no issues either way on
  current status).

**If experimenting with any of these purely for personal/experimental
lookups** (separate from the ToS risk already noted below): `Piltxi/Vivino-Crawler`
is the best-positioned technically — clearest match to the data this site
needs, most defensive code. Worth a quick sanity check that
`api/explore/explore` still returns real data before investing time (it's
undocumented and could change anytime). **Avoid `gugarosa/viviner`**
(archived, blank User-Agent) and **`aptash/vivino-api`** (stale since 2020,
brittle CSS-dependent scrape, no ID/vintage lookup) outright. None of the
four demonstrate clean AUD-specific pricing — the country/currency params
would need testing directly rather than assuming from these repos'
Italy/Brazil/US-centric examples.

## Reusable fetch script

`scripts/fetch_vivino_wines.py` implements the `Piltxi/Vivino-Crawler`
approach (calls `api/explore/explore` directly, extracts
`ratings_average`/`ratings_count`/price) as a standalone script.

**Manual trigger only — not wired into the site, CI, or any schedule.**
Run it by hand, review the output, and manually copy anything worth keeping
into the `wines` array in `index.html` (matching the existing fields —
`wine`, `producer`, `region`, `regionGroup`, `variety`, `type`, `price`,
`score`, `scoreSource`, `notes`). The script itself never touches
`index.html`.

```
pip install requests
python scripts/fetch_vivino_wines.py --min-rating 3.7 --max-price 30 --country au
```

Writes matches to `vivino_candidates.json` (gitignored — it's fetch output,
not curated content) and prints a summary to stdout.

Note: this could not be executed or tested from the sandbox this repo was
developed in — that environment's own network egress policy blocks
`www.vivino.com` outright (separate from anything Vivino itself does). It
needs to be run from an environment with normal internet access. Since the
endpoint is undocumented, sanity-check that it still returns real data
before relying on it (see the freshness caveats above).

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
