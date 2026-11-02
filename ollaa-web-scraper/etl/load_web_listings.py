"""Load the cleaned multi-site listings into a NEW table `web_listings` in the shared `ollaa`
database (task W16, step 4). Safe by design:

- It only CREATEs a new table and INSERTs rows (ON CONFLICT DO NOTHING). It never changes,
  removes or reads the sister project's own tables, and contains no delete/drop of data.
- It connects as the everyday login `ollaa_user` (via config / .env); it refuses `postgres`.
- Re-running it loads nothing twice: each row is keyed by content_hash.

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
COLS = ["source", "source_url", "price", "currency", "listing_type", "property_type", "area_sqm",
        "bedrooms", "location_code", "sub_city", "city", "latitude", "longitude", "probable_dup",
        "content_hash", "scraped_at"]


def read_csv(path):
    rows = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        rows.append(tuple((r[c] or None) if c not in ("probable_dup",) else (r[c] == "yes") for c in COLS))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=str(DEFAULT_CSV))
    ap.add_argument("--apply", action="store_true", help="actually create the table and load (owner-approved)")
    args = ap.parse_args()

    rows = read_csv(args.csv)
    print(f"read {len(rows)} rows from {args.csv}")
    if not args.apply:
        print("VALIDATE only — no database touched. Table it would create:")
        print(DDL)
        print(f"Would insert {len(rows)} rows into '{TABLE}' (ON CONFLICT (content_hash) DO NOTHING).")
        print("Re-run with --apply, after a backup and the owner's approval, to load.")
        return 0

    import psycopg2
    from psycopg2.extras import execute_values
    params = DBWriter()._get_connection_params()  # enforces ollaa_user, refuses postgres, needs .env password
    conn = psycopg2.connect(**params)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            before = cur.fetchone()[0]
            execute_values(cur,
                           f"INSERT INTO {TABLE} ({','.join(COLS)}) VALUES %s "
                           f"ON CONFLICT (content_hash) DO NOTHING", rows)
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            after = cur.fetchone()[0]
        print(f"loaded into {TABLE}: {before} rows before, {after} after (+{after - before} new).")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
