# ollaa-web-scraper: status

Audit of 30 October 2026 (read-only: no code changed, no website scraped, Telegram not
contacted, database not opened). Rules for working on the project are in `CLAUDE.md`.
Fixes done since the audit are marked in the fix list at the end.

## What it is

A Python program that collects property information from **websites** in Ethiopia and puts
it into one table:

- **bank foreclosure auctions** (CBE, Awash, Dashen, Zemen, Abyssinia, Amhara, Berhan,
  Coop Bank of Oromia) and the AddisList auction section;
- **tender and auction sites** (Walia Tender, 2Merkato, Ethiopian Tender, Afro Tender,
  Reporter Tenders, auction.et, eGP, TendersOnTime, GlobalTenders);
- **property listing sites** (Engocha, BetDelala, Ethiopia Property Centre, Ethiopia Realty,
  Ethio Real Estates, Living Ethio, Real Ethio, Jiji).

**Websites only.** Until 30 October 2026 it also read two Telegram channels
(`EthioRealEstate1`, `betoch_kom`) through Telegram's public web page. The owner decided
that Telegram is Ollaa-Telegram's job, so all Telegram code was removed (W1).

For each advert it reads the price, size, place, property type and dates (Amharic and
English), removes duplicates, and saves the result in one of two ways:

1. `scheduler.py` runs forever on a timer and writes into the PostgreSQL table
   `web_scraped_listings` (plus a daily CSV in `exports/`).
2. `etl/unified_exporter.py` runs once, writes `property_data.json` and a 57-column
   `property_data_unified.csv`, and uploads to a Google Sheet. This is what the GitHub
   automation ran every day.

It is a **scraper only**: there is no website or app for visitors.

## How it relates to Ollaa-Telegram

| | Ollaa-Telegram | ollaa-web-scraper |
|---|---|---|
| Reads | Telegram: the channels and groups in its `src/channels.py`, with the owner's Telegram login | websites only (no Telegram since W1) |
| Database | `ollaa` on this laptop | the **same** `ollaa` database |
| Tables | `telegram_listings`, `processed_listings`, `rental_listings`, … | only its own `web_scraped_listings` (76 rows at Ollaa-Telegram's audit) |
| Database login | `ollaa_user` (everyday), `postgres` only for backups | `postgres` by default (unsafe, see W3) |
| Other output | thesis report (`DATA_QUALITY.md`) | a Google Sheet, updated daily until 7 October 2026 |

- Same database, **different data**: nothing in Ollaa-Telegram reads `web_scraped_listings`,
  and its thesis numbers do not use it. The two Telegram channels this project used to read
  are not in Ollaa-Telegram's channel list; adverts from them collected before W1 may still
  be in the Google Sheet and in `web_scraped_listings` (source names "Ethio Real Estate
  Telegram" and "Betoch Telegram"). Removing them is part of W8.
- Separate code: Ollaa-Telegram has its own parser (`run_pipeline.py`, `locations.py`); this
  project has another (`parsers/semantic_engine.py`). They do not share code.

## Do you still need it?

Not for Ollaa-Telegram: nothing there depends on it, and Ollaa-Telegram works without it.

It is worth **keeping, parked**: it is the only source of bank-auction and website prices,
which could support valuation work later, and keeping it on GitHub costs nothing. Do not run
it until W2–W4 are done. Whether to use it again is the owner's decision after looking at
what it produced (task W8).

## Copies on this laptop

The real project folder is **`C:\Projects\ollaa-web`**: the only copy connected to GitHub,
identical to GitHub's `main` (commit `dbd34fc`, 7 June 2026), with the full history, and
next to Ollaa-Telegram in `C:\Projects`.

Every file in every copy was compared with every version in GitHub's history (line endings
ignored):

| Copy | Date | Same as GitHub? | Work not on GitHub |
|---|---|---|---|
| `C:\Projects\ollaa-web` (git) | 7 Jun | yes, `main` exactly | none (its local branch `master`, "initial local state", only holds versions that are on GitHub) |
| `Downloads\ollaa-web-scraper-main\` and `Downloads\ollaa-web-scraper-main.zip` | downloaded 30 Oct | yes, `main` exactly | none |
| `C:\Projects\ollaa-web-scraper-main (3).zip` | 25 May | yes, commit `46935da` | none |
| `Downloads\Sorted Files\Archives\ollaa-web-scraper-main (1).zip`, `(2).zip`, `(3).zip` | 17, 27, 30 May | yes, commits `db7f56f`, `20390bb`, `1935c80` | none |
| `C:\Projects\New folder (4)\ollaa-web` | 13 May | yes, commit `533f64c` | none; **contains the old database password** |
| `C:\Projects\New folder (2)\ollaa-web` | 8 May | older than GitHub's first commit (9 May) | 14 earlier drafts, no new work; **contains the old password** |
| `C:\Projects\New folder\ollaa-web` | 7 May | older than GitHub's first commit | 31 earlier drafts, no new work; **contains the old password** |
| `New folder\…main (1).zip`, `New folder (2)\…main (1).zip`, `New folder (3)\ollaa-web.zip` | 6–8 May | older than GitHub's first commit | earlier drafts only |
| `Downloads\Sorted Files\Archives\ollaa-web-scraper-main.zip` | 5 May | the oldest design | `scrapers/tenders/ppaa_scraper.py` (government tenders from ppaa.gov.et) and longer early bank scrapers, later replaced. The only code that exists nowhere else |
| `Downloads\Sorted Files\Archives\ollaa-web-files.zip` | 25 May | 4 code files are on GitHub | 2 notes for an AI helper (`ANTIGRAVITY_INSTRUCTIONS.txt`, `BANK_URL_FIXES.txt`), no code |

The 7–8 May copies are the "before" versions of GitHub's first commit ("Fixes: NoneType
errors, AddisList navigation, …"): the commit contains the same files with those fixes added.

**Deleting old copies.** All the copies above except `C:\Projects\ollaa-web` can be deleted
without losing any work. One optional exception: keep the 5 May zip if the PPAA scraper may
be wanted again (task W12). Careful with `C:\Projects\New folder (4)`: besides the old
`ollaa-web` folder it holds `Ollaa-Telegram.zip`, a 21 May backup of Ollaa-Telegram that
contains old Telegram login files (`session.session`, `src/ollaa_session.session`) and an
old `.env`, and so does `C:\Projects\Ollaa-Telegram.zip`. Those zips belong to
Ollaa-Telegram; decide about them in an Ollaa-Telegram session.

## How to run it

**Not yet.** Until W2–W4 are done, do not run `scheduler.py`, `etl/unified_exporter.py` or
any scraper on this laptop (tests that scrape, unsafe database login, automatic deletion).

What is safe now, from `C:\Projects\ollaa-web\ollaa-web-scraper` (the laptop's normal
Python already has the packages):

```
python -m pytest tests/test_amharic_parser.py tests/test_price_extractor.py tests/test_advanced_semantics.py tests/test_sheets_uploader.py tests/test_no_telegram.py -p no:cacheprovider
```

Never run a bare `pytest`: it also runs `tests/diagnostic_test.py`, which visits the real
bank and tender websites.

## What works (checked in this audit)

Checked offline only, with every internet connection blocked while the checks ran:

- **All 22 offline tests pass** (Amharic text, prices, the semantic engine, and the Google
  Sheets upload against a fake Google): `22 passed in 0.53s`. Same result in a temporary
  clean install of `requirements.txt` (Python 3.13.14, deleted afterwards) and with this
  laptop's normal Python.
- All 67 Python files are free of syntax errors, all 57 program modules load, and no file
  imports something that does not exist.
- `python scheduler.py --help` shows its options (`--init-db`, `--run-once`, `--scraper`,
  `--stats`, `--diagnostic`).
- The GitHub automation ran 167 times between May and 7 October 2026 (the last 100 about
  15 minutes each, none crashed), so the scrapers did run on GitHub's computers. Whether they found good
  data was not checked (W8).

What fails:

- `pip install -r requirements.txt` in the top folder, on Windows:
  `ERROR: Invalid requirement: 'ollaa-web-scraper/requirements.txt': Expected semicolon (after name with no version specifier) or end`
- `brotli` (in `requirements.txt`) is missing from the laptop's normal Python. Everything
  else is already installed there (in the owner's own package folder, from earlier work),
  so the scrapers **can be started today with plain `python`**, which is why the "do not
  run" rules matter.

After W1 (Telegram removed): **24 offline tests pass** (the 22 above plus
`tests/test_no_telegram.py`), all modules still load, and the source list has 30 sources.

Not checked, on purpose: any scraper against a real website, the Telegram reader (now
removed), the database (a read-only count was blocked by the session's safety settings; the 76 rows come
from Ollaa-Telegram's audit), and the Google Sheet (needs the owner's Google login).

## What is broken or risky

1. **Telegram speed (fixed by W1: all Telegram code removed).** `scrapers/telegram_scraper.py`
   read `t.me/s/<channel>` with only 2–5 seconds between pages, up to 50 pages per channel,
   every 30 minutes in `scheduler.py`, and at every start. Ollaa-Telegram allows the same
   kind of reading only once every 20–40 seconds with a hard cap per run. From this laptop it
   would have used the same internet connection as the owner's Telegram account.
2. **Tests that scrape.** `tests/diagnostic_test.py` (picked up by a bare `pytest`) and
   `tests/quick_diagnostic.py` visit live websites.
3. **Database login.** `config.py` connects as `postgres` (the administrator) with the
   default password `postgres` unless environment variables are set; it does not read a
   `.env` file, and its setting names (`OLLAADB_*`) differ from Ollaa-Telegram's (`DB_*`).
   Run on this laptop today, it would most likely fail to log in (the password was
   changed), or, started from an old `.bat` file, try the retired password.
4. **Automatic deletion.** `scheduler.py` deletes every `web_scraped_listings` row older
   than 90 days, once a day, with no backup.
5. **Old password on GitHub.** `START_OLLAA.bat` (in GitHub's history from 9 to 13 May)
   contains the old database password. It was deleted from `main` on 13 May but is still
   readable in 4 old branches (`cto/end-to-end-validation-ollaa-scrapers`,
   `cto/test-scrapers-e2e-build`, `cto/update-valuation-worthy-sources-registry`,
   `cto/validate-ollaa-scrapers-end-to-end`) and pull requests #1–#4. The password has been
   changed (it does not match the current one), so the risk is low unless it was reused
   somewhere else.
6. **Sources listed as working that have no scraper**: `etrealtor`, `ethiopianproperties`,
   `zegebeya`, `afrobet` (each run logs "No scraper implementation found"). `jiji` runs in
   the exporter but not in `scheduler.py`. Eight files are never used: the `abay`, `dbe`,
   `delala` and `auctionet` bank scrapers, `generic_scraper`, the `arifchereta` and
   `habeshatender` tender scrapers, and `eligibility_checker`. Every source is marked
   "verified_working"; nobody has checked that since May.
7. **GitHub automation is off.** GitHub disabled the daily "Sync to Google Sheets" job for
   inactivity after its run on 7 October 2026. It ran 167 times; the last 100 runs
   (30 June to 7 October) all ended "success", about 15 minutes each. "Success" only means
   it did not crash: the exporter hides scraper errors, so the Sheet's contents still need
   checking (W8).
8. **Windows set-up.** The top-level `requirements.txt` and `__init__.py` are Linux links;
   on Windows they are one-line text files, so `pip install -r requirements.txt` from the
   top folder fails. Package versions are not pinned (`>=`), unlike Ollaa-Telegram.
9. **Housekeeping.** No README or how-to-run guide (the old README was removed). 27 old
   `cto/*` branches on GitHub. The folder's git identity is "Antigravity"; 13 old commits
   show the owner's personal e-mail address publicly.

## What is missing

- A `.env` / `.env.example` and a settings module like Ollaa-Telegram's `src/settings.py`.
- A `pytest.ini` so that `pytest` runs only offline tests.
- A record of when each source was last checked, and an honest status per source.
- Pinned package versions and a project `venv`.
- A README in simple words.

## Fix list (one session each, in this order)

| # | Task | Why | Status |
|---|---|---|---|
| W1 | Telegram: remove everything Telegram-related (owner's decision: Telegram is Ollaa-Telegram's job). Removed `scrapers/telegram_scraper.py`, the two channels in `source_registry.py`, their entries and the 30-minute Telegram timer in `scheduler.py` and `etl/unified_exporter.py`, the `t.me` check in `eligibility_checker.py`, the `@username` ("Telegram handle") reading in `parsers/semantic_engine.py` (phone numbers are still read), the Telegram `message_id` fallback in `etl/normalizer.py` and `etl/sheets_exporter.py` (web listings never had one, so their duplicate fingerprints do not change), and the Telegram comments in `requirements.txt`. Added `tests/test_no_telegram.py`, which fails if a Telegram source or Telegram code comes back. The 57 Sheet columns are unchanged | protects the Telegram account; one project per job | done 30 Oct 2026 (24 offline tests pass) |
| W2 | Make `pytest` offline-only: move the two live diagnostics to a `tools/` folder and add `pytest.ini` | stops accidental scraping | to do |
| W3 | Settings: `.env` + `.env.example` + one settings module, `ollaa_user` instead of `postgres`, no default password, refuse to start without `.env` | safe database login | to do |
| W4 | Remove the daily 90-day delete (or make it a report only) | no silent data loss | to do |
| W5 | Old password on GitHub: owner confirms it is not used anywhere else; then either accept it (it is retired) or delete the 4 old branches and ask GitHub Support to remove the 4 pull-request copies | public history | to do (owner decision) |
| W6 | Set up a project `venv`, pin package versions in `requirements.txt`, document `pip install -r ollaa-web-scraper\requirements.txt` | reproducible set-up on Windows, independent of the owner's own package folder | to do |
| W7 | Offline tests for the scrapers: save one page per source and test each scraper on the saved page (no internet) | today's tests check only the parsers, the Sheet upload and the Telegram ban, not a single scraper | to do |
| W8 | Owner opens the Google Sheet (ID in `.github/workflows/sync_to_sheets.yml`) and the 76 database rows, and decides: use this project again, or keep it parked. Also decide whether to delete the old Telegram adverts there (source names "Ethio Real Estate Telegram", "Betoch Telegram"; backup first) | is the data useful? | to do (owner) |
| W9 | Source registry clean-up: honest status per source, remove or implement the 4 sources without a scraper, add `jiji` to the scheduler, remove unused scraper files (with owner approval) | runs only what works | to do |
| W10 | Write a short README (what, how to run, how not to run) | for the owner and future sessions | to do |
| W11 | GitHub clean-up: delete old merged `cto/*` branches and the local `master` branch (owner approval) | tidy, fewer copies of history | to do |
| W12 | Old copies: owner deletes the copies listed above (keep the 5 May zip only if the PPAA scraper is wanted) | removes the old password from the laptop | to do (owner) |
| W13 | Only if W8 says "use it": one supervised live test run of a single website source, then decide about re-enabling the GitHub automation | first real run after the fixes | to do |
