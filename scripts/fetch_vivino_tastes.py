#!/usr/bin/env python3
"""Fetch Vivino taste-profile data for wines already identified by ID.

MANUAL, MANUAL-TRIGGER-ONLY TOOL. Same caveats as fetch_vivino_wines.py —
see VIVINO_API_NOTES.md. Do not wire this into CI or a schedule.

Calls the undocumented `api/wines/{id}/tastes` endpoint. This endpoint is
referenced by the gugarosa/viviner wrapper (see VIVINO_API_NOTES.md) but
its actual response shape has never been observed from this codebase —
we could not reach vivino.com from the sandbox this was written in to
verify it. So this script deliberately does NOT try to parse specific
taste dimensions (sweetness/body/acidity/etc.) out of the response — it
just fetches and saves the RAW JSON per wine ID, so the actual shape can
be inspected before anyone writes parsing/merging logic against it. If
the endpoint returns something unexpected (404, different shape, or
nothing useful), that's exactly what this script is meant to surface.

Requires wine IDs you already trust — either from a previous
fetch_vivino_wines.py run's vivino_candidates.json (it includes
`vivino_wine_id` per match), or a hand-picked list. Do not guess IDs.

Usage:
    python scripts/fetch_vivino_tastes.py --ids 10143990,11798,1636879
    python scripts/fetch_vivino_tastes.py --ids-file wine_ids.txt
"""

import argparse
import json
import sys
import time

import requests

TASTE_URL_TEMPLATE = "https://www.vivino.com/api/wines/{id}/tastes"

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


def fetch_tastes(wine_ids):
    results = {}
    for wine_id in wine_ids:
        url = TASTE_URL_TEMPLATE.format(id=wine_id)
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            results[str(wine_id)] = response.json()
        except requests.exceptions.RequestException as exc:
            print(f"Request failed for wine {wine_id}: {exc}", file=sys.stderr)
            results[str(wine_id)] = {"error": str(exc)}
        except json.JSONDecodeError as exc:
            print(f"Could not parse JSON for wine {wine_id}: {exc}", file=sys.stderr)
            results[str(wine_id)] = {"error": "invalid JSON response"}

        time.sleep(REQUEST_DELAY_SECONDS)

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ids", help="Comma-separated Vivino wine IDs")
    parser.add_argument("--ids-file", help="Path to a file with one Vivino wine ID per line")
    parser.add_argument("--out", default="vivino_tastes.json", help="Output JSON file (default: vivino_tastes.json)")
    args = parser.parse_args()

    ids = []
    if args.ids:
        ids.extend(x.strip() for x in args.ids.split(",") if x.strip())
    if args.ids_file:
        with open(args.ids_file) as f:
            ids.extend(line.strip() for line in f if line.strip())
    if not ids:
        parser.error("Provide --ids or --ids-file with at least one Vivino wine ID")

    results = fetch_tastes(ids)

    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)

    ok = sum(1 for v in results.values() if "error" not in v)
    print(f"Fetched {ok}/{len(ids)} wine(s) successfully. Written to {args.out}.")
    print("This endpoint's response shape is unverified — inspect the raw output before we write any parsing/merge logic against it.")


if __name__ == "__main__":
    main()
