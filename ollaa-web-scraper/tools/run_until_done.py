"""
Runs the owner-approved scrape (13 Nov 2026) day after day until it is finished, within
the usual polite limits: honest user agent, random pauses, at most DAILY_CAP pages per site
per day, and a full stop at the first block, challenge, bad status or second connection
failure in a row (never bypassed, never retried beyond scrape_site's one retry).

Order: BetDelala (off-plan and developer adverts first, then the rest), then ethiopiarealty
re-read with the fixed price reader (8-15 s pauses). When the daily cap is reached it waits
until shortly after midnight and continues. It only writes local files; loading into the
database is a separate, checked step (etl/prepare_web_listings.py, etl/load_web_listings.py).

A stop is final: the runner writes saved_pages/SCRAPE_STOPPED.txt (and SCRAPE_FINISHED.txt
when all is done) and refuses to start while either file exists, so the at-logon restart
(tools/start_scrape.ps1, owner approved 15 Nov 2026) can never retry after a block. Only the
owner (or Claude, on the owner's word after checking the reason) removes the file.

Daily mode (owner, 16 Nov 2026): with --once it does one day's share and exits, adding a
line to saved_pages/daily_log.csv (date, site, pages read, new listings, re-reads, still to
read, status, error). The Windows task "OllaaWebScrape" runs it once a day at a fixed time
through tools/start_scrape.ps1, which first waits for the internet.

usage: python tools/run_until_done.py --live [--once]      (from ollaa-web-scraper)
"""
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrape_site  # noqa: E402

STOP_FILE = scrape_site.pg.BASE / "SCRAPE_STOPPED.txt"
DAILY_LOG = scrape_site.pg.BASE / "daily_log.csv"
RUN_STARTED = None
LOG_FIELDS = ["date", "time", "site", "pages_read", "new_listings", "re_reads", "still_to_read", "status", "error"]


def log_day(status):
    """One short line per site per run in saved_pages/daily_log.csv."""
    import csv  # noqa: PLC0415
    r = scrape_site.LAST_RUN
    now = RUN_STARTED or datetime.datetime.now()  # the day the run started counts as its day
    new_file = not DAILY_LOG.exists()
    with open(DAILY_LOG, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow({"date": f"{now:%Y-%m-%d}", "time": f"{now:%H:%M}", "site": r.get("site", ""),
                    "pages_read": r.get("read", 0), "new_listings": r.get("new", 0), "re_reads": r.get("reread", 0),
                    "still_to_read": r.get("left", ""), "status": status.split(":")[0],
                    "error": (r.get("error") or "")[:200]})


DONE_FILE = scrape_site.pg.BASE / "SCRAPE_FINISHED.txt"

PLAN = [
    # label, sitemap, gap min, gap max, re-read pages read by the old reader
    ("betdelala", "https://betdelala.com/sitemap.xml", 3, 6, False),
    ("ethiopiarealty", "https://ethiopiarealty.com/wp-sitemap.xml", 8, 15, True),
]


def wait_until_tomorrow():
    now = datetime.datetime.now()
    start = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(0, 10))
    print(f"[{now:%Y-%m-%d %H:%M}] daily cap reached; waiting until {start:%Y-%m-%d %H:%M}", flush=True)
    while datetime.datetime.now() < start:
        time.sleep(min(600, max(1, (start - datetime.datetime.now()).total_seconds())))


def main():
    if "--live" not in sys.argv:
        print("This visits live websites. Run it only with the owner's approval, adding --live.")
        return 2
    global RUN_STARTED
    RUN_STARTED = datetime.datetime.now()
    for marker in (STOP_FILE, DONE_FILE):
        if marker.exists():
            print(f"Not starting: {marker.name} exists ({marker.read_text(encoding='utf-8').strip()[:200]}).")
            return 3
    for label, sitemap, gmin, gmax, reread in PLAN:
        scrape_site.GAP_MIN, scrape_site.GAP_MAX = gmin, gmax
        while True:
            status = scrape_site.run(label, sitemap, scrape_site.DAILY_CAP, reread_old=reread)
            print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {label}: {status}", flush=True)
            log_day(status)
            if status == "finished":
                break
            if status.startswith("stopped"):
                print("STOPPED for good — not continuing with any site. Owner to decide.", flush=True)
                STOP_FILE.write_text(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {label}: {status}\n", encoding="utf-8")
                return 1
            if "--once" in sys.argv:
                print("daily share done; the next run is tomorrow at the fixed time", flush=True)
                return 0
            wait_until_tomorrow()
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] ALL FINISHED", flush=True)
    DONE_FILE.write_text(f"{datetime.datetime.now():%Y-%m-%d %H:%M} all sites finished\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
