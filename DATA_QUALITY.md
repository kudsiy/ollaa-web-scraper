# Web data quality

State of the `web_listings` table in the `ollaa` database on 2 November 2026, after the
first multi-site scrape (task W16). This is the **web** dataset only; Ollaa-Telegram keeps
its own `DATA_QUALITY.md` for the Telegram data. All counts are read-only and can be
re-derived from the local load-ready file and the scraper logs.

## Where it comes from
Two sites whose rules allow it and whose prices are in birr: **BetDelala** and
**ethiopiarealty** (see `SITE_RECON.md`). The scrape is **not finished** — about 29% of the
two sitemaps so far — so these numbers grow as it continues within the daily cap.

## From scraped pages to loaded listings

| Step | Listings |
|---|---|
| Scraped so far (BetDelala 1,000 + ethiopiarealty 510) | 1,510 |
| Removed as within-site duplicates (same type + place + price + size) | 178 |
| **Loaded into `web_listings`** | **1,332** (BetDelala 864, ethiopiarealty 468) |
| Mapped to a real Addis sub-city | 806 (61%) |
| Sale / rent | 684 / 648 |
| **Usable for a hedonic model** (birr price + size + a real sub-city) | **790** |
| — of those, sale | 423 |

For comparison, the Telegram data has 476 sale listings ready for the model. The web data
adds **423 usable sale listings** on top, of which 87 look like the same property already on
Telegram (see Duplicates), so roughly **340 are new**.

## Duplicates

**Between websites (removed).** Rule, mirroring Ollaa-Telegram's: two listings are the same
advert when they share type, place, price and size; keep the most complete copy and remove
the rest; never merge copies whose price or size differ. This removed **178** within-site
repeats; none needed a decision, because every removed pair had identical price and size.
Cross-site identical matches: none (the two sites did not share an exact listing). The
removed rows are listed in `saved_pages/_load/web_dedup_removed.csv` (local).

**Between web and Telegram (flagged only, nothing changed).** Comparing `web_listings` with
the Telegram listings on the same sub-city code, price (±5%) and size (±5%): **87 web
listings look like a property already on Telegram.** They are flagged, not removed; the
Telegram tables were only read. List: `saved_pages/_load/web_telegram_matches.csv`.

## Accuracy

Sixty random usable listings were put next to their original adverts in
`saved_pages/_load/accuracy_check_60_web.html` (for the owner to check; contacts masked).
**Claude's own rough reading: 21 of 60 (35%) look wrong in at least one field** — close to
the Telegram data's own 33%. The commonest issues: the stored size is the building's land or
a floor count rather than the flat's area, and the property type (house vs apartment vs a
whole building) is read from a short title. The owner's check decides what is really wrong.

## Known limits
- **The scrape is ~29% done.** Totals will rise over the coming daily-capped runs.
- **Location** is strong for BetDelala and sparser for ethiopiarealty (its sub-city is in
  the listing text); 61% overall carry a real sub-city, the rest are only "Addis Ababa".
- **Size needs care**: for some adverts the number is the plot or the whole building, not
  the flat — the accuracy check will show how often.
- **Currency**: both loaded sites quote birr. realethio and ethiopianproperties (mostly US
  dollars) were deliberately left out of the load.
- These are **asking** prices from adverts, not sale prices.
