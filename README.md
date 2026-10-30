# ollaa-web-scraper

Collects property prices from **websites** in Ethiopia, for the Ollaa valuation work:

- **bank foreclosure auctions**: CBE, Awash, Dashen, Zemen, Abyssinia, Amhara, Berhan,
  Coop Bank of Oromia, and AddisList's auction section;
- **tender and auction sites**: Walia Tender, 2Merkato, Ethiopian Tender, Afro Tender,
  Reporter Tenders, auction.et, eGP, TendersOnTime, GlobalTenders;
- **property listing sites**: Engocha, BetDelala, Ethiopia Property Centre, Ethiopia Realty,
  Ethio Real Estates, Living Ethio, Real Ethio, Jiji.

For each advert it reads the price, size, place, property type and dates (Amharic and
English) and removes duplicates. It is a scraper only: there is no website or app.

It reads **websites only**. Telegram channels are handled by the separate project
Ollaa-Telegram, never here.

## Status

Parked. The safety fixes are done (no Telegram, offline tests, safe database login, no
automatic deletion), but every run visits real websites and needs the owner's approval.
See [`STATUS.md`](STATUS.md) for the audit and the fix list, and [`CLAUDE.md`](CLAUDE.md)
for the working rules.

## What it produces

- `scheduler.py` writes into the table `web_scraped_listings` of the PostgreSQL database
  `ollaa` on the owner's laptop (shared with Ollaa-Telegram, which never touches this
  table), plus a daily CSV in `exports/`.
- `etl/unified_exporter.py` writes `property_data.json` and a 57-column
  `property_data_unified.csv`, and uploads to a Google Sheet when that is switched on.

These files hold other people's phone numbers: they are never committed.

## Folders

```
ollaa-web-scraper/
  source_registry.py   the list of websites and their status
  scrapers/            one scraper per website (banks/, tenders/, listings/)
  parsers/             reading prices, sizes, places and Amharic text
  etl/                 cleaning, duplicates, database, CSV and Google Sheet
  scheduler.py         runs the scrapers on a timer, writes the database
  config.py            settings, read from .env
  tests/               offline tests (no internet, no database)
  tools/               live website checks (need --live and approval)
.env.example           the settings this project needs (copy to .env)
```

## Set up (once)

1. Python 3.12 or newer (tested with 3.13).
2. Install the packages. On Windows use the inner file:
   `pip install -r ollaa-web-scraper\requirements.txt`
   (the `requirements.txt` at the top is a link that only works on Linux).
3. Copy `.env.example` to `.env` (same folder) and fill in `DB_PASSWORD` for the everyday
   database login `ollaa_user`. Never use the administrator login `postgres`; the program
   refuses it. `.env` is never committed.
4. Only for some websites: `python -m playwright install chromium` (a browser for pages
   that need JavaScript) and the Tesseract OCR program (for scanned PDF notices).

## Check that it works (safe, offline)

From the `ollaa-web-scraper` folder:

```
python -m pytest
```

This runs only the offline tests. They cannot reach the internet, the database or a
browser.

## Run the scrapers (only with the owner's approval)

These visit real websites. From the `ollaa-web-scraper` folder:

```
python scheduler.py --run-once --scraper engocha    one website, once
python scheduler.py --run-once                      every website, once
python scheduler.py                                 every website, on a timer, until stopped
python -m etl.unified_exporter                      every website once, to JSON, CSV and Sheet
```

`python scheduler.py --help` lists the options; `--diagnostic` runs without the database.
The website names are the keys in `source_registry.py`.

## Never

- Add Telegram in any form (sources, `t.me` pages, logins). A test fails if it comes back.
- Delete data automatically. A test fails if deleting code comes back.
- Put a password anywhere except `.env`, or use the `postgres` login.
- Commit `.env`, `credentials.json`, `exports/`, `property_data*` or any scraped data.
- Re-enable the GitHub automation (`.github/workflows/sync_to_sheets.yml`, switched off by
  GitHub on 7 October 2026) without the owner's approval.
