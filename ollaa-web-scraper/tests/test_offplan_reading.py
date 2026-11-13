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
