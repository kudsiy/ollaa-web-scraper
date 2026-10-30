# Rules for working on ollaa-web-scraper

Read `STATUS.md` first: it has the audit findings (30 October 2026) and the numbered fix
list (W1, W2, …). The safety fixes W1–W4 are done.

**The project is parked** (owner's decision, 31 October 2026, after the Google Sheet check
in STATUS.md): do not run the scrapers, do not revive them, and do not switch the GitHub
automation back on unless the owner asks for it in a new decision. Maintenance and offline
work are fine; every run that visits websites needs the owner's approval for that run.
Before any change to the scrapers, read `SCRAPING_REVIEW.md` (why they delivered so little).

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
- `tests/test_no_telegram.py` fails if a Telegram source or Telegram code comes back. It
  runs with every `python -m pytest`; never weaken it.

## Websites and tests

- Audits and tests never visit live websites. Run the tests with `python -m pytest` from
  `ollaa-web-scraper\` (or `python -m pytest ollaa-web-scraper` from the top folder);
  `ollaa-web-scraper\pytest.ini` limits them to `tests/`. Run them after every change.
- `tests/conftest.py` blocks the internet, the database and the browser for every test
  (task W2), and `tests/test_offline_guard.py` checks that the block works. Never weaken
  them. Tests use saved pages and fakes, never a real website.
- The live website checks are in `tools/` (`live_diagnostic.py`, `live_quick_diagnostic.py`).
  They refuse to start without `--live`; run them only with the owner's approval for that
  run. Never put a script that goes online in `tests/`, and never name one `test_*.py`.
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
  approval. If history is ever rewritten, every copy cloned before that must be deleted and
  cloned again.
- Since W11, `main` is the only branch. After a task branch is merged into `main`, ask the
  owner before deleting it.
- `backups/` (ignored by git) holds `branches_before_W11_2026-10-30.bundle`, a copy of
  every branch deleted in W11. Restore one with
  `git fetch backups/branches_before_W11_2026-10-30.bundle refs/remotes/origin/<name>:refs/heads/<name>`.
  Its history includes the old password: never upload it or put it on GitHub.

## Secrets and settings

- Every password and connection detail lives in `.env` in the top project folder
  (`C:\Projects\ollaa-web\.env`, never committed); `.env.example` lists the names.
  `config.py` reads it (with `python-dotenv`); settings already in the environment, such as
  the GitHub automation's, win.
- The database settings have the same names and values as Ollaa-Telegram's everyday login:
  `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` = `ollaa_user`, `DB_PASSWORD` (copied from
  Ollaa-Telegram's `.env` on 30 October 2026). If that password changes there, change it
  here too. Never copy the administrator login or any Telegram value.
- `etl/db_writer.py` refuses to connect without `DB_PASSWORD`, or as the administrator
  login `postgres` (task W3, checked by `tests/test_settings.py`). Never switch this project
  to `postgres`: it has no administrator tasks (the same rule as Ollaa-Telegram task S9).
- Never write a password into a script or a `.bat` file. The old `START_OLLAA.bat` did, and
  that old password is still readable in the saved copies of old pull requests #1–#9 on
  GitHub (W5; no branch has it since W11). It has been changed and must never be used
  again.

## Database safety

- This project uses the same PostgreSQL 18 database `ollaa` on this laptop as
  Ollaa-Telegram, but only its own table `web_scraped_listings` (76 rows at Ollaa-Telegram's
  audit). Never read from or write to Ollaa-Telegram's tables (`telegram_listings`,
  `processed_listings`, `rental_listings`, `media_queue`, `listing_overrides`,
  `processing_exclusions` and the rest).
- Nothing in this project deletes data automatically (task W4, checked by
  `tests/test_no_deletion.py`): no `DELETE`, `TRUNCATE` or `DROP`, and the Google Sheet is
  never cleared or shrunk. Old listings are price history. Deleting is a manual step for
  the owner, after a backup. Never add automatic deletion back.
- Before any task that changes data, take a backup (the `pg_dump` command in
  Ollaa-Telegram's `CLAUDE.md`), count the rows before and after, and report both numbers.
- Ollaa-Telegram's `database/schema.sql` describes the whole database, including
  `web_scraped_listings`. If a task here changes that table, tell the owner that
  Ollaa-Telegram's schema must be re-exported in an Ollaa-Telegram session.

## How the project runs

- `README.md` (top folder) explains the project, set-up and commands in simple words.
  Keep it true: update it in the same task whenever commands, folders or settings change.
- `source_registry.py`: the list of website sources (bank auctions, tender sites, property
  sites) and their status.
- `scrapers/`: one scraper per source (`banks/`, `tenders/`, `listings/`), built on
  `scrapers/base_scraper.py`.
- `parsers/`: reading prices, areas, places and Amharic text (`semantic_engine.py`,
  `price_extractor.py`, `amharic_parser.py`, PDF and OCR helpers).
- `etl/`: cleaning (`normalizer.py`), removing duplicates (`deduplicator.py`), writing to
  the database (`db_writer.py`), the 57-column CSV (`sheets_exporter.py`) and the Google
  Sheet upload (`sheets_uploader.py`).
- `tests/`: offline tests only. `tools/`: live website checks (need `--live` and the
  owner's approval).
- Two ways to run everything: `scheduler.py` (runs forever on a timer, writes the
  database) and `etl/unified_exporter.py` (one pass, writes `property_data.json`,
  `property_data_unified.csv` and the Google Sheet; this is what the GitHub automation ran).
- The laptop's normal Python already has the packages (in the owner's own package folder),
  so programs here start with plain `python`; a project `venv` with pinned versions is
  task W6. Install packages with `pip install -r ollaa-web-scraper\requirements.txt`. The
  `requirements.txt` and `__init__.py` at the top level are links that only work on
  Linux; on Windows they are one-line text files.
- The Tesseract OCR program is installed at `C:\Program Files\Tesseract-OCR`.
