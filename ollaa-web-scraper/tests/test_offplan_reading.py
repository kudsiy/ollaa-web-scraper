"""
Offline checks for the thesis fields (owner, 13 Nov 2026): phone masking, the off-plan terms
reader, the details-box price reader (the ethiopiarealty fix) and the off-plan-first order.
All adverts below are made up for the tests; nothing goes online.
"""
from bs4 import BeautifulSoup

from parsers.contact_mask import MASK, has_contact, mask_contacts
from parsers.offplan_terms import extract_terms, offplan_url_signal
from tools import pilot_generic as pg
from tools import scrape_site


# ------------------------------------------------------------------ masking
def test_phone_numbers_are_masked_in_every_common_form():
    for phone in ["0911 23 45 67", "+251-911-234567", "251911234567", "0911234567", "911234567",
                  "09-11-23-45-67", "+251 (0) 911 234 567", "0116 123456", "tel:+251911234567",
                  "wa.me/251911234567", "agent@example.com"]:
        out = mask_contacts(f"Call {phone} today")
        assert MASK in out and not any(ch.isdigit() for ch in out.replace(MASK, "")), (phone, out)


def test_prices_and_page_code_are_not_masked():
    for keep in ["35,000,000 birr", "600,000,000", "10% = 714,000", "185,446 ETB per m²", "in 2027",
                 '{"@context":"https://schema.org","@type":"Product"}', "@media (max-width: 600px)"]:
        assert mask_contacts(keep) == keep


def test_masking_twice_changes_nothing():
    once = mask_contacts("Call 0911234567 or +251922334455, mail a@b.com")
    assert mask_contacts(once) == once and not has_contact(once)


# ------------------------------------------------------------------ terms reader
def test_down_payment_and_handover():
    r = extract_terms("Two bedroom flat in CMC. We will build and hand it over to you within 18 months "
                      "with only a 25% down payment.")
    assert r["down_payment_pct"] == 25 and r["handover"] == "18 months"
    assert r["construction_status"] == "under construction" and r["has_payment_terms"]


def test_cash_discount_schedule():
    r = extract_terms("Full finished 3 bedroom, full price 30 mil. Discount 100%= 8% 75% = 6% 50% =2%")
    assert r["discount_schedule"] == "100% paid -> 8% off; 75% paid -> 6% off; 50% paid -> 2% off"
    assert r["finish_level"] == "fully finished"


def test_semi_and_full_finished_prices_per_m2():
    r = extract_terms("Semi finished price per square meter 140,000 Full finished price per square meter 160,000")
    assert r["price_per_m2_semi"] == 140000 and r["price_per_m2_full"] == 160000
    assert r["finish_level"] == "semi and full finished offered"


def test_amharic_terms():
    r = extract_terms("በግንባታ ላይ ያለ አፓርትመንት። ቅድመ ክፍያ 20% = 1,200,000 ብር። በካሬ 95,000 ብር። የባንክ ብድር 50% በ 15 አመት")
    assert r["construction_status"] == "under construction"
    assert r["down_payment_pct"] == 20 and r["down_payment_amount"] == 1200000
    assert r["stated_price_per_m2"] == 95000
    assert r["bank_loan"].startswith("50% bank loan") and "15 years" in r["bank_loan"]


def test_payments_tied_to_construction_progress():
    r = extract_terms("Only 10% down payment first and the rest will be through progress of the building.")
    assert r["stage_linked"] is True and r["down_payment_pct"] == 10


def test_rent_estimate_is_not_an_instalment():
    r = extract_terms("Ready flat, cash payment. Expected rent: 150,000 birr/month. Gross yield 8%.")
    assert r["instalment_plan"] is None and r["has_payment_terms"] is False


def test_developer_from_text_or_web_address():
    assert extract_terms("Apartments by Temer Real Estate in Ayat")["developer"].lower().startswith("temer real")
    r = extract_terms("Nice flat", url="https://example.invalid/property/flat-for-sale-noah-real-estate-figa/")
    assert r["developer"].lower().startswith("noah real")
    assert extract_terms("Apartment for sale around Bole Rwanda real estate")["developer"] is None


def test_url_signal_for_offplan_first_order():
    assert offplan_url_signal("https://x.invalid/property/big-discount-15-down-payment-3-bedroom-115-sqm/")
    assert offplan_url_signal("https://x.invalid/property/temer-real-estate-apartment-3-bedroom/")
    assert not offplan_url_signal("https://x.invalid/property/house-for-rent-in-bole-2-bedroom/")


def test_plan_order_puts_offplan_first_and_respects_the_cap():
    urls = ["https://x.invalid/property/house-for-rent-a/", "https://x.invalid/property/temer-real-estate-b/",
            "https://x.invalid/property/villa-c/", "https://x.invalid/property/under-construction-flat-d/"]
    done = {urls[1]}  # read before, but without its text: comes back first
    order = scrape_site.plan_order(urls, done, have_text=set(), batch=10, cap_left=3)
    assert order == [urls[1], urls[3], urls[0]]
    assert scrape_site.plan_order(urls, done, have_text={urls[1]}, batch=10, cap_left=0) == []


# ------------------------------------------------------------------ details-box price (ethiopiarealty fix)
PAGE = """<html><body>
<form class="search"><div class="prices-for-all">Min. Price Any 10,000ETB 20,000ETB</div></form>
<h1>Ayat apartment for sale</h1>
<div id="property-detail-wrap"><ul>
 <li><strong>Price:</strong> <span>19,000,000ETB</span></li>
 <li><strong>Property Size:</strong> <span>110 m²</span></li>
 <li><strong>Bedrooms:</strong> <span>2</span></li>
 <li><strong>Property Status:</strong> <span>For Sale</span></li>
</ul></div>
<div id="property-address-wrap"><ul><li><strong>Area</strong> <span>CMC</span></li></ul></div>
<div id="property-description-wrap"><h2>Description</h2><p>Call 0911234567. 20% down payment.</p></div>
</body></html>"""


def test_price_comes_from_the_details_box_not_the_search_form():
    rec = pg.extract("https://x.invalid/property/ayat-apartment/", BeautifulSoup(PAGE, "lxml"))
    assert rec["price"] == 19_000_000 and rec["currency"] == "ETB"
    assert rec["area_sqm"] == 110 and rec["bedrooms"] == 2
    assert rec["listing_type"] == "sale" and rec["place"] == "CMC"


def test_stored_advert_text_is_masked():
    text = scrape_site.masked_text(BeautifulSoup(PAGE, "lxml"))
    assert "20% down payment" in text and "0911234567" not in text and MASK in text


# ------------------------------------------------------------------ loader
def test_loader_masks_text_again_and_fills_the_terms():
    from etl import load_web_listings as lw
    row = {"source": "betdelala", "source_url": "https://x.invalid/property/flat/", "price": "5000000",
           "reader": scrape_site.READER, "ad_text": "Under construction. 20% down payment. Call 0911234567"}
    values = dict(zip(lw.COLS, lw.row_values(row)))
    assert "0911234567" not in values["ad_text_masked"] and MASK in values["ad_text_masked"]
    assert values["down_payment_pct"] == 20 and values["has_payment_terms"] is True
    assert values["construction_status"] == "under construction"


def test_old_reader_ethiopiarealty_rows_are_flagged_not_changed():
    from etl import load_web_listings as lw
    sql = lw.MARK_OLD_ETHIOPIAREALTY
    assert sql.startswith("UPDATE web_listings SET price_unusable = TRUE")
    assert "source = 'ethiopiarealty'" in sql and "reader IS NULL" in sql and "price =" not in sql


# ------------------------------------------------------------------ owner's corrections (13 Nov 2026)
def test_down_payment_without_status_is_probably_offplan():
    from parsers.offplan_terms import is_offplan
    r = extract_terms("Modern flats in Kazanchis, become a home owner with only 15% down payment")
    assert r["construction_status"] == "probably off-plan" and is_offplan(r)
    r = extract_terms("New block apartments for sale. 10% down payment = 700,000")
    assert r["construction_status"] == "probably off-plan"
    assert extract_terms("Ready to move in. 20 year bank loan available")["construction_status"] == "ready"


def test_adverts_of_one_property_are_read_together():
    from parsers.offplan_terms import TEXT_JOIN, is_offplan, terms_for
    r = terms_for("Ready to move in! 2 bedroom." + TEXT_JOIN + "Only 15% down payment. Discount 100%= 7% 75% = 5%")
    assert r["construction_status"] == "ready / probably off-plan" and is_offplan(r)
    assert r["down_payment_pct"] == 15 and r["discount_schedule"].startswith("100% paid -> 7% off")


def _row(url, price, area, beds="", text="", code="mexico", src="betdelala", reader=""):
    import hashlib
    return {"source": src, "source_url": url, "price": price, "area_sqm": area, "bedrooms": beds,
            "listing_type": "sale", "property_type": "apartment", "location_code": code, "ad_text": text,
            "reader": reader, "content_hash": hashlib.sha256(f"{src}|{url}".encode()).hexdigest(), "_terms": {}}


def test_same_property_grouping_and_repeat_merging():
    from etl import prepare_web_listings as P
    a = _row("https://x.invalid/a", 24800000.0, 157.0, "", "Semi finished price per square meter 155,000")
    b = _row("https://x.invalid/b", 24800000.0, 142.0, 2, "Discount 100%= 7% 75% = 5% 50% =3%")
    c = _row("https://x.invalid/c", 9000000.0, 80.0, 2, "", code="kazanchis")
    groups = P.group_same_property([a, b, c])
    assert groups[a["content_hash"]] == groups[b["content_hash"]] != groups[c["content_hash"]]
    d = _row("https://x.invalid/d", 9000000.0, 80.0, 2, "Only 15% down payment", code="kazanchis")
    kept, repeats = P.drop_exact_repeats([c, d])
    assert len(repeats) == 1 and "15% down payment" in kept[0]["ad_text"]
    assert repeats[0][1] == kept[0]["content_hash"]


def test_old_ethiopiarealty_prices_never_group_or_merge():
    from etl import prepare_web_listings as P
    rows = [_row(f"https://e.invalid/{i}", 3433.0, 100.0, 2, src="ethiopiarealty", code="kazanchis") for i in range(3)]
    kept, repeats = P.drop_exact_repeats(rows)
    assert repeats == [] and len(set(P.group_same_property(rows).values())) == 3


def test_reread_old_orders_every_page_without_new_text():
    urls = ["https://e.invalid/property/a/", "https://e.invalid/property/b/"]
    assert scrape_site.plan_order(urls, set(urls), set(), 10, 10) == []
    assert scrape_site.plan_order(urls, set(urls), set(), 10, 10, reread_old=True) == urls
    assert scrape_site.plan_order(urls, set(urls), {urls[0]}, 10, 10, reread_old=True) == [urls[1]]


def _fake_site(monkeypatch, tmp_path, responses):
    from unittest.mock import MagicMock
    monkeypatch.setattr(pg, "BASE", tmp_path)
    monkeypatch.setattr(scrape_site.pg, "BASE", tmp_path)
    monkeypatch.setattr(scrape_site.time, "sleep", lambda s: None)
    urls = [f"https://x.invalid/property/flat-{i}/" for i in range(len(responses))]
    monkeypatch.setattr(scrape_site.pg, "collect_listing_urls", lambda sm: (urls, None))
    pages = iter(responses)

    def fetch(u):
        code = next(pages)
        return MagicMock(status_code=code, content=PAGE.encode(), text=PAGE), None
    monkeypatch.setattr(scrape_site, "fetch_with_one_retry", fetch)
    return urls


def test_run_stops_for_good_at_a_block(monkeypatch, tmp_path):
    _fake_site(monkeypatch, tmp_path, [200, 403, 200])
    status = scrape_site.run("site", "https://x.invalid/sitemap.xml", 10)
    assert status.startswith("stopped") and "403" in status
    rows = (tmp_path / "site" / "full_v2.csv").read_text(encoding="utf-8")
    assert rows.count("x.invalid/property/") == 1 and "0911234567" not in rows


def test_run_reports_finished_and_cap(monkeypatch, tmp_path):
    _fake_site(monkeypatch, tmp_path, [200, 200])
    assert scrape_site.run("site", "https://x.invalid/sitemap.xml", 1) == "cap"
    assert scrape_site.run("site", "https://x.invalid/sitemap.xml", 5) == "finished"


def test_runner_refuses_without_live(monkeypatch):
    from tools import run_until_done
    monkeypatch.setattr(run_until_done.sys, "argv", ["run_until_done.py"])
    assert run_until_done.main() == 2


def test_runner_stop_is_final(monkeypatch, tmp_path):
    from tools import run_until_done as R
    monkeypatch.setattr(R, "STOP_FILE", tmp_path / "SCRAPE_STOPPED.txt")
    monkeypatch.setattr(R, "DONE_FILE", tmp_path / "SCRAPE_FINISHED.txt")
    monkeypatch.setattr(R.sys, "argv", ["run_until_done.py", "--live"])
    calls = []
    monkeypatch.setattr(R.scrape_site, "run", lambda *a, **k: calls.append(a) or "stopped: HTTP 403 at #1")
    assert R.main() == 1 and R.STOP_FILE.exists() and len(calls) == 1
    # the at-logon restart must not try again while the stop file is there
    assert R.main() == 3 and len(calls) == 1


def test_runner_marks_finished(monkeypatch, tmp_path):
    from tools import run_until_done as R
    monkeypatch.setattr(R, "STOP_FILE", tmp_path / "SCRAPE_STOPPED.txt")
    monkeypatch.setattr(R, "DONE_FILE", tmp_path / "SCRAPE_FINISHED.txt")
    monkeypatch.setattr(R.sys, "argv", ["run_until_done.py", "--live"])
    monkeypatch.setattr(R.scrape_site, "run", lambda *a, **k: "finished")
    assert R.main() == 0 and R.DONE_FILE.exists() and R.main() == 3


def test_owner_subcity_rules():
    """Owner, 16 Nov 2026: Bole* (except Bole Arabsa -> Lemi Kura) and Gerji -> Bole; Ayat, Summit,
    Feyel Bet, Figa, CMC, Wesen, Safari, Yetebaberut, Gurd Shola -> Lemi Kura."""
    import re
    from types import SimpleNamespace as NS
    from etl import prepare_web_listings as P
    places = {"bole_bulbula": NS(name="Bole Bulbula", sub_city="Bole", parent=None),
              "bole_arabsa": NS(name="Bole Arabsa", sub_city="Bole", parent=None),
              "bole_atlas": NS(name="Atlas", sub_city="Bole", parent=None),
              "gerji": NS(name="Gerji", sub_city="Yeka", parent=None),
              "cmc_michael": NS(name="CMC", sub_city="Yeka", parent=None),
              "ayat_zone": NS(name="Ayat", sub_city="Bole", parent=None),
              "gurd_shola": NS(name="Gurd Shola", sub_city="Yeka", parent=None),
              "sholla": NS(name="Shola", sub_city="Yeka", parent=None),
              "kazanchis": NS(name="Kazanchis", sub_city="Kirkos", parent=None)}
    L = NS(PLACES=places, UNKNOWN="other_addis", NOISE="noise",
           find_location=lambda s: next((c for c in places if places[c].name.lower() in s.lower()), "other_addis"))
    rules, extras = P.read_rules(), P.read_extras()
    sub = lambda code: P.decide_sub_city(L, code, {}, rules, extras)[0]  # noqa: E731
    assert sub("bole_bulbula") == sub("bole_atlas") == sub("gerji") == "Bole"
    assert sub("bole_arabsa") == "Lemi Kura"  # owner, 16 Nov 2026: not Bole, Lemi Kura
    assert sub("cmc_michael") == sub("ayat_zone") == sub("gurd_shola") == "Lemi Kura"
    assert sub("sholla") == "Yeka" and sub("kazanchis") == "Kirkos"
    for words, name in [("3 bedroom yetebaberut cmc", "Yetebaberut"), ("ፍየል ቤት አካባቢ", "Feyel Bet"), ("safari area", "Safari")]:
        code = P.find_code(L, words, "", extras)
        assert P.place_name(L, code, extras) == name and sub(code) == "Lemi Kura"
    # the owner's own cell in the table still beats every rule
    assert P.decide_sub_city(L, "cmc_michael", {"cmc_michael": {"owner_sub_city": "Yeka"}}, rules, extras)[0] == "Yeka"


def test_numbers_joined_by_commas_are_masked():
    out = mask_contacts("call 0911234567,0922334455 or 251911234567,+251922334455")
    assert not any(ch.isdigit() for ch in out.replace(MASK, "")), out
    assert mask_contacts("price 1,250,000 or 12,500,000 birr") == "price 1,250,000 or 12,500,000 birr"


def test_loader_masks_phone_in_web_address():
    from etl import load_web_listings as lw
    row = {"source": "betdelala", "source_url": "https://x.invalid/property/flat-for-sale-call-0911234567",
           "price": "5000000", "content_hash": "abc"}
    values = dict(zip(lw.COLS, lw.row_values(row)))
    assert "0911234567" not in values["source_url"] and values["source_url"].endswith(MASK)
    assert values["content_hash"] == "abc"


def test_sitemap_connection_drop_gets_one_retry(monkeypatch, tmp_path):
    import requests as rq
    monkeypatch.setattr(scrape_site.pg, "BASE", tmp_path)
    waits = []
    monkeypatch.setattr(scrape_site.time, "sleep", lambda s: waits.append(s))
    calls = []

    def flaky(sm):
        calls.append(sm)
        raise rq.exceptions.ConnectionError("no internet yet")
    monkeypatch.setattr(scrape_site.pg, "collect_listing_urls", flaky)
    status = scrape_site.run("site", "https://x.invalid/sitemap.xml", 5)
    assert status.startswith("stopped") and "after one retry" in status
    assert len(calls) == 2 and waits == [scrape_site.RETRY_WAIT]


def test_price_per_m2_in_the_price_box():
    """Owner, 16 Nov 2026: a price per m2 in the price box is stored as price per m2; the
    total is calculated (and marked) only when the size is known."""
    from etl import prepare_web_listings as P
    r = dict(_row("https://x.invalid/property/apartment-for-sale-3-bedroom-128-sqm", 106000.0, 128.0, 3), listing_type="rent")
    out = P.apply_price_basis(r)
    assert out["price_per_m2"] == 106000.0 and out["price"] == 106000.0 * 128 and out["listing_type"] == "sale"
    assert out["price_basis"] == P.BASIS_CALC and out["price_as_advertised"] == 106000.0
    r = dict(_row("https://x.invalid/property/apartment-for-sale-1-bedroom", 80000.0, ""), listing_type="rent")
    out = P.apply_price_basis(r)
    assert out["price"] == "" and out["price_per_m2"] == 80000.0 and out["price_basis"] == P.BASIS_PPM_ONLY
    # a real rent, a real total, and an old ethiopiarealty price are left alone
    rent = dict(_row("https://x.invalid/property/apartment-for-rent-bole", 50000.0, 112.0), listing_type="rent")
    assert P.apply_price_basis(rent)["price"] == 50000.0 and rent["price_basis"] == P.BASIS_TOTAL
    total = _row("https://x.invalid/property/apartment-for-sale-ayat", 9000000.0, 90.0)
    assert P.apply_price_basis(total)["price"] == 9000000.0 and total["price_per_m2"] == ""
    old = _row("https://e.invalid/property/flat-for-sale", 30000.0, 100.0, src="ethiopiarealty")
    assert P.apply_price_basis(old)["price"] == 30000.0


def test_hand_corrections():
    from types import SimpleNamespace as NS
    from etl import prepare_web_listings as P
    places = {"kazanchis": NS(name="Kazanchis", sub_city="Kirkos", parent=None, lat=9.01, lon=38.77)}
    L = NS(PLACES=places, UNKNOWN="other_addis", NOISE="noise", city_of=lambda c: "ADDIS_ABABA",
           coordinates=lambda c: (9.01, 38.77, "Kirkos"), find_location=lambda s: "other_addis")
    a = P.apply_price_basis(dict(_row("https://x.invalid/property/apartment-for-sale-urael", 80000.0, 18.0, 1), listing_type="rent"))
    b = P.apply_price_basis(_row("https://x.invalid/property/apartment-for-sale-metro", 127400.0, 68.0, 3))
    corr = [{"source_url": a["source_url"], "field": "area_sqm", "value": "97.18"},
            {"source_url": a["source_url"], "field": "location_code", "value": "kazanchis"},
            {"source_url": b["source_url"], "field": "area_sqm", "value": "130"},
            {"source_url": b["source_url"], "field": "price_total", "value": "16600000"}]
    assert P.apply_corrections([a, b], corr, L, {}, [], []) == 4
    assert a["area_sqm"] == 97.18 and a["price"] == round(80000 * 97.18, 2) and a["price_basis"] == P.BASIS_CALC
    assert a["sub_city"] == "Kirkos" and a["neighbourhood"] == "Kazanchis"
    assert b["area_sqm"] == 130 and b["price"] == 16600000 and b["price_basis"] == P.BASIS_HAND
    assert b["price_per_m2"] == 127400.0  # the advertised price per m2 is kept


def test_cash_discount_written_after_the_payment_words():
    r = extract_terms("Pay in full and get 7% discount. Apartment for sale in Ayat.")
    assert r["discount_schedule"] == "7% off for cash/full payment"
    r = extract_terms("10% discount for cash buyers")
    assert r["discount_schedule"] == "10% off for cash/full payment"


def test_daily_once_mode_writes_the_log(monkeypatch, tmp_path):
    import csv as _csv
    from tools import run_until_done as R
    monkeypatch.setattr(R, "STOP_FILE", tmp_path / "SCRAPE_STOPPED.txt")
    monkeypatch.setattr(R, "DONE_FILE", tmp_path / "SCRAPE_FINISHED.txt")
    monkeypatch.setattr(R, "DAILY_LOG", tmp_path / "daily_log.csv")
    monkeypatch.setattr(R.sys, "argv", ["run_until_done.py", "--live", "--once"])
    waited = []
    monkeypatch.setattr(R, "wait_until_tomorrow", lambda: waited.append(1))

    def fake_run(label, *a, **k):
        R.scrape_site.LAST_RUN.clear()
        R.scrape_site.LAST_RUN.update(site=label, read=500, new=480, reread=20, left=1278, error="")
        return "cap"
    monkeypatch.setattr(R.scrape_site, "run", fake_run)
    assert R.main() == 0 and waited == []          # one day's share, then exit (no waiting)
    rows = list(_csv.DictReader(open(R.DAILY_LOG, encoding="utf-8")))
    assert rows[0]["site"] == "betdelala" and rows[0]["pages_read"] == "500" and rows[0]["new_listings"] == "480"
    assert rows[0]["status"] == "cap" and rows[0]["error"] == ""


def test_run_records_pages_and_new_listings(monkeypatch, tmp_path):
    _fake_site(monkeypatch, tmp_path, [200, 200, 403])
    status = scrape_site.run("site", "https://x.invalid/sitemap.xml", 10)
    r = scrape_site.LAST_RUN
    assert status.startswith("stopped") and r["read"] == 2 and r["new"] == 2 and "403" in r["error"]
