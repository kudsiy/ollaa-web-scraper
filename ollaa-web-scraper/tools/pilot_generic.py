"""Generic pilot for the GO sites (task W16): resolve a site's sitemap, sample ~30 listing
pages, read them politely and report how many have price / size / location. Read-only,
honest UA, paced; stops a site at the first block, challenge or error (never bypasses).
Price/size/location come from each page's ld+json (schema.org) when present, else from
visible text (price only when next to a currency word, so phone numbers are not mistaken
for prices) and the URL slug. Writes a local CSV per site (no phone numbers, no
descriptions; git-ignored). Prints fill rates only.

usage: pilot_generic.py <label>=<sitemap-url> [...]
"""
import csv
import json
import pathlib
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = pathlib.Path(r"C:\Projects\ollaa-web\ollaa-web-scraper\saved_pages")
UA = "OllaaResearch/0.1 (MSc thesis on Addis Ababa housing prices; read-only; low rate)"
GAP = 4
N = 30
MAX_CHILD = 6
STATIC = re.compile(r"(about|contact|privacy|terms|faq|blog|agent|login|register|wp-content|category|tag|author|page/)", re.I)
LISTING_HINT = re.compile(r"propert|listing|estate|home|house|apartment|villa|rent|sale|for-", re.I)
CHALLENGE = ("just a moment", "/cdn-cgi/challenge", "enable javascript and cookies", "attention required")
last = [0.0]


def get(url):
    w = GAP - (time.time() - last[0])
    if w > 0:
        time.sleep(w)
    r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
    last[0] = time.time()
    return r


def blocked(r):
    b = r.text[:3000].lower()
    return r.status_code in (403, 429, 503) or any(c in b for c in CHALLENGE)


def collect_listing_urls(sitemap_url):
    r = get(sitemap_url)
    if blocked(r):
        return None, f"blocked at sitemap (HTTP {r.status_code})"
    if r.status_code != 200:
        return None, f"sitemap HTTP {r.status_code}"
    if "<sitemapindex" in r.text:
        children = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", r.text)
        pick = [c for c in children if LISTING_HINT.search(c)] or children
        urls = []
        for c in pick[:MAX_CHILD]:
            rc = get(c)
            if rc.status_code == 200 and not blocked(rc):
                urls += re.findall(r"<loc>\s*([^<]+?)\s*</loc>", rc.text)
    else:
        urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", r.text)
    # keep listing-like, drop static
    good = [u for u in urls if u.count("/") >= 4 and not STATIC.search(u) and LISTING_HINT.search(u)]
    if not good:  # fall back: largest non-static set
        good = [u for u in urls if not STATIC.search(u) and u.count("/") >= 4]
    seen, uniq = set(), []
    for u in good:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq, None


def jsonld_objs(soup):
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string)
        except Exception:  # noqa: BLE001
            continue
        for o in (d if isinstance(d, list) else [d]):
            if isinstance(o, dict):
                yield o
                for g in o.get("@graph", []) if isinstance(o.get("@graph"), list) else []:
                    if isinstance(g, dict):
                        yield g


def place_from_url(url):
    """Pull a place name from a listing URL slug. Handles '...-in/at/near-<place>' (most
    WordPress sites) and BetDelala's '...-sqm-<place>-addis-ababa-ethiopia'."""
    slug = url.rstrip("/").split("/")[-1]
    m = (re.search(r"-(?:in|at|around|near)-([a-z0-9-]+)", slug)
         or re.search(r"-sqm-([a-z0-9-]+?)(?:-ethiopia)?$", slug))
    return m.group(1) if m else None


def num(x):
    try:
        v = float(re.sub(r"[^\d.]", "", str(x)))
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


def extract(url, soup):
    price = currency = size = beds = place = None
    text = soup.get_text(" ", strip=True)
    for o in jsonld_objs(soup):
        off = o.get("offers") if isinstance(o.get("offers"), dict) else {}
        price = price or num(off.get("price")) or num(o.get("price"))
        currency = currency or off.get("priceCurrency") or o.get("priceCurrency")
        fs = o.get("floorSize") if isinstance(o.get("floorSize"), dict) else {}
        size = size or num(fs.get("value"))
        beds = beds or num(o.get("numberOfRooms") or o.get("numberOfBedrooms"))
        addr = o.get("address")
        if isinstance(addr, dict):
            place = place or addr.get("addressLocality") or addr.get("streetAddress")
    if price is None:
        m = re.search(r"(?:ETB|Br|ብር)\s?([\d,]{4,})|([\d,]{4,})\s?(?:ETB|Br|ብር)", text, re.I)
        if m:
            price = num(m.group(1) or m.group(2))
            currency = currency or "ETB"
    if size is None:
        m = re.search(r"(\d{2,4})\s?(?:sqm|m²|m2|ካሬ)", text, re.I)
        size = num(m.group(1)) if m else None
    if beds is None:
        m = re.search(r"(\d{1,2})\s?(?:bed|bedroom|bdr|መኝታ)", text, re.I)
        beds = num(m.group(1)) if m else None
    if not place:
        place = place_from_url(url)
    if place:
        place = re.sub(r"\bethiopia\b", "", str(place), flags=re.I).replace("-", " ").strip()
        if re.fullmatch(r"[\d.\s]*", place):  # a bare number is not a place
            place = ""
    lt = "rent" if re.search(r"rent|ኪራይ", url, re.I) else ("rent" if (price and 1000 <= price <= 300000) else "sale")
    return {"url": url, "price": price or "", "currency": currency or "", "area_sqm": size or "",
            "bedrooms": beds or "", "place": (place or "").strip(), "listing_type": lt}


def pilot(label, sitemap_url):
    print(f"\n===== {label}")
    out = BASE / label
    out.mkdir(parents=True, exist_ok=True)
    try:
        urls, err = collect_listing_urls(sitemap_url)
    except Exception as e:  # noqa: BLE001
        print(f"  could not read sitemap: {e!r}")
        return
    if err:
        print(f"  {err} — skipping (not bypassing)")
        return
    if not urls:
        print("  no listing URLs found in sitemap")
        return
    step = max(1, len(urls) // N)
    sample = urls[::step][:N]
    print(f"  {len(urls)} listing URLs; sampling {len(sample)}")
    rows, stopped = [], None
    for i, u in enumerate(sample, 1):
        try:
            r = get(u)
        except Exception as e:  # noqa: BLE001
            stopped = f"error at #{i}: {e!r}"
            break
        if blocked(r):
            stopped = f"block/challenge at #{i} (HTTP {r.status_code}) — stopping, not bypassing"
            break
        if r.status_code != 200:
            stopped = f"HTTP {r.status_code} at #{i}"
            break
        rows.append(extract(u, BeautifulSoup(r.content, "lxml")))
    with open(out / "pilot.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["url", "price", "currency", "area_sqm", "bedrooms", "place", "listing_type"])
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    print(f"  parsed {n}" + (f"; STOPPED: {stopped}" if stopped else "; no blocks"))
    if n:
        p = lambda k: f"{sum(1 for r in rows if str(r[k]).strip())}/{n} ({100*sum(1 for r in rows if str(r[k]).strip())//n}%)"
        print(f"    price {p('price')} | size {p('area_sqm')} | location {p('place')} | bedrooms {p('bedrooms')}")
        full = sum(1 for r in rows if r["price"] and r["area_sqm"] and r["place"])
        cur = {}
        for r in rows:
            cur[r["currency"] or "?"] = cur.get(r["currency"] or "?", 0) + 1
        print(f"    price+size+location: {full}/{n} ({100*full//n}%) | currencies {cur}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        label, _, sm = arg.partition("=")
        pilot(label, sm)
