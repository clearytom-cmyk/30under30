#!/usr/bin/env python3
"""Fetch Vivino wine candidates above a rating threshold and under a price cap.

MANUAL, MANUAL-TRIGGER-ONLY TOOL. Do not wire this into CI, a cron job, or
anything that runs unattended or on a schedule — see VIVINO_API_NOTES.md for
why (Vivino's ToS prohibits automated access, and every third-party wrapper
we surveyed is built on undocumented endpoints that can change without
notice). Run it by hand, occasionally, review the output yourself, and
manually add anything worth keeping to the `wines` array in index.html —
this script does not touch index.html.

Calls Vivino's undocumented `api/explore/explore` endpoint directly (the
same approach as https://github.com/Piltxi/Vivino-Crawler, the best-suited
of the four third-party wrappers we assessed). It is not an official or
sanctioned API and may stop working at any time.

IMPORTANT — origin vs. currency vs. availability:
`--country-origin` filters by the wine's country of origin (where it's
made) — it does NOT confirm the wine is actually stocked/available for
purchase in any particular market. Vivino has no documented, verified way
to filter by retail availability in a specific country. `--currency` is a
best-effort attempt to get prices displayed in a specific currency
(untested — see VIVINO_API_NOTES.md); the script self-checks the first
result's actual currency against what you asked for and aborts loudly if
they don't match, rather than silently writing mismatched-currency prices
into the output labeled as something they're not. If you need results
priced in a currency other than the wine's native market currency and the
self-check fails, fetch in the native currency (omit --currency) and
convert manually with a rate you look up yourself — see
VIVINO_API_NOTES.md for the reasoning.

Usage:
    python scripts/fetch_vivino_wines.py --min-rating 3.7 --max-price 30 --country-origin au
    python scripts/fetch_vivino_wines.py --min-rating 4.0 --max-price 30 --country-origin pt --currency AUD
"""

import argparse
import json
import sys
import time

import requests

EXPLORE_URL = "https://www.vivino.com/api/explore/explore"

# A generic desktop-browser UA. Vivino's own frontend requires something
# realistic here or requests come back empty (per aptash/vivino-api's code
# comments) — this is not spoofing a specific real user or session.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

REQUEST_DELAY_SECONDS = 2
RESULTS_PER_PAGE = 25


def fetch_candidates(min_rating, max_price, country_origin, currency, max_pages):
    candidates = []
    page = 1
    currency_checked = False

    while page <= max_pages:
        params = {
            "country_codes[]": country_origin,
            "min_rating": min_rating,
            "price_range_min": 0,
            "price_range_max": max_price,
            "order_by": "ratings_average",
            "order": "desc",
            "page": page,
        }
        if currency:
            params["currency_code"] = currency

        try:
            response = requests.get(EXPLORE_URL, params=params, headers=HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            print(f"Request failed on page {page}: {exc}", file=sys.stderr)
            break
        except json.JSONDecodeError as exc:
            print(f"Could not parse response as JSON on page {page}: {exc}", file=sys.stderr)
            break

        matches = data.get("explore_vintage", {}).get("matches", [])
        if not matches:
            break

        for match in matches:
            candidate = _parse_match(match)
            if candidate is None:
                continue

            if currency and not currency_checked:
                currency_checked = True
                if candidate["currency"] != currency:
                    print(
                        f"ABORTING: requested --currency {currency} but Vivino returned "
                        f"prices in {candidate['currency']}. The currency_code param does not "
                        f"appear to work as hoped (this was flagged as unverified — see "
                        f"VIVINO_API_NOTES.md). Re-run without --currency to fetch in the "
                        f"wine's native market currency, then convert the results manually "
                        f"with a rate you look up yourself.",
                        file=sys.stderr,
                    )
                    return []

            candidates.append(candidate)

        if len(matches) < RESULTS_PER_PAGE:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return candidates


def _parse_match(match):
    vintage = match.get("vintage", {})
    wine = vintage.get("wine", {})
    winery = wine.get("winery", {})
    region = wine.get("region", {})
    stats = vintage.get("statistics", {})
    price = match.get("price", {})

    rating = stats.get("ratings_average")
    ratings_count = stats.get("ratings_count")
    amount = price.get("amount")

    if rating is None or amount is None:
        return None

    return {
        "wine": wine.get("name"),
        "producer": winery.get("name"),
        "region": region.get("name"),
        "country": region.get("country", {}).get("name"),
        "vintage_year": vintage.get("year"),
        "price": amount,
        "currency": price.get("currency", {}).get("code"),
        "score": rating,
        "ratings_count": ratings_count,
        "vivino_wine_id": wine.get("id"),
        "scoreSource": "Vivino",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-rating", type=float, default=3.7, help="Minimum Vivino rating (default: 3.7)")
    parser.add_argument("--max-price", type=float, default=30, help="Maximum price, in whatever currency the response ends up in (default: 30)")
    parser.add_argument("--country-origin", "--country", dest="country_origin", default="au", help="Vivino country_codes[] filter — the wine's country of origin (default: au)")
    parser.add_argument("--currency", default=None, help="Optional currency_code override, e.g. AUD. UNVERIFIED — the script aborts if Vivino doesn't actually honor it, rather than mislabeling prices.")
    parser.add_argument("--max-pages", type=int, default=20, help="Safety cap on pages fetched (default: 20)")
    parser.add_argument("--out", default="vivino_candidates.json", help="Output JSON file (default: vivino_candidates.json)")
    args = parser.parse_args()

    candidates = fetch_candidates(args.min_rating, args.max_price, args.country_origin, args.currency, args.max_pages)

    with open(args.out, "w") as f:
        json.dump(candidates, f, indent=2)

    price_label = args.currency or "(native currency)"
    print(f"Found {len(candidates)} wine(s) with origin={args.country_origin.upper()}, score >= {args.min_rating}, price <= {args.max_price} {price_label}.")
    print(f"Written to {args.out} — review before adding anything to index.html.")
    for c in sorted(candidates, key=lambda c: c["score"], reverse=True):
        print(f"  {c['score']:.1f}★  {c['price']} {c['currency']}  {c['wine']} ({c['producer']})")


if __name__ == "__main__":
    main()
