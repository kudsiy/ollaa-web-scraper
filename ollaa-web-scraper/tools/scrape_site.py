"""Resumable, capped, polite full scrape of a GO site (task W16, owner approved the birr
sites 1 Nov 2026). Reuses the recon helpers. For each site: gather listing URLs from the
sitemap, skip the ones already done, read up to BATCH new ones with a random 3-6 s pause,
honest UA, read-only, and STOP at the first block, challenge or error (never bypass). A
connection drop or timeout is retried once after a minute (owner, 13 Nov 2026); a second
failure in a row stops the run, and a block, challenge or bad status is never retried.
Appends structured fields only (no phone numbers, no descriptions) to a local CSV, and
records done URLs so the next run continues. A daily cap keeps the load light.

usage: scrape_site.py <batch> <label>=<sitemap-url> [...]
"""
import csv
import datetime
import os
import pathlib
import random
import sys
import time

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pilot_generic as pg  # noqa: E402

DAILY_CAP = 500  # per site per day, polite
GAP_MIN = float(os.getenv("OLLAA_GAP_MIN", "3"))  # seconds between requests (raise for flaky sites)
GAP_MAX = float(os.getenv("OLLAA_GAP_MAX", "6"))
FIELDS = ["source", "url", "price", "currency", "area_sqm", "bedrooms", "place", "listing_type", "scraped_at"]
RETRY_WAIT = 60  # seconds before the one retry after a connection drop or timeout
TRANSIENT = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)


def fetch_with_one_retry(url):
    """Get a page; on a connection drop or timeout wait RETRY_WAIT s and try once more.
    Returns (response, None) or (None, error text). Nothing else is retried."""
    for attempt in (1, 2):
        try:
            return requests.get(url, headers={"User-Agent": pg.UA}, timeout=25), None
        except TRANSIENT as e:
            if attempt == 2:
                return None, f"{e!r} (after one retry)"
            print(f"  connection problem ({type(e).__name__}); waiting {RETRY_WAIT} s, then one retry", flush=True)
            time.sleep(RETRY_WAIT)
        except Exception as e:  # noqa: BLE001
            return None, repr(e)


def today_count(done_log):
    """How many fetched today already, to respect the daily cap across runs."""
    if not done_log.exists():
        return 0
    today = datetime.date.today().isoformat()
    return sum(1 for ln in done_log.read_text(encoding="utf-8").splitlines() if ln.startswith(today + "\t"))


def run(label, sitemap, batch):
    print(f"\n===== {label}")
    out = pg.BASE / label
    out.mkdir(parents=True, exist_ok=True)
    csv_file, done_log = out / "full.csv", out / "done.log"
    try:
        urls, err = pg.collect_listing_urls(sitemap)
    except Exception as e:  # noqa: BLE001
        print(f"  could not read sitemap: {e!r}")
        return
    if err or not urls:
        print(f"  {err or 'no listing URLs'} — skipping")
        return

    done = set()
    if done_log.exists():
        for ln in done_log.read_text(encoding="utf-8").splitlines():
            parts = ln.split("\t")
            if len(parts) == 2:
                done.add(parts[1])
    cap_left = DAILY_CAP - today_count(done_log)
    todo = [u for u in urls if u not in done][:min(batch, max(0, cap_left))]
    print(f"  {len(urls)} in sitemap, {len(done)} already done, daily cap left {cap_left}; this run: {len(todo)}")
    if not todo:
        print("  nothing to do (done, or daily cap reached)")
        return

    new_file = not csv_file.exists()
    rows, stopped = [], None
    with open(csv_file, "a", newline="", encoding="utf-8") as fh, open(done_log, "a", encoding="utf-8") as dl:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for i, u in enumerate(todo, 1):
            time.sleep(random.uniform(GAP_MIN, GAP_MAX))
            r, err = fetch_with_one_retry(u)
            if r is None:
                stopped = f"error at #{i}: {err}"
                break
            if pg.blocked(r):
                stopped = f"block/challenge at #{i} (HTTP {r.status_code}) — stopping, not bypassing"
                break
            if r.status_code != 200:
                stopped = f"HTTP {r.status_code} at #{i}"
                break
            rec = pg.extract(u, BeautifulSoup(r.content, "lxml"))
            rec["source"] = label
            rec["scraped_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            w.writerow({k: rec.get(k, "") for k in FIELDS})
            fh.flush()  # save every row at once: a run cut off part-way loses nothing
            dl.write(f"{datetime.date.today().isoformat()}\t{u}\n")
            dl.flush()
            rows.append(rec)
            if i % 25 == 0:
                print(f"  ... {i}/{len(todo)} done", flush=True)

    n = len(rows)
    print(f"  fetched {n} this run" + (f"; STOPPED: {stopped}" if stopped else ""))
    if n:
        p = lambda k: f"{100*sum(1 for r in rows if str(r[k]).strip())//n}%"
        print(f"    price {p('price')} | size {p('area_sqm')} | location {p('place')} | bedrooms {p('bedrooms')}")
    total_done = len(done) + n
    print(f"  total done for {label}: {total_done} / {len(urls)} ({len(urls)-total_done} left)")


if __name__ == "__main__":
    batch = int(sys.argv[1])
    for arg in sys.argv[2:]:
        label, _, sm = arg.partition("=")
        run(label, sm, batch)
