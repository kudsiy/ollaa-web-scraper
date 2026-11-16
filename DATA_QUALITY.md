# Web data quality

State of the `web_listings` table in the `ollaa` database on 2 November 2026, after the
first multi-site scrape (task W16). This is the **web** dataset only; Ollaa-Telegram keeps
its own `DATA_QUALITY.md` for the Telegram data. All counts are read-only and can be
re-derived from the local load-ready file and the scraper logs.

> **Warning (found 13 November 2026, `THESIS_DATA_CHECK.md`):** every **ethiopiarealty**
> row has the same wrong price, **3,433 birr**, and the label "rent" (468 rows in
> `web_listings`, all 657 in the local file, and the first pilot too). The price reader
> picks up a number shown on every page of that site. Its size, bedrooms and place are fine;
> its price and sale/rent label must not be used. The **423 usable sale listings** below are
> all BetDelala and are not affected; the "790 usable" total wrongly includes ethiopiarealty
> rows.
>
> **Fixed the same evening:** the reader now takes the price from the page's "Details" box
> (checked on one approved live page: 19,000,000 birr, For Sale) and ignores search forms.
> The 468 database rows are flagged `price_unusable = TRUE` with a `price_note`, so every
> query should add `WHERE NOT price_unusable`. They stay flagged until re-scraped with the
> fixed reader (needs approval); the 709 ethiopiarealty rows in the local `full.csv` are
> old-reader rows too, and the loader flags them automatically if they are ever loaded.

## New columns (13 November 2026)

`web_listings` now also has: `reader` (which reader version read the page; empty = old
reader), `price_unusable` / `price_note`, `ad_text_masked` (the advert's text with every
phone number, e-mail and chat handle replaced by `<contact>`), and the off-plan terms read
from that text: `developer`, `construction_status`, `construction_progress_pct`,
`finish_level`, `down_payment_pct`, `down_payment_amount`, `instalment_plan`,
`stage_linked`, `bank_loan`, `handover`, `discount_schedule`, `stated_price_per_m2`,
`price_per_m2_semi`, `price_per_m2_full`, `has_payment_terms`. They are empty for the
1,332 rows loaded before; they fill as pages are read with the new reader. Unmasked phone
numbers are never stored: the text is masked by the scraper and again by the loader.

Later the same night (owner's corrections): `neighbourhood`, `sub_city_unsure` (sub-city
taken from `data/neighbourhood_subcity.csv`, where the owner's column wins),
`property_group` (adverts of the same property share it) and `exact_repeat` (an older row
that turned out to be a repeat copy of a fuller advert: flagged, never deleted). The view
`web_offplan_properties` gives one row per property with all its adverts' terms together.

## State on 13 November 2026, 22:46 (after the second load)

Backup first (`backups/ollaa_2026-11-13c.dump`, checked). `web_listings`: **1,332 rows
before, 2,048 after** (716 new rows from the BetDelala and ethiopiarealty pages scraped
since 2 Nov; the rest updated; nothing deleted).

| | Rows |
|---|---|
| In the table | 2,048 |
| Flagged `exact_repeat` (older repeat copies) | 117 |
| Flagged `price_unusable` (all ethiopiarealty rows read by the old reader) | 709 |
| BetDelala sale / rent (not repeats) | 944 / 278 |
| With masked advert text | 61 (the local adverts; the scrape adds more) |
| Texts still holding a phone-like number | 0 |

**16 November 2026:** after a backup (`backups/ollaa_2026-11-16.dump`) the table holds
**2,442 rows** (133 flagged `exact_repeat`, 709 `price_unusable`), 517 with masked advert
text. Some off-plan adverts put a **price per m²** in the price field (e.g. 90,000–127,400
birr for a flat); treat a "price" under 1 million birr for a flat as a price per m², not a
total. 0 rows hold a phone-like number in the text or the address (7 addresses that
contained one are stored masked).

**Price per m² in the price box (fixed 16 Nov 2026, evening):** such numbers are now in
`price_per_m2` (the original in `price_as_advertised`); `price` holds a total only, either
as advertised or calculated from the price per m² × size — see `price_basis` ("total as
advertised" 2,236 rows, "calculated from price per m2" 76, "price per m2 only (no size)" 2,
where `price` is empty). Two calculated totals rest on a doubtful size (see
`THESIS_DATA_CHECK.md`). Table: 2,456 rows after the backup `backups/ollaa_2026-11-16b.dump`.

**Hand corrections (16 Nov 2026, night)**, checked against the stored advert text and kept in
`ollaa-web-scraper/data/manual_corrections.csv`: the Metro advert in Bole Bulbula is 130 m²
for 16.6 million birr (the reader had 68 m², and 5,400 m² for its second copy); the
"private real estate, Urael" advert is the Kazanchis project, 1 bedroom 97.18 m² (the
reader had 18), total 80,000 × 97.18 = 7,774,400 birr, now in Kirkos. Size and bedrooms now
follow the preparation step on every load, and repeat copies already in the table are
refreshed too (never inserted). Table after the load: **2,889 rows** (backup
`backups/ollaa_2026-11-16c.dump`).

**Every price query should add** `WHERE NOT price_unusable AND NOT exact_repeat`.
The sub-city of a row may change when the owner corrects the neighbourhood table; that is
expected (the next load applies it).

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
