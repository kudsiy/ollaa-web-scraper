# Thesis data check — off-plan apartments in Bole (13 November 2026)

Thesis topic: *"Market-implied discount rates and cash-equivalent prices of off-plan
apartments in Bole Sub-City."*

This check used **only data already on the laptop**: the listings stored in `web_listings`
and the local scrape files (a copy taken at 22:10 on 13 Nov: 1,957 distinct listings,
BetDelala 1,300 + ethiopiarealty 657), the 60 adverts in the accuracy file, two saved
BetDelala pages, the BetDelala sitemap, the pilot files, and an old copy of the Google Sheet.
**Nothing new was scraped for this check, and the Telegram tables were not touched.** The
database was backed up first (`backups/ollaa_2026-11-13.dump`, checked readable); the
database was only read.

## The short answer

**The stored data cannot support this thesis yet.** We have almost no off-plan apartments
(4 clear ones, 2 in Bole), and none of the payment terms the thesis needs, because **the
scraper never saved the advert text** — only price, size, bedrooms, place and the web
address. (The text was left out on purpose, because adverts contain people's phone
numbers.) Payment schedules, completion dates and cash discounts only appear in that text.

The good news: the adverts we *have* read show these terms **do exist** on BetDelala —
including one with an exact cash-discount schedule ("pay 100% → 7% off, 75% → 5% off,
50% → 3% off"), which is precisely what a market-implied discount rate is calculated from.
And **87 of BetDelala's ~90 developer/off-plan apartment adverts are in the part of the site
we have not scraped yet.** So the fix is: teach the scraper to keep the advert text (with
phone numbers masked) and read the payment terms out of it, *before* the rest of BetDelala
is scraped.

## ⚠️ A problem found along the way: ethiopiarealty prices are wrong

While counting, I found that **every ethiopiarealty listing has the same price, 3,433 birr,
and is labelled "rent"** — in the local files (657 rows), in the database (468 rows) and
even in the first 30-listing pilot. 374 of those web addresses say "for sale". The price
reader picks up some number that appears on every page of that site instead of the
listing's price, and anything between 1,000 and 300,000 birr is then guessed to be rent.
I missed this in the pilot and in the load report — sorry.

What it means:
- ethiopiarealty's **size, bedrooms and place are fine; its price and sale/rent label are
  not.** Its rows should not be used for prices until fixed.
- The **423 usable sale listings** in `DATA_QUALITY.md` are all BetDelala and are
  **not affected**. The "790 usable" total wrongly includes ethiopiarealty rent rows.
- **Fixed the same evening (owner approved one look at a live page):** the real price sits
  in the page's "Details" box (e.g. "Price 19,000,000ETB … Property Status For Sale"); the
  old reader took "10,000ETB"-type numbers from the site's search form. The reader now uses
  the Details box first and ignores search forms, menus and scripts. The 468 rows in the
  database are **flagged** `price_unusable = TRUE` (with a note) and stay flagged until
  those pages are read again with the fixed reader (a re-scrape still needs approval).

## 1. How many stored listings are off-plan apartments?

"Off-plan" here means the web address or advert says *under construction / off-plan /
project / handover / will be completed*, names a **developer** (e.g. "Ayat Real Estate"),
or offers a **down-payment / instalment plan**.

| | Count |
|---|---|
| Distinct stored listings | 1,957 |
| Apartments (any) | 680 |
| Apartments for **sale** with a trustworthy price (BetDelala) | 343 |
| **Off-plan / developer apartments for sale** (from the web address) | **4** |
| … of those in **Bole** | **2** |
| ethiopiarealty apartments whose address names a "real estate" company | 14 (5 name a real developer: Ayat ×2, Noah, Mega, Sefer), 4 in Bole — **but their price is wrong** (see above) |

From the 62 adverts whose **full text** we have locally: 37 are apartments, of which
**7 look off-plan** (2 say under construction / handover, 5 offer a down-payment plan,
4 name a developer). By sub-city: Kirkos 3, Bole 1, Yeka 1, Nifas Silk 1, unknown 1.

## 2. How often each thesis field is stated

**Among the 4 stored off-plan apartments** (web address + stored fields only):

| Field | Stated |
|---|---|
| Developer or project name | 4 of 4 |
| Unit size and total price | 4 of 4 |
| Payment schedule (down payment %, instalments, stage links) | 0 of 4 |
| Completion / handover date | 0 of 4 |
| Discount for cash / early payment | 0 of 4 |
| Price per m² stated by the seller | 0 of 4 (we can compute it: price ÷ size) |

The zeros are because we never stored the advert text, not because the adverts lack it.
**Among the 37 apartment adverts whose text we have** (7 of them off-plan):

| Field | All 37 apartments | The 7 off-plan |
|---|---|---|
| Developer or project name | 4 | 3 |
| Payment schedule (down payment / instalments / loan) | 8 | 5 |
| Instalments linked to construction stages | 0 | 0 |
| Completion / handover date | 1 | 1 |
| Discount for cash / full / early payment | 6 | 0* |
| Price per m² stated | 4 | 1 |

\* The best discount example (the 7/5/3% schedule below) mentions "semi-finished / full
finished" prices, so it is probably off-plan too; my word-matching just did not catch it.

### Real examples (phone numbers removed)

**Developer / project name + unit size and total price** (stored listings):
1. Ayat Real Estate — 1 bedroom, 23 m², 2,415,000 birr, Bole (BetDelala)
2. CMC Tsehay Real Estate — 3 bedroom, 144 m², 26,500,000 birr, Yeka (BetDelala)
3. Ayat Real Estate, Kazanchis building — 2 bedroom, 168 m², 35,000,000 birr, Kirkos (BetDelala)
4. Hope Real Estate (Dema) — 1 bedroom, 87 m², 17,420,000 birr, Bole (BetDelala)
5. From advert text: "Getas Realestate" (2 bedroom, 115 m², Bole); "Noh Real Estate"; "prestigious real estate"

**Payment schedule** (only 5 exist in our text):
1. "ቅድመ ክፍያ 10% = 714,000 … 85ካሬ ቅድመ ክፍያ 10% = 867,000" — 10% down payment on new-block 70 m² and 85 m² flats
2. "በ30% ቅድመ ክፍያ እና በ50% የባንክ ብድር በ20 አመት" — 30% down, 50% bank loan over 20 years
3. "Kazanchis … available with only a 15% down payment. Currently under good construction and will be completed …"
4. "We will build and hand it over to you within 12 months with only a 20% down payment" (CMC)
5. "139 sqm … 20 year bank loan financing available" (Bole; a bank loan, not a developer plan)

**Instalments linked to construction stages** (foundation, frame, finishing …): **none found**.

**Completion / handover date**: only **one** — "hand it over to you within 12 months" (CMC).

**Discount for paying in full or early**:
1. "Full price = 35.3 mil … Full finished = 38.4 mil. **Discount 100% = 7%, 75% = 5%, 50% = 3%**" — pay everything up front and get 7% off; this is exactly the data a discount rate is calculated from
2. "በቦሌ አትላስ … ለጥቂት ቤቶች ብቻ የወጣ ቅናሽ" — a limited discount on Bole Atlas apartments
3. "በካሳንችስ … ብቻ የወጣ ቅናሽ" — a discount on Kazanchis apartments and shops
4. "Luxury apartments for sale in affordable price with discount"
5. "Luxury commercial shops in affordable price and discount"

**Price per m² stated by the seller**:
1. "Price: 185,446 ETB per m²"
2. "Semi finished price per square meter 155,000 — Full finished 175,000" (the gap between
   semi-finished and full-finished is itself useful for the thesis)
3. "በካሬ 115,000 ብር ብቻ — በቦሌ አትላስ" — 115,000 birr per m², Bole Atlas
4. "157,447 ብር/ካሬ … Gross yield 10.38%" — Bole Mega area
5. (only 4 found)

## 3. Ready (finished) apartments in Bole, for comparison

**118** stored Bole apartments for sale have a price and size and no off-plan signal (all
BetDelala). After dropping 4 with impossible numbers, **114** remain: median **111,716
birr/m²** (middle half between 89,000 and 156,677). Only 6 say "ready / finished / title
deed" outright; the rest are "ready" only in the sense that nothing says off-plan.

Examples: Ayat 2-bed 105 m², 12,500,000 birr (119,048/m²); Bole Bulbula 3-bed 232 m²,
26,000,000 (112,069/m²); Bole Japan 2-bed 135 m², 22,000,000 (162,963/m²); Ayat-Mekedonia
3-bed 228 m², 23,984,284 (105,194/m²); Bole Homes 3-bed 281 m², 39,000,000 (138,790/m²).

So the **ready-apartment comparison group is already reasonable**; the **off-plan group
is the gap**.

## 4. Which websites have the most off-plan developer listings with payment terms

| Site | Status | Apartments | Off-plan / developer apartments | Payment or discount words in the web address |
|---|---|---|---|---|
| **BetDelala** (whole sitemap, 4,067 addresses) | scraping (~31% done) | 1,490 | **~90 (6%)**, 16 in Bole — **87 not scraped yet** | **48** — 44 not scraped yet |
| ethiopiarealty (657 scraped) | scraping; **price bug** | 273 | 14 (5%) | 0 |
| Ethiopia Property Centre (old sheet, May–Aug) | **excluded: Cloudflare bot wall** | 680 | 20 (mostly Temer Real Estate) | 4 |
| realethio (30-listing pilot) | GO, not scraped; mostly US dollars | 12 | 0 | 0 |
| ethiopianproperties (pilot) | GO, not scraped; US dollars | 7 | 0 | 0 |
| livingethio (pilot) | GO, not scraped; needs its own reader | 0 | 0 | 0 |
| ethiorealestates, shegahome | GO, not scraped; data API / small site | ? | ? | ? |

Examples of BetDelala addresses not scraped yet: "big discount 15 down payment 3 bedroom
115 sqm kazanchis"; "secure your home with an easy and flexible payment plan"; "sarbet
apartment 30 discounted"; "Temer real estate 90% constructed apartment, Ayat zone 5"; Jambo,
DMC, Big Group, Tsehay real estate apartments.

**Conclusion:** among the clean GO sites, **BetDelala is by far the best source**, and most
of its off-plan adverts are in the part we have not scraped yet. The other GO sites we
piloted showed **no** off-plan developer adverts in their samples, so they are unlikely to
have more. The site with many developer adverts (Ethiopia Property Centre) is behind a bot
wall and stays excluded. A possible extra source for later: the **developers' own
websites** (Temer, Noah, Ayat, etc.), which often publish payment plans — they would first
need the same GO / ASK / NO check as the other sites.

## 5. What the scraper should extract next (recommendation)

Do this **before** scraping the rest of BetDelala, so those ~90 off-plan adverts are read
properly the first time:

1. **Keep the advert text, with phone numbers and e-mails masked** (as the accuracy file
   already does). Everything below is read from it, and it lets us re-read later without
   visiting the site again.
2. **Developer / project name** (e.g. "Ayat Real Estate", "Temer").
3. **Construction status**: off-plan / under construction / % built ("90% constructed") / ready.
4. **Finish level**: semi-finished vs full-finished (often two prices).
5. **Down payment %** and its amount in birr.
6. **Instalments**: how many, how often, and whether they are tied to construction stages
   (foundation, frame, finishing …); bank-loan share and years.
7. **Completion / handover date** ("within 12 months", "2027", "በ2018 ዓ.ም").
8. **Discount schedule for paying early or in full** (e.g. 100% → 7%, 75% → 5%, 50% → 3%;
   "30% discounted").
9. **Price per m² as stated by the seller**, kept next to our own price ÷ size.
10. **Fix the ethiopiarealty price reader** (see the warning above) — needs your approval
    for one look at a live page.

These would be read in English and Amharic (ቅድመ ክፍያ = down payment, ቅናሽ = discount,
ርክክብ = handover, በካሬ = per m²). Expect the counts to stay modest: in our sample about 1
in 5 apartment adverts is off-plan, and only some of those state full terms, so the thesis
may need to combine web adverts with other sources (e.g. developers' own price lists).

## How these numbers were made

A one-off script (kept outside the repository) matched English and Amharic keywords in the
web addresses, stored fields and local advert texts; sub-cities came from Ollaa-Telegram's
place list (read only). Keyword matching misses some cases and catches a few wrong ones
(e.g. "Bole Rwanda real estate" is a place, not a developer), so treat the counts as
approximate. All examples above were checked by eye.

## Update, 13 November 2026 (evening): the scraper now reads the payment terms

Owner's decisions the same evening, now done:

- **ethiopiarealty part of the running scrape stopped** (709 pages read with the old
  reader). Price reader fixed (see the warning above); the 468 database rows are flagged.
- **Advert text is now stored, masked.** `parsers/contact_mask.py` replaces every phone
  number (0911…, +251…, 251…, 9-digit, landline), e-mail, chat link and chat handle with
  `<contact>` *before* anything is written; prices with thousands commas are never touched.
  The scraper writes the masked text to `saved_pages/<site>/full_v2.csv`, and the loader
  masks it again before it goes into the new column `web_listings.ad_text_masked`. The three
  saved web pages on the laptop were masked too.
- **New fields** (read by `parsers/offplan_terms.py`, English and Amharic) and matching new
  columns in `web_listings`: developer, construction status and % built, finish level
  (semi / full), down payment % and amount, instalment plan, whether payments follow the
  construction stages, bank loan, handover date, cash / early-payment discount schedule,
  stated price per m² (and separate semi- and full-finished prices per m²), and a
  "has payment terms" flag.
- **Off-plan first:** the scraper now reads adverts whose web address suggests off-plan or
  a developer first, including ones read earlier without their text.
- Database backed up first (`backups/ollaa_2026-11-13b.dump`, checked): 1,332 rows before
  and after; only new columns were added and 468 rows flagged.

### Test on the 62 adverts that have full text: 14 have payment terms

For the owner to check. "–" = not stated / not found. Amharic phrases translated in brackets.

| # | Advert (sub-city) | Developer | Status | Finish | Down payment | Instalments | Tied to stages | Bank loan | Handover | Discount | Price/m² stated |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | Mahder Property, new block, Summit (address says Bole) | Getas Realestate | – (new block; not marked) | – | 10% (= 714,000) | – | – | – | – | – | – |
| 7 | 2 bed 142 m², Mexico (Kirkos) | – | ready | semi and full offered | 30% | – | – | 50% over 20 years | – | – | semi 155,000 / full 175,000 |
| 10 | 1 bed 80 m², Kazanchis / Bole Atlas | – | – | – | – | – | – | – | – | mentioned, no figure | 115,000 |
| 14 | Gibi Gabriel project, Kazanchis (Kirkos) | Ayat Share Company | under construction | – | 15% | mentioned, no details | yes ("rest through progress") | – | – | – | – |
| 18 | 1 bed 80 m², Bole Atlas (Bole) | – | – | – | – | – | – | – | – | mentioned, no figure | – |
| 19 | 2 bed 142 m², Mexico (Kirkos) | – | – | fully finished | – | – | – | – | – | **100% → 7%, 75% → 5%, 50% → 3%** | – |
| 20 | 1 bed, Kazanchis (Kirkos) | – | under construction | – | 15% | – | – | – | 2.5 years | – | – |
| 21 | 85 m², Yetebaberut, CMC (Yeka) | – | under construction | – | 30% | rest within 1 year 6 months | – | – | 1 year 6 months | – | 89,995 |
| 30 | 2 bed 139 m², Bole road (Bole) | – | – | – | – | – | – | over 20 years | – | – | – |
| 34 | 2 bed, CMC Michael (Yeka) | – | under construction | – | 20% | – | – | – | 12 months | – | – |
| 41 | 2 bed 45 m², Kazanchis (Kirkos) | – | – | – | – | – | – | – | – | mentioned, no figure | – |
| 46 | 1 bed 23 m², Ayat real estate (Bole) | Ayat Real Estate | – | – | – | – | – | – | – | mentioned, no figure | – |
| 50 | 2 bed 80 m², Kazanchis (Kirkos) | – | – | – | 15% | – | – | – | – | – | – |
| 51 | 3 bed 185 m², Ayat 49 (Bole) | – | ready | – | – | – | – | up to 100% | – | – | – |

Things the reader does **not** count as payment terms, on purpose: an estimated monthly rent
("320,000 birr/month" in an investment note), "cash payment" for a ready flat, and an agent's
2% commission. 0 of the 62 texts kept a phone number after masking.

**Off-plan apartments in Bole with payment terms, so far: at most 1** — #6, Getas
Realestate's new block at Summit (10% down payment; its web address says Bole, but the
advert does not say "under construction", so the reader did not mark it off-plan). The other
Bole rows are ready flats with a bank-loan option (#30, #51) or only say "discount" without
a figure (#10, #18, #46). The clear off-plan cases are in Kirkos (Kazanchis) and
Yeka (CMC). This number should rise once the ~87 unread off-plan/developer BetDelala adverts
are read with the new reader (waiting for the owner's check of this table).

## Owner's corrections and the full scrape (13 November 2026, night)

The owner checked the table above and approved it, with three corrections. All three are done:

1. **#7 and #19 are one property** (Mexico / Senga Tera, 2 bed 142 m², 24.8 million birr).
   They are now linked (`data/same_property_links.csv`, plus an automatic rule: same
   sale/rent, price and place, and the same size or bedrooms where both are known), and
   the database view `web_offplan_properties` shows one row per property with both
   adverts' terms together: 30% down payment, 50% bank loan over 20 years, semi-finished
   155,000 / full-finished 175,000 birr per m², and the staged cash discount (100% → 7%,
   75% → 5%, 50% → 3%).
   **Is it off-plan? Probably not.** #7 calls it a "ሙሉ በሙሉ የተጠናቀቀ" (completely finished)
   apartment, its building services are described as working, and the price list matches a
   finished building (24.8 million ÷ 142 m² ≈ 175,000 = the full-finished price per m²).
   The semi/full choice is about the *interior finishing*, not the structure. So it is a
   **developer selling finished units, with a price for paying earlier** — useful for the
   cash-equivalent price idea, but it should not be counted as off-plan. It is recorded
   as "ready".
2. **#6 and #50 are now "probably off-plan"**: a developer-style down payment (or "new
   block / new project") without the words "under construction" or "ready" gives that
   status. #50 turned out to be a copy of another Kazanchis advert for the same flat that
   says "Ready to move in", so that property is recorded as "ready / probably off-plan"
   (the adverts disagree; both are kept). #6's text places it at **Summit 72**, while its
   web address says **Bole** — see the sub-city table.
3. **Sub-city field.** Every listing now has `neighbourhood` (the place name found), a
   `sub_city` and a `sub_city_unsure` flag. The sub-city comes from
   `ollaa-web-scraper/data/neighbourhood_subcity.csv`; **the owner's column
   `owner_sub_city` in that file always wins** — fill it in (or send the corrections) and
   the next preparation/load uses it. The table lists every neighbourhood named in the
   off-plan and developer adverts so far (scraped ones, plus BetDelala addresses not yet
   read):

| Neighbourhood | Sub-city used now | Unsure? | Why | Off-plan / developer adverts |
|---|---|---|---|---|
| Ayat | Bole | unsure | Ayat spreads over Bole, Yeka and (since 2020) Lemi Kura | 30 |
| Kazanchis | Kirkos | | | 28 |
| Bole Bulbula | Bole | unsure | edge of Bole (Akaki-Kality border) | 23 |
| Sarbet / Old Airport | Nifas Silk | unsure | Nifas Silk-Lafto or Kolfe | 16 |
| Bole | Bole | unsure | "Bole" alone may mean the Bole road / airport area | 14 |
| Kirkos | Kirkos | | | 12 |
| CMC | Yeka | unsure | usually Yeka, some CMC-area sites on the Bole side | 11 |
| Bulgaria | (none) | unsure | Kirkos or Nifas Silk | 9 |
| Lebu | Kolfe | unsure | may be Nifas Silk-Lafto | 7 |
| Piassa | Arada | | | 6 |
| Gelan | Sheger | unsure | run by Addis but in Oromia | 5 |
| Gotera | Nifas Silk | | | 4 |
| Yeka | Yeka | | | 3 |
| Summit | (none) | unsure | Bole or Yeka | 3 |
| Megenagna | Yeka | unsure | Yeka / Bole / Kirkos border | 3 |
| Wello Sefer | Bole | unsure | Kirkos or Bole | 3 |
| Wesen | (none) | unsure | not in the place list | 3 |
| Jemo | Kolfe | unsure | may be Nifas Silk-Lafto | 3 |
| Ayat 49 | Bole | unsure | Bole, Yeka or Lemi Kura by site | 3 |
| Alem Bank | (none) | unsure | not in the place list | 3 |
| Lemi Kura | Lemi Kura | | | 2 |
| Summit 72 | (none) | unsure | Bole or Yeka | 2 |
| Lafto | Nifas Silk | | | 2 |
| Bole Rwanda | Bole | | | 2 |
| Meskel Flower | Kirkos | unsure | Kirkos / Bole border | 2 |
| Gerji | Yeka | unsure | the place list says Yeka; much of Gerji may be Bole | 2 |
| Garment, Signal | (none) | unsure | not in the place list | 2 each |
| Imperial | Yeka | unsure | Bole / Yeka border | 1 |
| Mexico | Kirkos | unsure | Kirkos / Lideta border | 1 |
| Figa | (none) | unsure | Bole or Yeka | 1 |
| Urael | Bole | unsure | Bole / Kirkos border | 1 |
| Atlas | Bole | | | 1 |
| Stadium, Arada | Arada | | | 1 each |
| Sidist Kilo | Gulele | | | 1 |
| Ayer Tena | Kolfe | | | 1 |
| Kality | Akaki | | | 1 |
| Shola | Yeka | | | 1 |
| Enkulal Fabrica, Haile Garment, Addisu Gebeya | (none) | unsure | not in the place list | 1 each |

The "unsure" notes are Claude's starting points only; the owner (land administration)
decides. The file is refreshed after each preparation run, keeping the owner's columns.

### Off-plan apartments WITH payment terms, by sub-city — so far

From the 61 adverts whose text is stored (database view `web_offplan_properties`, one row
per property):

| Sub-city (current mapping) | Off-plan properties with payment terms | Note |
|---|---|---|
| Kirkos | 3 | all Kazanchis (one is "ready / probably off-plan": its adverts disagree) |
| Yeka | 2 | both CMC — unsure, CMC sits near the Bole border |
| Bole | 1 | #6 Getas Realestate, 10% down payment — unsure: its text says Summit 72 |
| **Total** | **6** | |

These are **interim** numbers: the full scrape below has just started.

### The full scrape (step 3) — running

- **Restarted 15 Nov 22:04** (the 13 Nov start had stopped, unnoticed, before midnight —
  probably when the app or laptop closed — so no pages were read on 14 Nov). It now runs
  independently of the app, and the Windows task `OllaaWebScrape` (owner approved) restarts
  it at each log-in unless it has stopped for good. Log:
  `saved_pages/run_until_done_2026-11-15.log`. First 11 pages: price, masked text and terms
  all read; no phone numbers left.
- First started 13 Nov 22:46 as its own Windows process (`tools/run_until_done.py --live`, log
  `saved_pages/run_until_done_2026-11-13.log`). Usual polite limits: honest user agent,
  3–6 s pauses (ethiopiarealty 8–15 s), at most 500 pages per site per day, and a **full
  stop at the first block, challenge, bad status or second connection failure** (the
  one-retry rule).
- Order: BetDelala **off-plan and developer adverts first** (including those read earlier
  without their text), then the rest of BetDelala, then **ethiopiarealty re-read** with
  the fixed price reader (owner approved).
- BetDelala's 500 pages for 13 Nov were already used, so it starts at 00:10 on 14 Nov.
  About 2,650 BetDelala pages plus ~1,600 ethiopiarealty pages remain: **about 9 days** at
  500 pages a day. If the laptop is switched off, the run stops; it starts again at the next
  log-in and continues where it left off.
- The scrape only writes local files. Loading into the database is a separate step
  (`etl/prepare_web_listings.py`, then a backup, then `etl/load_web_listings.py --apply`),
  done by Claude when the owner asks, never between 10:00 and 12:00.
