# Scraping review: right websites, right method?

Review of 31 October 2026, after the Google Sheet check in `STATUS.md`. Offline only: the
scraper code, its git history, the sheet data already downloaded (counts only) and web
searches. No property website was visited and no scraper was run (the project is parked).

**Short answer: the main problem is how we scrape, not which websites.** The most important
site, Ethiopia Property Centre, is on the list and holds about 5,000 adverts, but our code
captured a small part of it, then broke on 7 June. A few useful sites are missing and four
entries on the list do not look like property sites at all.

## 1. Are these the right websites?

| Kind | On our list | What it produced (sheet "new") | Verdict |
|---|---|---|---|
| Property listing sites | 13 | 2 sites gave real data: Ethiopia Property Centre (1,365 rows) and BetDelala (427); Real Ethio 12 and Ethiopia Realty 3 rows; 5 sites nothing (Jiji, Engocha, AddisList, Living Ethio, Ethio Real Estates); 4 had no scraper at all | right idea, badly covered |
| Tender sites | 8 | 2,548 rows, almost no prices or sizes; about 1 title in 5 is about property | wrong source for prices |
| Bank / government auctions | 9 | 54 rows (48 from eGP, 6 from 3 banks); 5 banks nothing | few notices, prices hidden in PDFs |

- **Ethiopia Property Centre is the right main source.** Its own report for July–September
  2026 analysed 5,031 adverts, 4,975 of them in Addis Ababa; its pages list, for example,
  665 adverts in Yeka alone. We captured about 1,365 rows in the 10 days before our scraper
  broke, and only 121 usable sale adverts. It also publishes monthly average asking prices per area and number
  of bedrooms, which could serve the thesis as a benchmark without any scraping.
- **Missing or not working:** Jiji (the country's largest classifieds site, over 2,000
  property adverts already in 2022; our scraper got nothing) and Qefira (a large classifieds site with
  property adverts; not on the list). Developer sites (such as Temer Properties) show
  new-build prices, a different signal.
- **Four entries look wrong:** `zegebeya.com`, `afrobet.com`, `etrealtor.com.et` and
  `ethiopianproperties.com` never had a scraper, and a web search found no property site
  under these names (`afrobet` sounds like a betting site). They should be removed.
- **Tender sites** carry all kinds of public purchases. Only bank auction notices ("ሐራጅ")
  matter for property, and their prices are in notice texts or PDFs. **Banks** publish few
  notices; the Development Bank of Ethiopia has an auction page, and a scraper for it
  (`scrapers/banks/dbe_scraper.py`) exists but was never switched on.

## 2. Are we scraping properly?

No. These faults explain most of what the sheet showed:

1. **A rewrite on 7 June broke Ethiopia Property Centre.** The earlier AI helper replaced the
   code that looked for advert cards with a narrow list made for a WordPress layout this
   site does not use. The daily run on 7 June (old code) still collected adverts; from
   8 June on, none, while every run reported "success". Some of its page addresses also look
   wrong (we ask for `/for-sale/apartments/`; the site uses `/for-sale/flats-apartments/`).
2. **Nothing reached the sheet after 10 August.** BetDelala and most tender sites stopped
   on the same day, with no code change; the runs kept taking about 14 minutes, so the
   scraping went on and the upload to the sheet failed. The exact error is in the GitHub run
   log, which needs a GitHub sign-in to read.
3. **Only the summary cards on search pages are read, never the advert's own page.** The
   size, full place and description are usually on the advert page, which is why the size
   is known for only 37% of Ethiopia Property Centre rows and 10% of BetDelala rows.
4. **Posting dates are never saved**: the code sets them to "none", although Ethiopia
   Property Centre shows "Added on …" dates (the old code even noted this and did nothing).
5. **Rent or sale is guessed from the letters "rent" anywhere on the card**, so words like
   "currently" turn a sale into a rent.
6. **Junk can get in**: when no card is found, any "article" on the page counts as an
   advert (the sheet has, for example, 18 rows titled just "Apartment", probably junk).
7. **Repeats**: an advert's fingerprint is made of about 38 fields, including the card text,
   so any small change on the card saves it again. 1,462 of 4,409 rows are repeats, mostly
   tenders (1,337 from Reporter Tenders). Using the advert's link would avoid this.
8. **Price reading**: the "prices" that were phone numbers came from the code used before
   7 June. Today's main reader handled made-up test adverts correctly, but the backup reader
   reads "Apartment 120 m2 Br 9,800,000" as 120,000,000 birr and finds no price in
   "4 bed house Br 25,000,000".
9. **Failures are invisible**: the exporter hides errors, so a site can deliver nothing for
   months (Ethiopia Property Centre: June to October) with every run marked "success".
   There is no count per site and no warning when a site drops to zero.
10. **Package versions are not pinned**, so GitHub installed the newest version of every
    package each day (W6).

## 3. What it would take

If web prices are wanted again, the best value is a small pilot on **Ethiopia Property
Centre only** (W15): look at two or three of its pages once by hand (with the owner's
approval), read each advert's own page for size, place and the "Added on" date, use the
advert link to avoid repeats, report a count per run and warn at zero, and keep the speed
low. Before that, check the site's `robots.txt` and terms of use; for a thesis, asking the
site for an academic data extract, or citing its published average-price reports, may be
the better route. Jiji and Qefira could follow only if the pilot works.

Staying parked is also reasonable: Ollaa-Telegram already has 394 sale listings ready for
the hedonic model, and reading its 2,860 photo-only posts is a larger gain.

## Sources

- [Ethiopia Property Centre, market report Q3 2026](https://ethiopiapropertycentre.com/market-reports/q3-2026)
- [Ethiopia Property Centre, adverts in Yeka, Addis Ababa](https://ethiopiapropertycentre.com/addis-ababa/yeka)
- [Ethiopia Property Centre, average house prices in Addis Ababa](https://ethiopiapropertycentre.com/market-trends/average-prices/for-sale/houses/addis-ababa)
- [Ethiopia Property Centre, an apartment advert (address format)](https://ethiopiapropertycentre.com/for-sale/flats-apartments/addis-ababa/kirkos/showtype/2361-ready-apartemnet-for-sell-at-riche)
- [Shega: review of the top online marketplaces in Ethiopia, Jiji](https://shega.co/news/review-of-the-top-3-online-marketplaces-in-ethiopia-jiji)
- [Shega: review of the top online marketplaces in Ethiopia, Qefira](https://shega.co/news/review-of-the-top-3-online-marketplaces-in-ethiopia-qefira)
- [Development Bank of Ethiopia, auction announcements](https://dbe.com.et/index.php?start=112)
