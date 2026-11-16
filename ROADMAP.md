# Ollaa roadmap

Ollaa is first a **company product**; the thesis uses its data. Both projects
(`ollaa-web-scraper` and the sister project Ollaa-Telegram) follow the same four phases
(owner, 16 November 2026). Keep this file updated at the end of every task.

**Rule: finish one phase before starting the next. No new features outside the current
phase.**

| Phase | Goal | Status (16 Nov 2026) |
|---|---|---|
| **1** | Telegram listener live 24/7 | **Current phase.** Sister project's work. |
| 2 | Telegram and web data merged into one database | Not started. Preparation only: `MERGE_NOTES.md` lists what must be solved first. |
| 3 | Photos, PDFs, then videos read automatically | Not started. |
| 4 | Estate IQ fed daily from the Ollaa database, and launched | Not started. |

## What this project does until Phase 2 starts

Only maintenance; no new features:

1. **Keep the approved scrape running** within the polite limits: BetDelala first; when it
   is finished, the approved **ethiopiarealty re-scrape** with the fixed price reader.
   It runs **once a day at 21:00** (Windows task `OllaaWebScrape`; if the laptop is off at
   that time, it runs as soon as the laptop is on), waits for the internet, does at most
   500 pages per site, and **stops for good at the first block or error**. Each run adds a
   line to `ollaa-web-scraper/saved_pages/daily_log.csv` (pages read, new listings,
   re-reads, still to read, error).
2. **Load the new pages into `web_listings`** when the owner asks (backup first, never
   between 10:00 and 12:00): `etl/prepare_web_listings.py`, then
   `etl/load_web_listings.py --apply`.
3. Fix data problems the owner points out (as with the two sizes on 16 Nov), always
   after a backup and recorded in `ollaa-web-scraper/data/manual_corrections.csv`.

Progress on 16 Nov 2026: BetDelala 2,482 of 4,244 pages read (1,778 left, about 4 days);
then ethiopiarealty about 1,600 pages (about 4 days). `web_listings`: 2,889 rows.

## Phase 2 preparation (no building yet)

`MERGE_NOTES.md`: every `web_listings` field next to the matching Ollaa-Telegram field,
and every difference (ids, place codes and sub-cities, developer names, price rules,
property types, payment terms, phone numbers) that must be decided before merging.
