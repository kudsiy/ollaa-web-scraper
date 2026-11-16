"""
Prepare the scraped listings for the database (task W16/W17). Offline: reads the local
scrape files, touches no database and no website.

- Reads `saved_pages/<site>/full.csv` (old reader) and `full_v2.csv` (new reader, with the
  masked advert text); for the same web address the newest row wins.
- Adds advert texts kept elsewhere on the laptop (`saved_pages/_load/ad_texts_backfill.csv`,
  masked) to rows that have none.
- Finds the neighbourhood with the sister project's place list (`locations.py` in the folder
  named by SISTER_PLACES_DIR in `.env`, imported read-only) and turns it
  into a sub-city with `data/neighbourhood_subcity.csv`. **The owner's column in that file
  always wins** (owner, 13 Nov 2026: the thesis uses the official Bole Sub-City boundary).
- Reads the off-plan terms from the advert text (parsers/offplan_terms.py).
- Gives adverts that describe the same property the same `property_group` (same sale/rent,
  price and place, and the same size or bedrooms where both are known; plus the links in
  `data/same_property_links.csv`), so their terms can be read together.
- Drops exact repeats within a site (same type, place, price and size: keeps the most
  complete copy), and flags probable cross-site duplicates, as in the first load.

Writes `saved_pages/_load/web_listings_loadready.csv` (git-ignored) and refreshes
`data/neighbourhood_subcity.csv` (keeping the owner's corrections).

usage: python etl/prepare_web_listings.py
"""
import csv
import hashlib
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parsers.contact_mask import has_contact, mask_contacts  # noqa: E402
from parsers.offplan_terms import TEXT_JOIN, is_offplan, offplan_url_signal, terms_for  # noqa: E402

PAGES = ROOT / "saved_pages"
OUT = PAGES / "_load"
DATA = ROOT / "data"
MAP_FILE = DATA / "neighbourhood_subcity.csv"
LINKS_FILE = DATA / "same_property_links.csv"
RULES_FILE = DATA / "subcity_rules.csv"     # owner's rules: names starting with ... are in sub-city ...
EXTRA_FILE = DATA / "extra_places.csv"      # place names the owner uses that the place list lacks
BACKFILL = OUT / "ad_texts_backfill.csv"
SOURCES = ["betdelala", "ethiopiarealty"]
PTYPES = [("apartment", r"apartment|flat|condo|አፓርት|ኮንዶ"), ("house", r"house|villa|home|ቤት|ቪላ|g\+\d"),
          ("office", r"office|ቢሮ"), ("shop", r"shop|store|ሱቅ"), ("land", r"land|plot|ቦታ|መሬት"),
          ("building", r"building|ህንፃ|ሕንፃ")]
MAP_FIELDS = ["neighbourhood", "location_code", "sub_city_used", "owner_rule", "place_list_sub_city", "unsure",
              "why_unsure",
              "offplan_or_developer_adverts", "owner_sub_city", "owner_note"]

# Claude's notes on names that may sit in more than one sub-city, or that the place list
# puts somewhere Claude is not sure of. Only a starting point: the owner decides.
UNSURE = {
    "ayat_zone": "Ayat spreads over Bole, Yeka and (since 2020) Lemi Kura; depends on the zone/site",
    "ayat_49": "Ayat sites: Bole, Yeka or Lemi Kura depending on the site",
    "ayat_mekdonia": "Ayat sites: Bole, Yeka or Lemi Kura depending on the site",
    "cmc_michael": "CMC is usually Yeka, but some CMC-area sites are on the Bole side",
    "summit": "Summit / Figa area: not set in the place list; Bole or Yeka",
    "summit_72": "Summit area: Bole or Yeka", "summit_figa": "Summit / Figa: Bole or Yeka",
    "figa": "Figa: Bole or Yeka", "figa_mebrat": "Figa: Bole or Yeka",
    "megenagna": "Megenagna is on the Yeka / Bole / Kirkos border",
    "imperial": "Imperial is near the Bole / Yeka border",
    "gerji": "Gerji: the place list says Yeka; much of Gerji may be Bole",
    "haya_hulet": "22 (Haya Hulet) is on the Bole / Yeka / Kirkos border",
    "urael": "Urael is on the Bole / Kirkos border",
    "meskel_flower": "Meskel Flower is on the Kirkos / Bole border",
    "wello_sefer": "Wello Sefer: Kirkos or Bole; not set in the place list",
    "bulgaria": "Bulgaria: Kirkos or Nifas Silk; not set in the place list",
    "dembel": "Dembel (Bole road): Kirkos or Bole; not set in the place list",
    "bole_arabsa": "Arabsa may now be in Lemi Kura",
    "bole_lemi": "Bole Lemi may now be in Lemi Kura",
    "bole_lemi_industrial": "Bole Lemi industrial park may now be in Lemi Kura",
    "bole_bulbula": "Bulbula is at the edge of Bole (Akaki-Kality border)",
    "mexico": "Mexico square is on the Kirkos / Lideta border",
    "sengatera": "Senga Tera: Kirkos or Lideta",
    "sarbet_old_airport": "Sarbet / Old Airport: Nifas Silk-Lafto or Kolfe",
    "lebu": "Lebu: the place list says Kolfe; may be Nifas Silk-Lafto",
    "lebu_varnero": "Lebu: the place list says Kolfe; may be Nifas Silk-Lafto",
    "jemo": "Jemo: the place list says Kolfe; may be Nifas Silk-Lafto",
    "gelan": "Gelan condominiums: run by Addis but lie in Oromia (Sheger)",
    "tulu_dimtu": "Tulu Dimtu: Akaki-Kality or Bole; not set in the place list",
    "bole_main": "'Bole' alone may mean the Bole road / airport area rather than the sub-city",
}
for code in ("german", "signal", "bethel", "kebena", "lamberet", "awareness", "jacros", "wesen", "hiya",
             "enkulal_fabrica", "ambassador", "alem_bank", "atena_tera", "la_gare", "7kilo", "teklehaimanot",
             "addisu_gebeya", "salite_mehret", "mikililand", "addis_sefer", "haile_garment", "garment",
             "pastor_medhanialem", "medhanialem", "bisrate_gabriel", "alem_gena", "jarsso", "gofa",
             "addis_industrial", "awere"):
    UNSURE.setdefault(code, "no sub-city in the place list")


def _locations():
    """The sister project's place list, imported read-only from SISTER_PLACES_DIR (.env)."""
    import os  # noqa: PLC0415
    from config import ENV_FILE  # noqa: PLC0415  (loads .env)
    folder = os.getenv("SISTER_PLACES_DIR", "")
    if not folder or not pathlib.Path(folder, "locations.py").exists():
        raise SystemExit(f"Set SISTER_PLACES_DIR in {ENV_FILE} to the folder holding the sister project's locations.py")
    sys.path.insert(0, folder)
    import locations as L  # noqa: PLC0415 (sister project's file, read only)
    return L


def fnum(x):
    try:
        v = float(re.sub(r"[^\d.]", "", str(x)))
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


def slug_words(url):
    slug = url.rstrip("/").split("/")[-1]
    slug = re.sub(r"\b\d+\s?(?:bedroom|bed|sqm|m2)\b", " ", slug)
    return re.sub(r"[-_]+", " ", slug)


def ptype(text):
    for name, pat in PTYPES:
        if re.search(pat, text, re.I):
            return name
    return ""


def place_list_sub_city(L, code):
    p = L.PLACES.get(code)
    while p is not None:
        if p.sub_city:
            return p.sub_city
        p = L.PLACES.get(p.parent) if p.parent else None
    return ""


def read_rules():
    """Owner's prefix rules, longest prefix first (so 'bole arabsa' beats 'bole')."""
    if not RULES_FILE.exists():
        return []
    rules = [r for r in csv.DictReader(open(RULES_FILE, encoding="utf-8")) if r["name_starts_with"].strip()]
    return sorted(rules, key=lambda r: -len(r["name_starts_with"].strip()))


def read_extras():
    if not EXTRA_FILE.exists():
        return []
    return [(r["name"], re.compile(r["pattern"], re.I)) for r in csv.DictReader(open(EXTRA_FILE, encoding="utf-8"))]


def extra_code(name):
    return "extra_" + re.sub(r"\W+", "_", name.lower()).strip("_")


def place_name(L, code, extras):
    if code in L.PLACES:
        return L.PLACES[code].name
    for name, _ in extras:
        if extra_code(name) == code:
            return name
    return ""


def find_code(L, where, text, extras):
    """Owner's extra names first, then the place list; the advert text only if the web
    address and place field name no place."""
    for source in (where, text[:600] if text else ""):
        if not source:
            continue
        for name, rx in extras:
            if rx.search(source):
                return extra_code(name)
        code = L.find_location(source)
        if code not in (L.UNKNOWN, L.NOISE, None):
            return L.canonical(code) if hasattr(L, "canonical") else code
    return L.find_location(where)


def decide_sub_city(L, code, mapping, rules, extras):
    """(sub_city, unsure, why, rule): the owner's own cell in the table wins, then the
    owner's prefix rules, then the place list."""
    m = mapping.get(code, {})
    own = (m.get("owner_sub_city") or "").strip()
    if own:
        return own, False, "", "owner's table cell"
    name = place_name(L, code, extras).lower()
    words = (code or "").replace("_", " ").lower()
    for r in rules:
        prefix = r["name_starts_with"].strip().lower()
        if name.startswith(prefix) or words.startswith(prefix):
            sub = r["sub_city"].strip()
            return sub, not sub, ("" if sub else r["note"]), f"starts with '{prefix}'"
    return place_list_sub_city(L, code), code in UNSURE, UNSURE.get(code, ""), ""


def read_map():
    if not MAP_FILE.exists():
        return {}
    return {r["location_code"]: r for r in csv.DictReader(open(MAP_FILE, encoding="utf-8"))}


def read_rows():
    """Newest row per (site, web address); v2 rows (with masked text) win over old ones."""
    rows = {}
    for src in SOURCES:
        for name in ("full.csv", "full_v2.csv"):
            f = PAGES / src / name
            if not f.exists():
                continue
            for r in csv.DictReader(open(f, encoding="utf-8")):
                r = dict(r, source=src)
                r["ad_text"] = mask_contacts(r.get("ad_text") or "")
                if has_contact(r["ad_text"]):
                    r["ad_text"] = ""
                key = (src, r["url"])
                old = rows.get(key)
                if old is None or name == "full_v2.csv" or (r.get("scraped_at", "") >= old.get("scraped_at", "")
                                                            and not old.get("reader")):
                    rows[key] = r
    if BACKFILL.exists():
        same = lambda u: re.sub(r"^https?://(www\.)?", "", u).rstrip("/")  # noqa: E731
        texts = {same(r["source_url"]): mask_contacts(r["ad_text"])
                 for r in csv.DictReader(open(BACKFILL, encoding="utf-8"))}
        for r in rows.values():
            tx = texts.get(same(r["url"]))
            if not r["ad_text"] and tx and not has_contact(tx):
                r["ad_text"] = tx
    return list(rows.values())


def build(rows, L, mapping, rules=(), extras=()):
    out = []
    for r in rows:
        url, text = r["url"], r.get("ad_text") or ""
        where = f"{r.get('place', '')} {slug_words(url)}"
        code = find_code(L, where, text, extras)
        sub, unsure, _, _ = decide_sub_city(L, code, mapping, rules, extras)
        coords = L.coordinates(code) or (None, None, None)
        terms = terms_for(text, url) if text else {}
        rec = {
            "source": r["source"], "source_url": url,
            "price": fnum(r.get("price")) or "", "currency": r.get("currency") or "ETB",
            "listing_type": r.get("listing_type") or "", "property_type": ptype(f"{where} {text[:200]}"),
            "area_sqm": fnum(r.get("area_sqm")) or "",
            "bedrooms": int(fnum(r.get("bedrooms"))) if fnum(r.get("bedrooms")) else "",
            "location_code": code or "", "neighbourhood": place_name(L, code, extras),
            "sub_city": sub, "sub_city_unsure": "yes" if unsure else "",
            "city": "ADDIS_ABABA" if str(code).startswith("extra_") else L.city_of(code), "latitude": coords[0] or "", "longitude": coords[1] or "",
            "scraped_at": r.get("scraped_at") or "", "reader": r.get("reader") or "", "ad_text": text,
            "content_hash": hashlib.sha256(f"{r['source']}|{url}".encode()).hexdigest(),
            "_terms": terms,
        }
        out.append(rec)
    return out


# Owner, 16 Nov 2026: some sale adverts put a PRICE PER m2 in the site's price box (e.g.
# 90,000 birr for a flat). Such a number is stored as price_per_m2, never as the total; if
# the size is known the total is calculated and marked "calculated from price per m2".
PPM_LOW, PPM_HIGH = 20_000, 400_000          # birr per m2 for Addis homes
SIZE_LOW, SIZE_HIGH = 15, 1_000              # m2 sizes trusted for the calculation
SALE_WORDS = re.compile(r"for[\s-]*sa(?:le|ll)|for[\s-]*sell|ሽያጭ|የሚሸጥ|ይሸጣል|down[\s-]?payment|ቅድመ\s*ክፍያ", re.I)
RENT_WORDS = re.compile(r"for[\s-]*rent|ኪራይ|የሚከራይ|ለኪራይ|per\s+month|/\s*month|በወር", re.I)
BASIS_TOTAL = "total as advertised"
BASIS_CALC = "calculated from price per m2"
BASIS_PPM_ONLY = "price per m2 only (no size)"


def is_price_per_m2(rec):
    """True when the advertised 'price' is really a price per m2 (see above)."""
    if rec["source"] == "ethiopiarealty" and not rec["reader"]:
        return False                                     # old-reader price: wrong anyway, flagged
    p = rec["price"]
    if not p or not (PPM_LOW <= p <= PPM_HIGH):
        return False
    text = f"{rec['ad_text']} {slug_words(rec['source_url'])}"
    if RENT_WORDS.search(text):
        return False
    terms = rec.get("_terms") or {}
    stated = terms.get("stated_price_per_m2")
    return bool(SALE_WORDS.search(text) or (stated and abs(float(stated) - p) < 1) or is_offplan(terms))


def apply_price_basis(rec):
    """Set price_basis / price_per_m2 / price_as_advertised; fix price and sale/rent."""
    rec["price_as_advertised"] = rec["price"]
    rec["price_per_m2"] = ""
    rec["price_basis"] = BASIS_TOTAL if rec["price"] else ""
    if is_price_per_m2(rec):
        ppm = rec["price"]
        rec["price_per_m2"] = ppm
        rec["listing_type"] = "sale"
        size = rec["area_sqm"]
        if size and SIZE_LOW <= size <= SIZE_HIGH:
            rec["price"] = round(ppm * size, 2)
            rec["price_basis"] = BASIS_CALC
        else:
            rec["price"] = ""
            rec["price_basis"] = BASIS_PPM_ONLY
    return rec


def drop_exact_repeats(rows):
    """Same site, type, place, price and size: keep the most complete copy, and give it the
    advert texts of all the copies (so no copy's terms are lost). Returns the kept rows and
    a list of (repeat's content_hash, kept copy's content_hash): repeats already in the
    database get flagged `exact_repeat` by the loader; nothing is deleted."""
    def score(r):
        return (bool(r["reader"]), bool(r["ad_text"]), sum(1 for k in ("bedrooms", "area_sqm", "price") if r[k]))
    best, texts, members = {}, defaultdict(list), defaultdict(list)
    for r in rows:
        old_bad_price = r["source"] == "ethiopiarealty" and not r["reader"]  # every price was 3,433
        if old_bad_price or not (r["price"] and r["area_sqm"]):
            best[("_single", r["content_hash"])] = r
            continue
        k = (r["source"], r["listing_type"], r["property_type"], r["location_code"], r["price"], r["area_sqm"])
        members[k].append(r["content_hash"])
        if r["ad_text"] and r["ad_text"] not in texts[k]:
            texts[k].append(r["ad_text"])
        if k not in best or score(r) > score(best[k]):
            best[k] = r
    for k, r in best.items():
        if len(texts.get(k, [])) > 1:
            r["ad_text"] = TEXT_JOIN.join(texts[k])
            r["_terms"] = terms_for(r["ad_text"], r["source_url"])
    repeats = [(h, best[k]["content_hash"]) for k, hs in members.items() for h in hs if h != best[k]["content_hash"]]
    return list(best.values()), repeats


def group_same_property(rows):
    """Union adverts that describe the same property; returns {content_hash: group id}."""
    parent = {r["content_hash"]: r["content_hash"] for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    buckets = defaultdict(list)
    for r in rows:
        if r["source"] == "ethiopiarealty" and not r["reader"]:
            continue  # old-reader price is wrong: never group on it
        if r["price"] and r["location_code"] not in ("", "other_addis", "noise"):
            buckets[(r["listing_type"], r["price"], r["location_code"])].append(r)
    for group in buckets.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                same_size = a["area_sqm"] and a["area_sqm"] == b["area_sqm"]
                same_beds = a["bedrooms"] and a["bedrooms"] == b["bedrooms"]
                beds_unknown = not a["bedrooms"] or not b["bedrooms"]
                if same_size or same_beds or (beds_unknown and (a["ad_text"] or b["ad_text"])):
                    union(a["content_hash"], b["content_hash"])
    if LINKS_FILE.exists():
        by_url = {r["source_url"]: r["content_hash"] for r in rows}
        for link in csv.DictReader(open(LINKS_FILE, encoding="utf-8")):
            a, b = by_url.get(link["url_a"]), by_url.get(link["url_b"])
            if a and b:
                union(a, b)
    return {h: find(h)[:16] for h in parent}


def write_map(rows, L, mapping, extra_urls=(), rules=(), extras=()):
    """Every neighbourhood named in off-plan / developer adverts (scraped, or only known
    from the sitemap address so far), with the sub-city used; keeps the owner's columns."""
    counts = Counter()
    for r in rows:
        t = r["_terms"]
        if is_offplan(t) or t.get("developer") or offplan_url_signal(r["source_url"]):
            counts[r["location_code"]] += 1
    seen = {r["source_url"] for r in rows}
    for u in extra_urls:
        if u not in seen and offplan_url_signal(u):
            counts[find_code(L, slug_words(u), "", extras)] += 1
    lines = []
    for code, n in counts.most_common():
        if code in ("", L.UNKNOWN, L.NOISE):
            continue
        old = mapping.get(code, {})
        owner = (old.get("owner_sub_city") or "").strip()
        used, unsure, why, rule = decide_sub_city(L, code, mapping, rules, extras)
        lines.append({
            "neighbourhood": place_name(L, code, extras) or code, "location_code": code,
            "sub_city_used": used, "owner_rule": rule, "place_list_sub_city": place_list_sub_city(L, code),
            "unsure": "yes" if unsure else "", "why_unsure": why,
            "offplan_or_developer_adverts": n, "owner_sub_city": owner, "owner_note": old.get("owner_note", ""),
        })
    for code, old in mapping.items():  # keep rows the owner already edited, even if no advert now
        if code not in counts and (old.get("owner_sub_city") or old.get("owner_note")):
            lines.append(dict(old, offplan_or_developer_adverts=0))
    DATA.mkdir(exist_ok=True)
    with open(MAP_FILE, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MAP_FIELDS)
        w.writeheader()
        w.writerows(lines)
    return lines


def sitemap_urls(site="betdelala"):
    f = PAGES / site / "sitemap.xml"
    if not f.exists():
        return []
    return [u for u in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", f.read_text(encoding="utf-8")) if "/property/" in u]


OUT_FIELDS = ["source", "source_url", "price", "price_basis", "price_as_advertised", "price_per_m2", "currency",
              "listing_type", "property_type", "area_sqm", "bedrooms",
              "location_code", "neighbourhood", "sub_city", "sub_city_unsure", "city", "latitude", "longitude",
              "probable_dup", "property_group", "content_hash", "scraped_at", "reader", "ad_text"]


def main():
    L = _locations()
    mapping, rules, extras = read_map(), read_rules(), read_extras()
    rows = build(read_rows(), L, mapping, rules, extras)
    write_map(rows, L, mapping, sitemap_urls(), rules, extras)
    mapping = read_map()  # owner columns kept; rebuild sub-cities with the refreshed file
    rows = build(read_rows(), L, mapping, rules, extras)
    rows = [apply_price_basis(r) for r in rows]
    rows, repeats = drop_exact_repeats(rows)
    dropped = len(repeats)
    groups = group_same_property(rows)
    with open(OUT / "web_listings_repeats.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["content_hash", "kept_content_hash", "kept_property_group"])
        w.writerows((h, kept, groups[kept]) for h, kept in repeats)
    key = lambda r: (r["listing_type"], r["property_type"], r["price"], r["area_sqm"], r["bedrooms"], r["location_code"])
    usable = [r for r in rows if r["price"] and r["area_sqm"] and not (r["source"] == "ethiopiarealty" and not r["reader"])]
    multi = {k for k, c in Counter(key(r) for r in usable).items() if c > 1}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "web_listings_loadready.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        w.writeheader()
        for r in rows:
            r["probable_dup"] = "yes" if key(r) in multi and r in usable else ""
            r["property_group"] = groups[r["content_hash"]]
            w.writerow({k: r.get(k, "") for k in OUT_FIELDS})
    with_text = sum(1 for r in rows if r["ad_text"])
    print(f"prepared {len(rows)} rows ({dropped} exact repeats dropped); with advert text: {with_text}; "
          f"neighbourhood table: {MAP_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
