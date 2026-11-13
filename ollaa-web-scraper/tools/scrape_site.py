"""Resumable, capped, polite full scrape of a GO site (task W16, owner approved the birr
sites 1 Nov 2026). Reuses the recon helpers. For each site: gather listing URLs from the
sitemap, skip the ones already done, read up to BATCH new ones with a random 3-6 s pause,
honest UA, read-only, and STOP at the first block, challenge or error (never bypass). A
connection drop or timeout is retried once after a minute (owner, 13 Nov 2026); a second
failure in a row stops the run, and a block, challenge or bad status is never retried.
Appends structured fields and the advert's own text, with every phone number, e-mail and
chat handle masked BEFORE it is written (owner, 13 Nov 2026: never store an unmasked phone
number), to a local CSV (`full_v2.csv`), and records done URLs so the next run continues.
Adverts whose web address suggests an off-plan or developer listing are read first,
including ones read earlier without their text. A daily cap keeps the load light.

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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pilot_generic as pg  # noqa: E402
from parsers.contact_mask import has_contact, mask_contacts  # noqa: E402
from parsers.offplan_terms import offplan_url_signal  # noqa: E402

DAILY_CAP = 500  # per site per day, polite
GAP_MIN = float(os.getenv("OLLAA_GAP_MIN", "3"))  # seconds between requests (raise for flaky sites)
GAP_MAX = float(os.getenv("OLLAA_GAP_MAX", "6"))
FIELDS = ["source", "url", "price", "currency", "area_sqm", "bedrooms", "place", "listing_type", "scraped_at",
          "ad_text", "reader"]
READER = "v2-2026-11-13"  # v2: details-box price (ethiopiarealty fix) + masked advert text
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


def masked_text(soup):
    """The advert's text with contacts hidden; refuses to return anything still unmasked."""
    text = mask_contacts(pg.advert_text(soup))
    if has_contact(text):  # masking twice must change nothing; if it would, store nothing
        return ""
    return text


def plan_order(urls, done, have_text, batch, cap_left, reread_old=False):
    """Off-plan / developer adverts without stored text first (even if read before without
    text), then the adverts never read; at most min(batch, cap_left). With reread_old (the
    ethiopiarealty re-scrape, owner 13 Nov 2026) every advert not yet read by the new reader
    counts as not read."""
    first = [u for u in urls if offplan_url_signal(u) and u not in have_text]
    picked = set(first)
    rest = [u for u in urls if (u not in have_text if reread_old else u not in done) and u not in picked]
    return (first + rest)[:min(batch, max(0, cap_left))]


def today_count(done_log):
    """How many fetched today already, to respect the daily cap across runs."""
    if not done_log.exists():
        return 0
    today = datetime.date.today().isoformat()
    return sum(1 for ln in done_log.read_text(encoding="utf-8").splitlines() if ln.startswith(today + "\t"))


def run(label, sitemap, batch, reread_old=False):
    """One capped batch for one site. Returns "finished", "cap" (daily cap reached, more to
    do tomorrow) or "stopped: <reason>" (a block, challenge, bad status or second
    connection failure: the caller must not continue)."""
    print(f"\n===== {label}" + (" (re-reading old pages with the new reader)" if reread_old else ""))
    out = pg.BASE / label
    out.mkdir(parents=True, exist_ok=True)
    csv_file, done_log = out / "full_v2.csv", out / "done.log"
    try:
        urls, err = pg.collect_listing_urls(sitemap)
    except Exception as e:  # noqa: BLE001
        print(f"  could not read sitemap: {e!r}")
        return f"stopped: could not read sitemap ({e!r})"
    if err or not urls:
        print(f"  {err or 'no listing URLs'} — stopping")
        return f"stopped: {err or 'no listing URLs'}"

    done = set()
    if done_log.exists():
        for ln in done_log.read_text(encoding="utf-8").splitlines():
            parts = ln.split("\t")
            if len(parts) == 2:
                done.add(parts[1])
    have_text = set()
    if csv_file.exists():
        have_text = {r["url"] for r in csv.DictReader(open(csv_file, encoding="utf-8")) if r.get("reader") == READER}
    cap_left = DAILY_CAP - today_count(done_log)
    todo = plan_order(urls, done, have_text, batch, cap_left, reread_old)
    n_first = sum(1 for u in todo if offplan_url_signal(u) and u not in have_text)
    print(f"  {len(urls)} in sitemap, {len(done)} already done, daily cap left {cap_left}; this run: {len(todo)}"
          f" (off-plan/developer first: {n_first})")
    if not todo:
        left = plan_order(urls, done, have_text, 10**9, 10**9, reread_old)
        print("  nothing to do " + ("(daily cap reached)" if left else "(finished)"))
        return "cap" if left else "finished"

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
            soup = BeautifulSoup(r.content, "lxml")
            rec = pg.extract(u, soup)
            rec["source"] = label
            rec["ad_text"] = masked_text(soup)
            rec["reader"] = READER
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
    read_now = {r["url"] for r in rows}
    left = plan_order(urls, done | read_now, have_text | read_now, 10**9, 10**9, reread_old)
    print(f"  total done for {label}: {len(done | read_now)} / {len(urls)}; still to read: {len(left)}")
    if stopped:
        return f"stopped: {stopped}"
    return "cap" if left else "finished"


if __name__ == "__main__":
    batch = int(sys.argv[1])
    for arg in sys.argv[2:]:
        label, _, sm = arg.partition("=")
        run(label, sm, batch, reread_old=os.getenv("OLLAA_REREAD_OLD") == "1")
