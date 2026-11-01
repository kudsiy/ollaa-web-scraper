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
| Database login | `ollaa_user` (everyday), `postgres` only for backups | `ollaa_user` from its own `.env` (since W3); `postgres` is refused |
| Other output | thesis report (`DATA_QUALITY.md`) | a Google Sheet, updated daily until 7 October 2026 |

- Same database, **different data**: nothing in Ollaa-Telegram reads `web_scraped_listings`,
  and its thesis numbers do not use it. The two Telegram channels this project used to read
  are not in Ollaa-Telegram's channel list. The Google Sheet holds none of their adverts
  (checked 31 October); `web_scraped_listings` was not checked (source names "Ethio Real
  Estate Telegram" and "Betoch Telegram").
- Separate code: Ollaa-Telegram has its own parser (`run_pipeline.py`, `locations.py`); this
  project has another (`parsers/semantic_engine.py`). They do not share code.

## Do you still need it?

Not for Ollaa-Telegram: nothing there depends on it, and Ollaa-Telegram works without it.

**The owner decided on 31 October 2026 to keep it parked** (task W8): it stays on GitHub,
where it costs nothing, with the safety fixes W1–W4 done, but nothing is run or revived.
What it produced so far is modest (see the next section): about 154 usable sale adverts,
no bank-auction prices.

## What the Google Sheet holds (checked 31 October 2026)

Read through the Google Sheets connection already set up in the Claude app (no new login).
Only counts were analysed; the advert texts, which hold phone numbers, were not downloaded.

- The spreadsheet "Ollaa-Web" has three tabs. **"new"** (4,409 rows) is the one the GitHub
  automation filled. "Sheet1" (1,360 rows, 27–29 May) is an earlier upload; 1,240 of its
  rows are also in "new". "Property Data" holds 2 junk rows from a first test on 16 May.
- **Nothing new since 10 August 2026.** Rows were added from 29 May to 10 August; the daily
  runs after that, until 7 October, added nothing although they all "succeeded". The main
  listing site, Ethiopia Property Centre, last added rows on 7 June; BetDelala and most
  tender sites on 10 August; the bank scrapers produced 6 rows in all (last on 8 June).
- **A third of the rows are repeats**: 1,462 of the 4,409 rows repeat an advert link already
  in the sheet (one advert appears 48 times); the duplicate check did not recognise them.
- **Tender sites (2,548 rows) and bank/government auctions (54 rows: 48 from eGP, 6 from
  banks) are not usable for valuation**: almost none has a price (0.4% and 2%) or a size,
  and only about 1 in 5 tender titles is about property at all; most are purchases of goods
  and services.
- **Property listing sites (1,807 rows) are the useful part.** After removing repeats,
  US-dollar prices and 75 "prices" that look like phone numbers (all on Ethiopia Property
  Centre), **154 distinct sale adverts** have a price, a size and a place with a believable
  price per m² (median about 151,000 ETB/m²; 10% below 25,000 and 10% above 297,000): 121
  from Ethiopia Property Centre and 33 from BetDelala, 82 of them in Bole.
- Missing for valuation: no advert has a posting date (only the day it was scraped), places
  are only at sub-city level (Bole, Yeka, …), there are no coordinates, and bedrooms are
  known for about 1 row in 5.
- No adverts from the two removed Telegram channels are in the sheet.
- For comparison, Ollaa-Telegram's thesis report (`DATA_QUALITY.md`) counts 394 sale
  listings ready for a hedonic model. These 154 could add up to about 39% more, from other
  sources, if they do not overlap (not checked). Its own biggest possible gain, reading its
  2,860 photo-only posts, is much larger.

**Recommendation:** keep the project parked and do not switch the GitHub automation back on
as it is. If more sale prices are wanted for the thesis, the cheapest step is a one-off clean
export of the 154 usable adverts (W14); reviving the scraping is only worth it for Ethiopia
Property Centre and BetDelala, with the fixes in W14. **Owner's decision (31 October 2026):
keep it parked.**

## Why so little data: right websites, wrong method (review of 31 October 2026)

Details and sources in `SCRAPING_REVIEW.md`. In short, the main problem is how the project
scrapes, not which websites: Ethiopia Property Centre, the main Ethiopian property site
with about 5,000 adverts, is on the list, but a code change on 7 June broke our scraper for
it, and from 10 August the upload to the sheet failed silently. The scrapers only read the
summary cards (so most sizes are missing), never save posting dates, guess rent or sale
badly, save the same advert again and again, and hide failures. A recon of candidate sites
on 1 November 2026 (task W16, `SITE_RECON.md`) refined this: about 8 sites are reachable and
allow crawling (BetDelala, with a 4,076-page sitemap, is the best; five WordPress sites and
EPC follow), Jiji is an ASK (its terms, not robots, are the blocker), and engocha/qefira/
etrealtor are walled or down. EPC's own rules in fact allow crawling; its wall is an
intermittent Cloudflare challenge, which we never force.

## Copies on this laptop

The real project folder is **`C:\Projects\ollaa-web`**: the only copy connected to GitHub,
identical to GitHub's `main` (commit `dbd34fc`, 7 June 2026), with the full history, and
next to Ollaa-Telegram in `C:\Projects`.

Every file in every copy was compared with every version in GitHub's history (line endings
ignored):

| Copy | Date | Same as GitHub? | Work not on GitHub |
|---|---|---|---|
| `C:\Projects\ollaa-web` (git) | 7 Jun | yes, `main` exactly | none (its local branch `master`, "initial local state", only holds versions that are on GitHub; deleted in W11) |
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

**Only with the owner's approval.** The safety fixes W1–W4 are done, but every run of
`scheduler.py`, `etl/unified_exporter.py` or a scraper visits real websites and needs the
owner's approval for that run: first decide whether the project is wanted (W8), then one
supervised test run (W13). Set-up and the exact commands are in `README.md`.

What is safe now: the offline tests, from `C:\Projects\ollaa-web\ollaa-web-scraper` (the
laptop's normal Python already has the packages):

```
python -m pytest
```

Since W2 the tests cannot reach the internet, the database or a browser
(`tests/conftest.py`). The two live website checks are in `tools/`; they refuse to start
without `--live` and need the owner's approval.

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

After W2 (tests offline only): a plain `python -m pytest` collects only `tests/` and
**29 tests pass** (the 24 above plus 5 in `tests/test_offline_guard.py`), started from
`ollaa-web-scraper\` or from the top folder (`python -m pytest ollaa-web-scraper`). The two
`tools/live_*.py` scripts stop with a message when started without `--live`.

After W3 (safe database login): **36 tests pass** (the 29 above plus 7 in
`tests/test_settings.py`). This laptop now has `C:\Projects\ollaa-web\.env`: the five
everyday database settings were copied from Ollaa-Telegram's `.env` without being shown,
and the program reads them (login `ollaa_user`, password present). In a copy without
`.env`, as on GitHub's machines, every program still loads and `scheduler.py --init-db`
stops with "DB_PASSWORD is missing. Add it to …\.env" before any database connection. Not
checked: an actual login to the database (that needs a connection; the first approved run
will show it). `ollaa_user` already owns `web_scraped_listings`: Ollaa-Telegram's task S9
gave it every table in the database.

After W4 (no automatic deletion): **41 tests pass** (the 36 above plus 5 in
`tests/test_no_deletion.py`). The same 5 tests run on the code before W4 fail 4 times
(deleting SQL found, delete function present, a clean-up timer in the scheduler, a
60-column sheet shrunk to 57), so they really catch the problem.

Not checked, on purpose: any scraper against a real website, the Telegram reader (now
removed), the database (a read-only count was blocked by the session's safety settings; the 76 rows come
from Ollaa-Telegram's audit), and the Google Sheet (needs the owner's Google login).

## What is broken or risky

1. **Telegram speed (fixed by W1: all Telegram code removed).** `scrapers/telegram_scraper.py`
   read `t.me/s/<channel>` with only 2–5 seconds between pages, up to 50 pages per channel,
   every 30 minutes in `scheduler.py`, and at every start. Ollaa-Telegram allows the same
   kind of reading only once every 20–40 seconds with a hard cap per run. From this laptop it
   would have used the same internet connection as the owner's Telegram account.
2. **Tests that scrape (fixed by W2).** `tests/diagnostic_test.py` (picked up by a bare
   `pytest`) and `tests/quick_diagnostic.py` visited live websites. They are now
   `tools/live_diagnostic.py` and `tools/live_quick_diagnostic.py`, need `--live`, and are
   never collected. Both still save their results to a Linux path
   (`/home/engine/project/diagnostic_results.json`), so on Windows they would fail at the
   very end (see W13).
3. **Database login (fixed by W3).** `config.py` connected as `postgres` (the
   administrator) with the default password `postgres` unless environment variables were
   set; it did not read a `.env` file, and its setting names (`OLLAADB_*`) differed from
   Ollaa-Telegram's (`DB_*`). Now it reads `.env`, uses `DB_*` and `ollaa_user`, has no
   default password, and refuses `postgres`.
4. **Automatic deletion (fixed by W4).** `scheduler.py` deleted every
   `web_scraped_listings` row older than 90 days, once a day, with no backup. The Google
   Sheet upload also shrank any sheet with more than 57 columns back to 57, deleting
   whatever was in the extra columns. Both are gone; nothing deletes data automatically.
5. **Old password on GitHub.** `START_OLLAA.bat` (in GitHub's early history, 9 to 13 May)
   contains the old database password. Corrected in W11: it was never in `main`'s history
   (`main` starts on 16 May), but it was in the history of 9 old branches, not 4 (the audit
   only looked at each branch's latest files). W11 deleted those branches, so now it is
   readable only in the saved copies of old pull requests #1–#9, which only GitHub Support
   can remove. The password has been changed (it does not match the current one), so the
   risk is low unless it was reused somewhere else.
6. **Sources listed as working that have no scraper**: `etrealtor`, `ethiopianproperties`,
   `zegebeya`, `afrobet` (each run logs "No scraper implementation found"). `jiji` runs in
   the exporter but not in `scheduler.py`. Eight files are never used: the `abay`, `dbe`,
   `delala` and `auctionet` bank scrapers, `generic_scraper`, the `arifchereta` and
   `habeshatender` tender scrapers, and `eligibility_checker`. Every source is marked
   "verified_working"; nobody has checked that since May.
7. **GitHub automation is off.** GitHub disabled the daily "Sync to Google Sheets" job for
   inactivity after its run on 7 October 2026. It ran 167 times; the last 100 runs
   (30 June to 7 October) all ended "success", about 15 minutes each. "Success" only means
   it did not crash: the exporter hides scraper errors. Indeed nothing new reached the Sheet
   after 10 August (see "What the Google Sheet holds").
8. **Windows set-up.** The top-level `requirements.txt` and `__init__.py` are Linux links;
   on Windows they are one-line text files, so `pip install -r requirements.txt` from the
   top folder fails. Package versions are not pinned (`>=`), unlike Ollaa-Telegram.
9. **Housekeeping.** No README or how-to-run guide (the old README was removed; a new one
   was added by W10). 27 old `cto/*` branches on GitHub (deleted in W11). The folder's git
   identity is "Antigravity"; 13 old commits show the owner's personal e-mail address
   publicly.

## What is missing

- A record of when each source was last checked, and an honest status per source.
- Pinned package versions and a project `venv`.

## Fix list (one session each, in this order)

| # | Task | Why | Status |
|---|---|---|---|
| W1 | Telegram: remove everything Telegram-related (owner's decision: Telegram is Ollaa-Telegram's job). Removed `scrapers/telegram_scraper.py`, the two channels in `source_registry.py`, their entries and the 30-minute Telegram timer in `scheduler.py` and `etl/unified_exporter.py`, the `t.me` check in `eligibility_checker.py`, the `@username` ("Telegram handle") reading in `parsers/semantic_engine.py` (phone numbers are still read), the Telegram `message_id` fallback in `etl/normalizer.py` and `etl/sheets_exporter.py` (web listings never had one, so their duplicate fingerprints do not change), and the Telegram comments in `requirements.txt`. Added `tests/test_no_telegram.py`, which fails if a Telegram source or Telegram code comes back. The 57 Sheet columns are unchanged | protects the Telegram account; one project per job | done 30 Oct 2026 (24 offline tests pass) |
| W2 | Make `pytest` offline-only. Moved the two live diagnostics to `tools/live_diagnostic.py` and `tools/live_quick_diagnostic.py` (names no tool collects; they refuse to start without `--live`; removed the hidden pytest hook), added `ollaa-web-scraper/pytest.ini` (tests in `tests/` only), and `tests/conftest.py`, which blocks the internet, the database and the browser for every test, checked by `tests/test_offline_guard.py` | stops accidental scraping | done 30 Oct 2026 (29 offline tests pass) |
| W3 | Settings: `config.py` reads `.env` from the top folder (`python-dotenv`, added to `requirements.txt`), the same `DB_*` names as Ollaa-Telegram, login `ollaa_user`, no default password; `etl/db_writer.py` refuses to connect without `DB_PASSWORD` or as `postgres`; removed an unused line that wrote the password into a database address; added `.env.example`, `tests/test_settings.py`, and this laptop's `.env` (everyday login copied from Ollaa-Telegram's `.env`, values not shown) | safe database login | done 30 Oct 2026 (36 offline tests pass) |
| W4 | Remove the daily 90-day delete. Removed the scheduler's daily clean-up job and `DBWriter.delete_old_listings` (old listings are price history; deleting is a manual step for the owner, after a backup). Also in the Google Sheet upload: the sheet still grows to 57 columns but is never shrunk, and only the first 57 header cells are checked, so extra columns are kept. Added `tests/test_no_deletion.py` | no silent data loss | done 30 Oct 2026 (41 offline tests pass) |
| W5 | Old password on GitHub: owner confirms it is not used anywhere else; then either accept it (it is retired) or ask GitHub Support to remove the saved copies of pull requests #1–#9 (the branches that held it were deleted in W11; `main` never had it) | public history | to do (owner decision) |
| W6 | Set up a project `venv`, pin package versions in `requirements.txt`, document `pip install -r ollaa-web-scraper\requirements.txt` | reproducible set-up on Windows, independent of the owner's own package folder | to do |
| W7 | Offline tests for the scrapers: save one page per source and test each scraper on the saved page (no internet) | today's tests check only the parsers, the Sheet upload, the Telegram ban and the offline guard, not a single scraper | to do |
| W8 | Check the Google Sheet and decide: use this project again, or keep it parked. Sheet checked on 31 Oct 2026 (see "What the Google Sheet holds"): 154 usable sale adverts, nothing new since 10 August, tenders and bank auctions not usable, no Telegram adverts. Recommendation: keep parked. **Owner's decision (31 Oct 2026): keep it parked.** Not checked: the 76 database rows | is the data useful? | done 31 Oct 2026 (kept parked) |
| W9 | Source registry clean-up: honest status per source; remove the 4 sources without a scraper (`zegebeya`, `afrobet`, `etrealtor`, `ethiopianproperties`: no property site found under these names, see `SCRAPING_REVIEW.md`); add `jiji` to the scheduler; remove unused scraper files (with owner approval) | runs only what works | to do |
| W10 | Write a short README (what, how to run, how not to run). Added `README.md` (top folder): what the project does, its status, outputs, folders, set-up, the offline test command, the live commands (only with approval; the exporter starts as `python -m etl.unified_exporter`, because `python etl/unified_exporter.py` cannot find its modules on Windows) and a "never" list. Also added `exports/` and `results.txt` to `.gitignore`: the scheduler's daily CSV and its fallback results file hold scraped adverts and were not ignored | for the owner and future sessions | done 30 Oct 2026 |
| W11 | GitHub clean-up, with the owner's approval of the exact list. Every branch was first copied to `backups/branches_before_W11_2026-10-30.bundle` (ignored by git; checked complete) and checked: 24 were inside `main`'s history, and 8 early ones (11–15 May) were carried into `main` (each is part of the 15 May branch, whose latest files are all in `main`). The one with work that never reached `main`, `cto/validate-ollaa-scrapers-end-to-end` (a closed "WIP" attempt of 11 May, pull request #2), was also deleted, on the owner's decision. Deleted 33 branches on GitHub (6 finished task branches, 27 old `cto/*`) and 7 on this laptop (including `master`); `main` is now the only branch. Restore one with `git fetch backups/branches_before_W11_2026-10-30.bundle refs/remotes/origin/<name>:refs/heads/<name>` | tidy, removes the old password from every branch | done 30 Oct 2026 |
| W12 | Old copies: owner deletes the copies listed above (keep the 5 May zip only if the PPAA scraper is wanted) | removes the old password from the laptop | to do (owner) |
| W13 | Only if W8 says "use it": fix the Linux save path in the two `tools/live_*.py` scripts, then one supervised live test run of a single website source, then decide about re-enabling the GitHub automation | first real run after the fixes | not planned (project parked, 31 Oct 2026) |
| W14 | Only if the owner wants web prices for the thesis: either export the 154 usable sale adverts once into a clean file (no phone numbers, never committed), or revive only Ethiopia Property Centre and BetDelala after fixing three things: phone numbers read as prices, the same advert added again and again, and missing posting dates | more sale prices for the hedonic model | not planned (project parked, 31 Oct 2026) |
| W15 | Only if the owner un-parks the project: a small pilot on Ethiopia Property Centre only (see `SCRAPING_REVIEW.md`, section 3). First check its `robots.txt` and terms, or ask it for an academic data extract; owner opens one GitHub run log after 10 August to see why uploads failed; with approval, look at 2–3 of its pages once; then read each advert's own page (size, place, "Added on" date), avoid repeats by the advert link, count rows per site and warn at zero, fix the backup price reader ("120 m2" read as 120 million), and test offline on saved pages before one supervised run. **Started by the owner on 31 Oct 2026 and stopped at the first request**: the site answered `robots.txt` with HTTP 403 and a Cloudflare bot check, so it blocks automated readers; not got around (see `SCRAPING_REVIEW.md`, section 4). Left: ask the site for an academic data extract, or cite its average-price reports | many more usable sale adverts than today's 154, if the site allows it | stopped: site blocks automated readers |
| W16 | Owner un-parked the project on 1 Nov 2026 for a legitimate multi-site plan (sitemaps / page JSON / Scrapy / Playwright; never bypass bot protection). Read-only recon done (`SITE_RECON.md`): GO / ASK / NO table for 16 candidate sites. Next, on the owner's pick: a ~50-listing pilot per GO site (BetDelala first), showing price/size/place fill rates, to a local file first. Still needs approval: installing Scrapy, and writing to the database. On EPC the recon found robots.txt permits crawling (the earlier 403 was an intermittent Cloudflare challenge), so it is GO-cautious, not a flat block. First pilot done on BetDelala (50 listings, no blocks): price 100%, size 100%, location ~72%, clean ETB, median sale ~106,000 ETB/m² (see `SITE_RECON.md`). Still needs approval: installing Scrapy, the full BetDelala scrape (step 5), and writing to the database (step 4) | grow the dataset from sites that allow it | recon + BetDelala pilot done; full scrape and more sites await owner's pick |
