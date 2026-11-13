"""
Runs the owner-approved scrape (13 Nov 2026) day after day until it is finished, within
the usual polite limits: honest user agent, random pauses, at most DAILY_CAP pages per site
per day, and a full stop at the first block, challenge, bad status or second connection
failure in a row (never bypassed, never retried beyond scrape_site's one retry).

Order: BetDelala (off-plan and developer adverts first, then the rest), then ethiopiarealty
re-read with the fixed price reader (8-15 s pauses). When the daily cap is reached it waits
until shortly after midnight and continues. It only writes local files; loading into the
database is a separate, checked step (etl/prepare_web_listings.py, etl/load_web_listings.py).

usage: python tools/run_until_done.py      (from ollaa-web-scraper; refuses without --live)
"""
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrape_site  # noqa: E402

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
    for label, sitemap, gmin, gmax, reread in PLAN:
        scrape_site.GAP_MIN, scrape_site.GAP_MAX = gmin, gmax
        while True:
            status = scrape_site.run(label, sitemap, scrape_site.DAILY_CAP, reread_old=reread)
            print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {label}: {status}", flush=True)
            if status == "finished":
                break
            if status.startswith("stopped"):
                print("STOPPED for good — not continuing with any site. Owner to decide.", flush=True)
                return 1
            wait_until_tomorrow()
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] ALL FINISHED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
