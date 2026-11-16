"""Load the cleaned multi-site listings into a NEW table `web_listings` in the shared `ollaa`
database (task W16, step 4). Safe by design:

- It only CREATEs a new table and INSERTs rows (ON CONFLICT DO NOTHING). It never changes,
  removes or reads the sister project's own tables, and contains no delete/drop of data.
- It connects as the everyday login `ollaa_user` (via config / .env); it refuses `postgres`.
- Re-running it loads nothing twice: each row is keyed by content_hash.

Since 13 Nov 2026 the table also holds each advert's text with contacts masked
(`ad_text_masked`) and the off-plan terms read from it (parsers/offplan_terms.py), and
flags rows whose price must not be used (`price_unusable`, `price_note`). Rows from
ethiopiarealty read by the old reader (no `reader` value) are always flagged: their price
came from the site's search form (bug found 13 Nov 2026), so they wait for a re-scrape.
`--upgrade` only adds the new columns and applies that flag, without loading a CSV.

Run `python etl/load_web_listings.py` to VALIDATE only (reads the CSV, prints the table
definition and the row count, touches no database). Run with `--apply` to actually create
the table and load the rows. The owner approves the --apply run, and a backup is taken
first (see CLAUDE.md). The CSV holds structured fields only — no phone numbers.
"""
import argparse
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from etl.db_writer import DBWriter  # reuses the everyday-login / no-postgres guard  # noqa: E402
from parsers.contact_mask import has_contact, mask_contacts  # noqa: E402
from parsers.offplan_terms import terms_for  # noqa: E402

DEFAULT_CSV = pathlib.Path(__file__).resolve().parent.parent / "saved_pages" / "_load" / "web_listings_loadready.csv"
TABLE = "web_listings"
DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id            SERIAL PRIMARY KEY,
    source        VARCHAR(40),
    source_url    TEXT,
    price         NUMERIC(15,2),
    currency      VARCHAR(8),
    listing_type  VARCHAR(16),
    property_type VARCHAR(32),
    area_sqm      NUMERIC(10,2),
    bedrooms      INTEGER,
    location_code VARCHAR(64),
    sub_city      VARCHAR(64),
    city          VARCHAR(64),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    probable_dup  BOOLEAN DEFAULT FALSE,
    content_hash  VARCHAR(64) UNIQUE,
    scraped_at    TIMESTAMP,
    loaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
# Added 13 Nov 2026 (thesis fields). ADD COLUMN IF NOT EXISTS: safe to run again.
NEW_COLUMNS = [
    ("reader", "VARCHAR(32)"),
    ("price_unusable", "BOOLEAN DEFAULT FALSE"),
    ("price_note", "TEXT"),
    ("ad_text_masked", "TEXT"),
    ("developer", "TEXT"),
    ("construction_status", "TEXT"),
    ("construction_progress_pct", "NUMERIC(5,1)"),
    ("finish_level", "TEXT"),
    ("down_payment_pct", "NUMERIC(5,1)"),
    ("down_payment_amount", "NUMERIC(15,2)"),
    ("instalment_plan", "TEXT"),
    ("stage_linked", "BOOLEAN"),
    ("bank_loan", "TEXT"),
    ("handover", "TEXT"),
    ("discount_schedule", "TEXT"),
    ("stated_price_per_m2", "NUMERIC(12,2)"),
    ("price_per_m2_semi", "NUMERIC(12,2)"),
    ("price_per_m2_full", "NUMERIC(12,2)"),
    ("has_payment_terms", "BOOLEAN"),
    ("neighbourhood", "TEXT"),
    ("sub_city_unsure", "BOOLEAN"),
    ("property_group", "VARCHAR(16)"),
    ("exact_repeat", "BOOLEAN DEFAULT FALSE"),
    ("price_basis", "TEXT"),
    ("price_as_advertised", "NUMERIC(15,2)"),
    ("price_per_m2", "NUMERIC(12,2)"),
]
TERM_COLS = ["developer", "construction_status", "construction_progress_pct", "finish_level", "down_payment_pct",
             "down_payment_amount", "instalment_plan", "stage_linked", "bank_loan", "handover", "discount_schedule",
             "stated_price_per_m2", "price_per_m2_semi", "price_per_m2_full", "has_payment_terms"]
BASE_COLS = ["source", "source_url", "price", "price_basis", "price_as_advertised", "price_per_m2", "currency", "listing_type", "property_type", "area_sqm",
             "bedrooms", "location_code", "neighbourhood", "sub_city", "sub_city_unsure", "city", "latitude",
             "longitude", "probable_dup", "property_group", "content_hash", "scraped_at"]
YES_NO = ("probable_dup", "sub_city_unsure")
COLS = BASE_COLS + ["reader", "ad_text_masked"] + TERM_COLS
OLD_READER_NOTE = ("price taken from the site's search form by the old reader (bug found 13 Nov 2026); "
                   "do not use until re-scraped with the fixed reader")
MARK_OLD_ETHIOPIAREALTY = (f"UPDATE {TABLE} SET price_unusable = TRUE, price_note = %s "
                           f"WHERE source = 'ethiopiarealty' AND reader IS NULL AND price_unusable IS NOT TRUE")


def row_values(r):
    """One CSV row -> a tuple in COLS order. The advert text is masked again here, and a row
    whose text would still hold a contact is stored without text."""
    base = [(r.get(c) or None) if c not in YES_NO else (r.get(c) == "yes") for c in BASE_COLS]
    # a few web addresses carry the agent's phone number in them: store the address masked
    # (content_hash, made from the full address before loading, still identifies the row)
    i = BASE_COLS.index("source_url")
    base[i] = mask_contacts(base[i]) if base[i] else base[i]
    text = mask_contacts(r.get("ad_text") or r.get("ad_text_masked") or "")
    if has_contact(text):
        text = ""
    terms = terms_for(text, r.get("source_url") or "") if text else {}
    return tuple(base + [r.get("reader") or None, text or None] + [terms.get(c) for c in TERM_COLS])


# Re-loading a web address already in the table updates it instead of skipping it:
# - place, sub-city, neighbourhood and same-property group always follow the latest mapping
#   (so the owner's sub-city corrections reach the table);
# - advert text and terms are replaced only when the new row has text;
# - price, size and the rest only when the new row was read by the new reader, which also
#   clears the "price unusable" flag. Nothing is ever deleted.
# price and sale/rent follow the preparation step (owner, 16 Nov 2026: a price per m2 in
# the price box is never a total), so they are updated on every load as well
_ALWAYS = ["source_url", "price", "price_basis", "price_as_advertised", "price_per_m2", "listing_type", "property_type", "location_code", "neighbourhood", "sub_city", "sub_city_unsure", "city", "latitude",
           "longitude", "probable_dup", "property_group"]
_IF_READER = ["currency", "area_sqm", "bedrooms", "scraped_at", "reader"]
UPSERT = (
    f"INSERT INTO {TABLE} ({','.join(COLS)}) VALUES %s ON CONFLICT (content_hash) DO UPDATE SET "
    + ", ".join(f"{c} = EXCLUDED.{c}" for c in _ALWAYS) + ", "
    + "ad_text_masked = COALESCE(EXCLUDED.ad_text_masked, {t}.ad_text_masked), ".format(t=TABLE)
    + ", ".join(f"{c} = CASE WHEN EXCLUDED.ad_text_masked IS NOT NULL THEN EXCLUDED.{c} ELSE {TABLE}.{c} END"
                for c in TERM_COLS) + ", "
    + ", ".join(f"{c} = CASE WHEN EXCLUDED.reader IS NOT NULL THEN EXCLUDED.{c} ELSE {TABLE}.{c} END"
                for c in _IF_READER) + ", "
    + f"price_unusable = CASE WHEN EXCLUDED.reader IS NOT NULL THEN FALSE ELSE {TABLE}.price_unusable END, "
    + f"price_note = CASE WHEN EXCLUDED.reader IS NOT NULL THEN NULL ELSE {TABLE}.price_note END"
)
# One row per property for the thesis: adverts of the same property (property_group) read
# together. Prices from rows flagged price_unusable are left out.
VIEW = f"""
CREATE OR REPLACE VIEW web_offplan_properties AS
SELECT property_group,
       COUNT(*)                                                   AS adverts,
       string_agg(DISTINCT source_url, ' | ')                     AS web_addresses,
       string_agg(DISTINCT sub_city, ' / ')                       AS sub_city,
       bool_or(sub_city_unsure)                                   AS sub_city_unsure,
       string_agg(DISTINCT neighbourhood, ' / ')                  AS neighbourhood,
       string_agg(DISTINCT developer, ' / ')                      AS developer,
       string_agg(DISTINCT construction_status, ' / ')            AS construction_status,
       bool_or(construction_status LIKE '%under construction%' OR construction_status LIKE '%probably off-plan%') AS offplan,
       string_agg(DISTINCT finish_level, ' / ')                   AS finish_level,
       MAX(price) FILTER (WHERE NOT COALESCE(price_unusable, FALSE)) AS price,
       MAX(area_sqm)                                              AS area_sqm,
       MAX(bedrooms)                                              AS bedrooms,
       MAX(down_payment_pct)                                      AS down_payment_pct,
       string_agg(DISTINCT instalment_plan, ' / ')                AS instalment_plan,
       bool_or(stage_linked)                                      AS stage_linked,
       string_agg(DISTINCT bank_loan, ' / ')                      AS bank_loan,
       string_agg(DISTINCT handover, ' / ')                       AS handover,
       string_agg(DISTINCT discount_schedule, ' / ')              AS discount_schedule,
       MAX(stated_price_per_m2)                                   AS stated_price_per_m2,
       MAX(price_per_m2_semi)                                     AS price_per_m2_semi,
       MAX(price_per_m2_full)                                     AS price_per_m2_full,
       bool_or(has_payment_terms)                                 AS has_payment_terms,
       -- added 16 Nov 2026 (new view columns can only go at the end)
       string_agg(DISTINCT price_basis, ' / ')                    AS price_basis,
       MAX(price_per_m2)                                          AS price_per_m2_advertised
FROM {TABLE}
WHERE ad_text_masked IS NOT NULL AND property_group IS NOT NULL AND NOT COALESCE(exact_repeat, FALSE)
GROUP BY property_group;
"""


# A row already in the table that the preparation step now treats as a repeat copy of a
# fuller advert (same site, type, place, price and size) is flagged, never deleted.
MARK_REPEAT = (f"UPDATE {TABLE} SET exact_repeat = TRUE, property_group = %s "
               f"WHERE content_hash = %s AND exact_repeat IS NOT TRUE")
REPEATS_CSV = DEFAULT_CSV.parent / "web_listings_repeats.csv"


def mark_repeats(cur, path=REPEATS_CSV):
    if not pathlib.Path(path).exists():
        return 0
    n = 0
    for r in csv.DictReader(open(path, encoding="utf-8")):
        cur.execute(MARK_REPEAT, (r["kept_property_group"], r["content_hash"]))
        n += cur.rowcount
    return n


def read_csv(path):
    return [row_values(r) for r in csv.DictReader(open(path, encoding="utf-8"))]


# Columns first created as short VARCHARs (13 Nov 2026) that now hold joined values such as
# "under construction / probably off-plan". PostgreSQL will not change a column's type while
# a view uses it, and this project never drops anything, so the view is pointed away from
# these columns for a moment (CREATE OR REPLACE with NULL placeholders), the columns are
# widened to TEXT, and the real view is put back, all inside one transaction.
WIDEN = ["developer", "construction_status", "finish_level", "neighbourhood"]
VIEW_PLACEHOLDER = VIEW
for _c in WIDEN:
    VIEW_PLACEHOLDER = VIEW_PLACEHOLDER.replace(f"string_agg(DISTINCT {_c}, ' / ')", "NULL::text")
VIEW_PLACEHOLDER = VIEW_PLACEHOLDER.replace(
    "bool_or(construction_status LIKE '%under construction%' OR construction_status LIKE '%probably off-plan%')",
    "NULL::boolean")


def widen_columns(cur):
    """Make the WIDEN columns TEXT if they are not yet; returns how many were changed."""
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s "
                "AND column_name = ANY(%s) AND data_type <> 'text'", (TABLE, WIDEN))
    narrow = [r[0] for r in cur.fetchall()]
    if not narrow:
        return 0
    cur.execute("SELECT 1 FROM information_schema.views WHERE table_name = 'web_offplan_properties'")
    has_view = cur.fetchone() is not None
    if has_view:
        cur.execute(VIEW_PLACEHOLDER)
    for c in narrow:
        cur.execute(f"ALTER TABLE {TABLE} ALTER COLUMN {c} TYPE TEXT")
    cur.execute(VIEW)
    return len(narrow)


def upgrade(cur):
    """Add the new columns (if missing) and flag the old-reader ethiopiarealty rows."""
    for name, kind in NEW_COLUMNS:
        cur.execute(f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS {name} {kind}")
    cur.execute(MARK_OLD_ETHIOPIAREALTY, (OLD_READER_NOTE,))
    marked = cur.rowcount
    cur.execute(VIEW)
    return marked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=str(DEFAULT_CSV))
    ap.add_argument("--apply", action="store_true", help="actually create the table and load (owner-approved)")
    ap.add_argument("--upgrade", action="store_true",
                    help="only add the new columns and flag old-reader ethiopiarealty prices (owner-approved)")
    args = ap.parse_args()

    if args.upgrade:
        import psycopg2
        conn = psycopg2.connect(**DBWriter()._get_connection_params())
        try:
            with conn, conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
                before = cur.fetchone()[0]
                marked = upgrade(cur)
                cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
                after = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE price_unusable")
                flagged = cur.fetchone()[0]
            print(f"{TABLE}: {before} rows before, {after} after; newly flagged {marked}; "
                  f"rows flagged price_unusable now: {flagged}")
        finally:
            conn.close()
        return 0

    rows = read_csv(args.csv)
    print(f"read {len(rows)} rows from {args.csv}")
    if not args.apply:
        print("VALIDATE only — no database touched. Table it would create:")
        print(DDL)
        print(f"Would insert or update {len(rows)} rows in '{TABLE}' (matched by content_hash; nothing deleted).")
        print("Re-run with --apply, after a backup and the owner's approval, to load.")
        return 0

    import psycopg2
    from psycopg2.extras import execute_values
    params = DBWriter()._get_connection_params()  # enforces ollaa_user, refuses postgres, needs .env password
    conn = psycopg2.connect(**params)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(DDL)
            for name, kind in NEW_COLUMNS:
                cur.execute(f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS {name} {kind}")
            widened = widen_columns(cur)
            if widened:
                print(f"widened {widened} text column(s) to TEXT (no data changed)")
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            before = cur.fetchone()[0]
            execute_values(cur, UPSERT, rows, page_size=500)
            cur.execute(MARK_OLD_ETHIOPIAREALTY, (OLD_READER_NOTE,))
            marked = cur.rowcount
            repeats = mark_repeats(cur)
            cur.execute(VIEW)
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            after = cur.fetchone()[0]
        print(f"loaded into {TABLE}: {before} rows before, {after} after (+{after - before} new, the rest updated); "
              f"old-reader ethiopiarealty prices flagged: {marked}; older rows flagged as repeat copies: {repeats}.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
