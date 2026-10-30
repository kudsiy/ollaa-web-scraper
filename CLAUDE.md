# Rules for working on ollaa-web-scraper

Read `STATUS.md` first: it has the audit findings (30 October 2026) and the numbered fix
list (W1, W2, …). W1 is done; W2–W4 must be done before anything in this project is run.

## Working with the owner

- The owner is not a programmer. Explain in simple words, do the technical work yourself,
  and stop only for things the owner must do in person (approve a step, open a Google
  Sheet, paste a value into `.env`).
- Never show a password, API key, token or credentials file in the chat, in a commit, or
  in a file other than `.env`. When printing code or data that might contain one, mask it.
- Ask the owner before installing anything new (packages or programs).

## Where the project is

- The real project folder is `C:\Projects\ollaa-web`, a git copy of
  `github.com/kudsiy/ollaa-web-scraper`. The code is in the inner folder
  `ollaa-web-scraper\`; run Python from there.
- Every other copy on the laptop (`C:\Projects\New folder*`, the zip files, the
  `Downloads` copies) is old; see STATUS.md. Never edit them or copy files from them.
- Sister project: `C:\Projects\Ollaa-Telegram`. Never change anything there from a session
  in this project. Its `CLAUDE.md` holds the Telegram account rules, which apply here too.

## No Telegram in this project (top priority)

The owner's Telegram account has been revoked many times and banned once, and the
Ollaa-Telegram scraper depends on it. Protecting it comes before everything else.

- **This is a website scraper only. Telegram is Ollaa-Telegram's job** (owner's decision,
  30 October 2026). All Telegram code was removed in task W1.
- Never add Telegram back in any form: no Telegram sources in `source_registry.py`, no
  reading of `t.me` pages (not even the public web preview), no Telethon or Pyrogram, no
  `TG_API_ID` / `TG_API_HASH` / phone number, no `.session` files. Never copy
  Ollaa-Telegram's `.env` Telegram values or login files into this project. If Telegram
  data is wanted, it comes from Ollaa-Telegram.
- `tests/test_no_telegram.py` fails if a Telegram source or Telegram code comes back. Run
  it after any change to the sources, scrapers or parsers, and never weaken it.

## Websites and tests

- Audits and tests never visit live websites. `tests/diagnostic_test.py` and
  `tests/quick_diagnostic.py` visit real bank and tender sites: never run them. A bare
  `pytest` also runs `diagnostic_test.py`, so until W2 is done run the offline tests by
  name, from `ollaa-web-scraper\`:
  `python -m pytest tests/test_amharic_parser.py tests/test_price_extractor.py tests/test_advanced_semantics.py tests/test_sheets_uploader.py tests/test_no_telegram.py -p no:cacheprovider`
- A live scraping run needs the owner's approval for that run: no logins, no getting
  around blocks or CAPTCHAs, polite delays.

## GitHub automation

- `.github/workflows/sync_to_sheets.yml` ran every day on GitHub's computers (scraping all
  sources into a Google Sheet; until W1 that included two Telegram channels) until GitHub
  switched it off for inactivity on 7 October 2026. Never re-enable or start it without
  the owner's approval.
- The Google key exists only as the GitHub secret `GOOGLE_CREDENTIALS`. `credentials.json`
  and any service-account file are never committed.

## Git and GitHub

- The GitHub repository `kudsiy/ollaa-web-scraper` is **public**: everything pushed,
  including old history, can be read by anyone.
- Commit and push after every finished task, so work never stays on one computer. Do each
  task on its own branch, then merge into `main` when it is safe and the owner agrees.
- After a task is finished, update its row in the `STATUS.md` fix list.
- Commit as `kudsiy <kudsiy@users.noreply.github.com>` (as Ollaa-Telegram does). This
  folder's own git setting says "Antigravity", so pass
  `git -c user.name=kudsiy -c user.email=kudsiy@users.noreply.github.com commit ...`.
- Never commit: `.env`, `credentials.json` or other key files, `*.session`, `venv/` or
  `.venv/`, `property_data*.json` / `*.csv`, `exports/`, logs, or any scraped data (it holds
  other people's phone numbers).
- Never force-push, rewrite history or delete branches on GitHub without the owner's
  approval. If history is ever rewritten (task W5), every copy cloned before that must be
  deleted and cloned again.

## Secrets and settings

- Today `config.py` reads the database settings from environment variables
  `OLLAADB_HOST`, `OLLAADB_PORT`, `OLLAADB_NAME`, `OLLAADB_USER`, `OLLAADB_PASSWORD`, with
  unsafe defaults (user `postgres`, password `postgres`); no `.env` file is read. Until W3 is
  done, do not run anything that connects to the database.
- After W3: every password and connection detail lives in `.env` in the project folder
  (never committed); `.env.example` lists the names with empty values. Scripts use the
  everyday login `ollaa_user`, never `postgres` (the same rule as Ollaa-Telegram task S9).
- Never write a password into a script or a `.bat` file. The old `START_OLLAA.bat` did, and
  that old password is still readable in this repository's public history (W5). It has
  been changed and must never be used again.

## Database safety

- This project uses the same PostgreSQL 18 database `ollaa` on this laptop as
  Ollaa-Telegram, but only its own table `web_scraped_listings` (76 rows at Ollaa-Telegram's
  audit). Never read from or write to Ollaa-Telegram's tables (`telegram_listings`,
  `processed_listings`, `rental_listings`, `media_queue`, `listing_overrides`,
  `processing_exclusions` and the rest).
- `scheduler.py` deletes rows older than 90 days from `web_scraped_listings` every day
  (`_cleanup_old_data`). Until W4 is done, do not run the scheduler.
- Before any task that changes data, take a backup (the `pg_dump` command in
  Ollaa-Telegram's `CLAUDE.md`), count the rows before and after, and report both numbers.
- Ollaa-Telegram's `database/schema.sql` describes the whole database, including
  `web_scraped_listings`. If a task here changes that table, tell the owner that
  Ollaa-Telegram's schema must be re-exported in an Ollaa-Telegram session.

## How the project runs

- `source_registry.py`: the list of website sources (bank auctions, tender sites, property
  sites) and their status.
- `scrapers/`: one scraper per source (`banks/`, `tenders/`, `listings/`), built on
  `scrapers/base_scraper.py`.
- `parsers/`: reading prices, areas, places and Amharic text (`semantic_engine.py`,
  `price_extractor.py`, `amharic_parser.py`, PDF and OCR helpers).
- `etl/`: cleaning (`normalizer.py`), removing duplicates (`deduplicator.py`), writing to
  the database (`db_writer.py`), the 57-column CSV (`sheets_exporter.py`) and the Google
  Sheet upload (`sheets_uploader.py`).
- Two ways to run everything: `scheduler.py` (runs forever on a timer, writes the
  database) and `etl/unified_exporter.py` (one pass, writes `property_data.json`,
  `property_data_unified.csv` and the Google Sheet; this is what the GitHub automation ran).
- The laptop's normal Python already has the packages (in the owner's own package folder),
  so programs here start with plain `python`; a project `venv` with pinned versions is
  task W6. Install packages with `pip install -r ollaa-web-scraper\requirements.txt`. The
  `requirements.txt` and `__init__.py` at the top level are links that only work on
  Linux; on Windows they are one-line text files.
- The Tesseract OCR program is installed at `C:\Program Files\Tesseract-OCR`.
