# Pour Score methodology

Internal notes on how the "Pour Score" shown on each wine card is calculated. Not shown on the site itself.

## Inputs

Only two numbers, both already visible on each card:
- Vivino rating (stars)
- Price (AUD)

## Steps

1. **Weight the rating.** Vivino scores cluster tightly in this price band (most sub-$30 wines sit around 3.6–3.9★), so each extra tenth of a star is treated as harder to earn. A step multiplier is applied based on score tier:

   | Score        | Multiplier |
   |--------------|-----------|
   | 4.2★ and up  | ×1.40     |
   | 4.0★ – 4.19★ | ×1.25     |
   | 3.8★ – 3.99★ | ×1.10     |
   | 3.6★ – 3.79★ | ×1.00     |
   | Below 3.6★   | ×0.92     |

2. **Divide by price.** `(rating × multiplier) / price` gives a raw quality-per-dollar ratio.

3. **Index against a fixed benchmark.** The raw ratio is compared to a hypothetical perfect 5.0★ wine at $20 (`(5.0 × 1.40) / 20 = 0.35`), then scaled to a 0–100 index: `(raw ratio / 0.35) × 100`. This keeps 100 tied to an absolute reference rather than whichever wine happens to top the current list — a wine could in theory score above 100 if it beats the benchmark outright.

Wines with no confirmed Vivino score get `pourScore: null` and are excluded from ranking/sorting by Pour Score.

## Current results

| Wine | Rating | Price | Multiplier | Pour Score |
|---|---|---|---|---|
| Vinha da Coutada Velha | 4.1★ | $18.99 | ×1.25 | 77 |
| Mike Press Shiraz | 3.7★ | $15.00 | ×1.00 | 70 |
| Tar & Roses Pinot Grigio | 3.9★ | $21.00 | ×1.10 | 58 |
| Pewsey Vale Eden Valley Riesling | 3.7★ | $22.99 | ×1.00 | 46 |
| Woodcutter's Shiraz (Torbreck) | 4.1★ | $29.00 | ×1.25 | 50 |
| The Footbolt Shiraz (d'Arenberg) | 3.8★ | $22.00 | ×1.10 | 54 |
| Dead Letter Office Shiraz (Farmer's Leap) | 4.0★ | $26.00 | ×1.25 | 55 |

## Why this design

- The tiered multiplier makes the score non-linear (higher star ratings are rewarded disproportionately) rather than a flat linear score/price ratio.
- The $20/5.0★ benchmark avoids the trap of a relative-to-max index, where the top wine in any given list is trivially always 100 regardless of how good it actually is.
- The reference price ($20) and multiplier bands are judgment calls, not derived from a larger dataset — revisit if the wine list grows or price range shifts materially.
