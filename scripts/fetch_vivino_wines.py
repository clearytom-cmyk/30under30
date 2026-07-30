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

Usage:
    python scripts/fetch_vivino_wines.py --min-rating 3.7 --max-price 30 --country au
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


def fetch_candidates(min_rating, max_price, country_code, max_pages):
    candidates = []
    page = 1

    while page <= max_pages:
        params = {
            "country_codes[]": country_code,
            "min_rating": min_rating,
            "price_range_min": 0,
            "price_range_max": max_price,
            "order_by": "ratings_average",
            "order": "desc",
            "page": page,
        }

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
            if candidate is not None:
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
    parser.add_argument("--max-price", type=float, default=30, help="Maximum price in the target market's currency (default: 30)")
    parser.add_argument("--country", default="au", help="Vivino country code to localize pricing against (default: au)")
    parser.add_argument("--max-pages", type=int, default=20, help="Safety cap on pages fetched (default: 20)")
    parser.add_argument("--out", default="vivino_candidates.json", help="Output JSON file (default: vivino_candidates.json)")
    args = parser.parse_args()

    candidates = fetch_candidates(args.min_rating, args.max_price, args.country, args.max_pages)

    with open(args.out, "w") as f:
        json.dump(candidates, f, indent=2)

    print(f"Found {len(candidates)} wine(s) matching score >= {args.min_rating} and price <= {args.max_price} {args.country.upper()}.")
    print(f"Written to {args.out} — review before adding anything to index.html.")
    for c in sorted(candidates, key=lambda c: c["score"], reverse=True):
        print(f"  {c['score']:.1f}★  {c['price']} {c['currency']}  {c['wine']} ({c['producer']})")


if __name__ == "__main__":
    main()
